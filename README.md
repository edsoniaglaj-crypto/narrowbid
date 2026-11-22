# NarrowBid — UK public tender discovery prototype

A static, transparent and inexpensive first product for independent UK creative and digital agencies.

## What works
- Mobile-first English website and product description.
- Search, sector filters and sorting for government notice records.
- Explainable agency-to-opportunity *heuristic* (not eligibility or legal advice).
- Source attribution, consent-free static interface, clear incomplete/stale-data disclosure.
- Python 3.12 official API collector, with cursor pagination, dates, deduplication and safe filtering.
- GitHub Actions automation scheduled daily at 06:17 UTC and GitHub Pages deployment.
- No account payments, AI spend, invented notices or unsourced endorsements.

## First deployment
1. Create a NEW public repository named `narrowbid` under your own GitHub account.
2. Upload these files, including the `.github/workflows/refresh-and-deploy.yml` workflow.
3. In repository Settings → Pages → Build and deployment, set source to **GitHub Actions**.
4. Go to Actions → **Refresh official UK tenders and deploy** → Run workflow. If the API is unavailable, the page shows no/stale feed rather than fake results.
5. Check the Pages URL in Settings → Pages; confirm real official notices and deadlines before sharing.

A public GitHub Pages repo exposes *source code* and generated public procurement data. It should not contain credentials or user information. GitHub scheduled Actions may be delayed. If you operate a business, add legally accurate operator contact, privacy/legal disclosures and any required company details before collecting contact information or accepting payments. For a production service, add a privacy-preserving opt-in waitlist and an approved payment provider.

## Local preview
`python -m http.server 8000` from the repository root, then visit http://localhost:8000 . No additional packages required. The checked-in `data/tenders.json` is initially empty until the first refresh.

## Refresh
`python scripts/fetch_tenders.py` (internet required). External dependencies: Python standard library only. The script does not fabricate notice records or overwrite good data if the official endpoint fails. Output: `data/tenders.json`.

## Market hypothesis
Target users: small UK agencies selling web, digital, marketing, design, video and research services. Proposed future subscription: £19/month for saved profiles and high-quality daily alerts. No paid service, payments or automatic emails exist yet. Successful sales require independent demand validation, proper billing and customer support.

## Sources
- [UK government official Open Contracting guidance](https://www.gov.uk/government/publications/open-contracting)
- [Find a Tender official service](https://www.find-tender.service.gov.uk/)
- [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

Not affiliated with the government. Buyer source documents are authoritative.
