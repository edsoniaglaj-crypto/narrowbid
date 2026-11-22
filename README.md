# NarrowBid

Free public-tender discovery for small UK creative and digital agencies.

- [Open the explorer](https://narrowbid.citruskid10.chatgpt.site)
- [Report a problem or suggest a filter](https://github.com/edsoniaglaj-crypto/narrowbid/issues/new). GitHub issues are public.

## Run locally

Use Python 3.12. No third-party dependencies are required.

```sh
python -m unittest discover -s tests -v
python scripts/fetch_tenders.py
python -m http.server 8000
```

Open http://localhost:8000. The browser reads the latest public GitHub snapshot and falls back to the bundled snapshot if it cannot retrieve it. The explorer shows the last successful sync and marks data older than 48 hours as stale.

## Operations

GitHub Actions runs the collector daily at 06:17 UTC (03:17 in Brasília) and allows manual runs. It publishes successful snapshots to `data/tenders.json`; a failed refresh preserves the previous snapshot. The public site is hosted on ChatGPT Sites. Changes to HTML or JavaScript require a new site deployment. Daily changes to the feed do not.

The source is the official [Find a Tender service](https://www.find-tender.service.gov.uk/), under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Buyers' notices govern deadlines and eligibility. The agency score is a keyword and profile heuristic. The free prototype has no checkout or customer account system.
