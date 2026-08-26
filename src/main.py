import os
import sys
from datetime import datetime, timezone

from sheets import get_client, ensure_setup, read_seen_urls, append_scored_urls, append_results, load_companies, load_profile, load_search_terms
from fetchers import FETCHERS, fetch_broad_search
from filters import passes_title_filter, passes_description_filter, is_too_old, _parse_list
from scorer import score_jobs


def main():
    print(f'[{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC] Strategic Copilot starting')

    api_key = os.environ.get('OPENAI_API_KEY', '').strip()    
    sheets_id     = os.environ.get('GOOGLE_SHEETS_ID', '').strip()
    rapidapi_key  = os.environ.get('RAPIDAPI_KEY', '').strip()
    lookback_days = int(os.environ.get('LOOKBACK_DAYS', '30') or '30')

    if not api_key or not sheets_id:
        print('ERROR: OPENAI_API_KEY and GOOGLE_SHEETS_ID must be set')
        sys.exit(1)

    client = get_client()

    print('Checking Google Sheet setup...')
    ensure_setup(client, sheets_id)

    print('Loading config from Google Sheets...')
    companies    = load_companies(client, sheets_id)
    profile      = load_profile(client, sheets_id)
    search_terms = load_search_terms(client, sheets_id)
    seen_urls    = read_seen_urls(client, sheets_id)

    print(f'  {len(companies)} active companies')
    print(f'  {len(search_terms)} active search terms')
    print(f'  {len(seen_urls)} URLs in dedup cache')

    threshold       = int(profile.get('score_threshold', 6) or 6)
    lower_threshold = int(profile.get('lower_score_threshold', threshold) or threshold)
    lower_titles    = _parse_list(profile.get('lower_threshold_titles', ''))
    print(f'  Lookback:  {lookback_days} days')
    if lower_titles:
        print(f'  Lower threshold ({lower_threshold}) for: {", ".join(lower_titles)}')

    def meets_threshold(scored_job):
        score = scored_job.get('Fit Score', 0)
        title = (scored_job.get('Job Title') or '').lower()
        if lower_titles and any(t in title for t in lower_titles):
            return score >= lower_threshold
        return score >= threshold
    new_scored = []  # list of scored dicts for Scored URLs tab
    qualifying = []
    total_fetched  = 0
    total_filtered = 0
    total_new      = 0
    total_scored   = 0

    for company in companies:
        name   = str(company.get('Company Name', '')).strip()
        ats    = str(company.get('ATS Type', '')).strip().lower()
        handle = str(company.get('ATS Handle', '')).strip()

        if not name or not ats or not handle:
            print(f'  Skipping incomplete row: {company}')
            continue

        fetch_fn = FETCHERS.get(ats)
        if not fetch_fn:
            print(f'  Unknown ATS "{ats}" for {name} — skipping')
            continue

        # Per-company seniority override (e.g. Palantir uses 'lead' not 'director')
        co_seniority_raw = str(company.get('Seniority Override', '')).strip()
        co_profile = dict(profile)
        if co_seniority_raw:
            co_profile['seniority_keywords'] = co_seniority_raw

        print(f'\n{name} ({ats}/{handle})')
        if ats == 'workday':
            seniority = _parse_list(co_profile.get('seniority_keywords', ''))
            jobs = fetch_fn(handle, name, seniority_keywords=seniority or None)
        else:
            jobs = fetch_fn(handle, name)
        total_fetched += len(jobs)
        print(f'  Fetched:   {len(jobs)}')

        filtered = [j for j in jobs if not is_too_old(j, lookback_days) and passes_title_filter(j, co_profile)]
        total_filtered += len(filtered)
        print(f'  Filtered:  {len(filtered)}')

        new_jobs = [j for j in filtered if j.get('job_url') and j['job_url'] not in seen_urls]
        total_new += len(new_jobs)
        print(f'  New:       {len(new_jobs)}')

        if not new_jobs:
            continue

        print(f'  Scoring {len(new_jobs)} jobs...')
        scored = score_jobs(new_jobs, profile, api_key)
        total_scored += len(scored)

        for s in scored:
            url = s.get('Job URL', '')
            if url and url not in seen_urls:
                new_scored.append(s)
                seen_urls.add(url)

        hits = [s for s in scored if meets_threshold(s) and len(s) > 2]
        qualifying.extend(hits)
        print(f'  Score >= {threshold}: {len(hits)}')

    print(f'\n{"="*40}')
    print(f'Total fetched:   {total_fetched}')
    print(f'After filters:   {total_filtered}')
    print(f'New (unscored):  {total_new}')
    print(f'Scored:          {total_scored}')
    print(f'Qualifying:      {len(qualifying)}')
    print(f'{"="*40}')

    # ── Write company scan results before broad search so a broad search
    # failure never causes company results to be lost ────────────────────────
    print('\nWriting company scan results to Google Sheets...')
    if new_scored:
        append_scored_urls(client, sheets_id, new_scored)
        print(f'  Wrote {len(new_scored)} URLs to Scored URLs tab')
    if qualifying:
        append_results(client, sheets_id, qualifying)
        print(f'  Wrote {len(qualifying)} jobs to Opportunities CRM tab')

    # ── Broad search pass ───────────────────────────────────────────────────
    if rapidapi_key and search_terms:
        print(f'\n{"="*40}')
        print('BROAD SEARCH PASS')
        print(f'{"="*40}')
        bs_fetched = bs_filtered = bs_new = bs_scored = 0
        bs_scored_jobs = []
        bs_qualifying = []

        for query in search_terms:
            print(f'\nQuery: "{query}"')
            try:
                jobs = fetch_broad_search(query, rapidapi_key)
            except Exception as e:
                print(f'  Broad search error for "{query}": {e}')
                continue
            bs_fetched += len(jobs)
            print(f'  Fetched:   {len(jobs)}')

            filtered = [
                j for j in jobs
                if not is_too_old(j, lookback_days)
                and passes_title_filter(j, profile)
                and passes_description_filter(j, profile)
            ]
            bs_filtered += len(filtered)
            print(f'  Filtered:  {len(filtered)}')

            new_jobs = [j for j in filtered if j.get('job_url') and j['job_url'] not in seen_urls]
            bs_new += len(new_jobs)
            print(f'  New:       {len(new_jobs)}')

            if not new_jobs:
                continue

            print(f'  Scoring {len(new_jobs)} jobs...')
            scored = score_jobs(new_jobs, profile, api_key)
            bs_scored += len(scored)

            for s in scored:
                s['Source Lane'] = 'Lane 2 - Broad Search'
                url = s.get('Job URL', '')
                if url and url not in seen_urls:
                    bs_scored_jobs.append(s)
                    seen_urls.add(url)

            hits = [s for s in scored if meets_threshold(s) and len(s) > 2]
            bs_qualifying.extend(hits)
            print(f'  Score >= {threshold}: {len(hits)}')

        print(f'\nBroad search totals:')
        print(f'  Fetched:   {bs_fetched}')
        print(f'  Filtered:  {bs_filtered}')
        print(f'  New:       {bs_new}')
        print(f'  Scored:    {bs_scored}')

        if bs_scored_jobs:
            append_scored_urls(client, sheets_id, bs_scored_jobs)
            print(f'  Wrote {len(bs_scored_jobs)} URLs to Scored URLs tab')
        if bs_qualifying:
            append_results(client, sheets_id, bs_qualifying)
            print(f'  Wrote {len(bs_qualifying)} jobs to Opportunities CRM tab')
    elif search_terms and not rapidapi_key:
        print('\nSkipping broad search — RAPIDAPI_KEY not set')

    print(f'\n[{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC] Done')



if __name__ == '__main__':
    main()
