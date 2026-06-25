# Connector Audit — PipelineOps Agent

**Audited:** 2026-06-25  
**Policy:** Do not build fake connector implementations. If no legal official API path exists, implement a blocked-state stub only. Do not scrape, do not simulate data, do not store raw passwords.

---

## Summary Table

| Source | Official API Path | Auth Method | Data Scope | Verdict |
|---|---|---|---|---|
| Indeed | ❌ None (deprecated) | N/A | N/A | **BLOCKED** |
| CareerBuilder | ❌ Partner-only (closed) | N/A | N/A | **BLOCKED** |
| Monster | ❌ No public employer API | N/A | N/A | **BLOCKED** |
| Dice | ❌ No public employer API | N/A | N/A | **BLOCKED** |
| Greenhouse | ✅ Harvest API v1 | API Key (HTTP Basic) | Jobs, Candidates, Applications, Offers, Scorecards | **BUILD — requires GREENHOUSE_API_KEY** |
| Lever | ✅ Data API v1 | API Key (HTTP Basic) | Postings, Opportunities, Offers, Feedback | **BUILD — requires LEVER_API_KEY** |
| Bullhorn | ⚠️ REST API exists | OAuth 2.0 + corporate credentials | Jobs, Candidates, Submissions, Placements | **BUILD — requires BULLHORN_CLIENT_ID + CLIENT_SECRET + credentials** |
| Google Sheets | ✅ Sheets API v4 | Service Account JSON or OAuth 2.0 | Read/write any spreadsheet | **BUILD — requires service account JSON or OAuth** |
| CSV / Excel | ✅ File upload (no external API) | None | All columns in file | **READY — build now** |

---

## Detailed Findings

### Indeed
- **Official API:** Indeed had a Publisher API that allowed job search/embedding. That API has been **deprecated and is closed to new partners** as of 2023.
- **Indeed for Employers:** Internal SaaS product. No public REST API for reading posted jobs or applicant data.
- **Indeed Apply Button:** Allows candidates to apply via Indeed widget, but does not provide an employer-facing data read endpoint.
- **ATS Partnership:** Indeed integrates with partner ATSs (Greenhouse, Lever, etc.) for job distribution, but that is an outbound push — not a read API we can consume.
- **Verdict:** BLOCKED. Do not build a real connector. Implement blocked-state UI/API response only. If the user wants Indeed data, they must export it manually as CSV.
- **Path to unblock:** Apply to Indeed's Employer Integration Partner Program. Availability and terms not publicly documented as of audit date.

### CareerBuilder
- **Official API:** CareerBuilder had a REST API (CareerBuilder Connect) that allowed partner access to job listings and resume search. This API **requires an active publisher partnership agreement** and is not open to new applicants without a business relationship.
- **Status:** The developer portal (developer.careerbuilder.com) exists but requires an approved API key that is not obtainable without contacting CareerBuilder sales.
- **Verdict:** BLOCKED. No self-serve path to obtain credentials. Implement blocked-state stub only.
- **Path to unblock:** Contact CareerBuilder Partner Program (partnerprogram@careerbuilder.com). Requires executed MSA.

### Monster
- **Official API:** Monster had a Semantic Search API used primarily for academic/research access. No current documented public employer-facing API for reading job postings or applicant data.
- **Monster for Employers:** Web product only. No API documented for employer data read.
- **Verdict:** BLOCKED. No verifiable public API path as of audit date.
- **Path to unblock:** Contact Monster Business Development. No self-serve API program currently active.

### Dice
- **Official API:** Dice (owned by DHI Group / Dice.com) had a Job Seeker API years ago, which has since been deprecated. No current public employer-facing REST API is documented.
- **Dice for Employers:** Web portal only. Manual CSV export available from employer dashboard.
- **Verdict:** BLOCKED. No public API path available. If users have employer accounts, they can export candidate lists as CSV and use the CSV connector.
- **Path to unblock:** Contact Dice Enterprise Sales. No self-serve API program documented.

---

### Greenhouse
- **Official API:** Greenhouse Harvest API v1 — fully documented at [developers.greenhouse.io/harvest](https://developers.greenhouse.io/harvest).
- **Auth:** HTTP Basic auth. API key is the username; password is empty. Key obtained from Greenhouse admin panel: Configure > Dev Center > API Credential Management.
- **Rate limit:** 50 requests/second (default). Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Pagination:** `Link` header with `rel="next"`. Also supports `?page=N&per_page=500` query params.
- **Data scope:**
  - `GET /v1/jobs` — all open/closed jobs
  - `GET /v1/candidates` — all candidates (paginated)
  - `GET /v1/applications` — all applications with current stage
  - `GET /v1/offers` — all offers with amounts
  - `GET /v1/job_stages` — stage configuration per job
  - `GET /v1/departments` — department hierarchy
- **Webhook support:** Yes — can push stage changes, new applications, etc. via webhook to our API.
- **Verdict:** BUILD. Implement `GreenhouseConnector` using HTTP Basic auth. Requires `GREENHOUSE_API_KEY` in env. If key not present, return `needs_credentials` status.

### Lever
- **Official API:** Lever Data API v1 — documented at [hire.lever.co/developer/documentation](https://hire.lever.co/developer/documentation).
- **Auth:** HTTP Basic auth. API key is the username; password is empty. Key obtained from Lever admin: Settings > Integrations & API > API Credentials. **Read-only** vs **full access** keys are separate scopes.
- **Rate limit:** 10 requests/second per endpoint. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.
- **Pagination:** Cursor-based. `?limit=100&offset=<cursor>` where `offset` comes from `next` in the JSON response.
- **Data scope:**
  - `GET /v1/postings` — job postings (also available without auth as public endpoint)
  - `GET /v1/opportunities` — candidate opportunities (Lever's core entity, combines candidate + application)
  - `GET /v1/opportunities/{id}/offers` — offers per opportunity
  - `GET /v1/stages` — pipeline stage configuration
  - `GET /v1/contacts` — contacts (distinct from opportunities)
- **Verdict:** BUILD. Implement `LeverConnector` using HTTP Basic auth. Requires `LEVER_API_KEY`. If key not present, return `needs_credentials` status.

### Bullhorn
- **Official API:** Bullhorn REST API — documented at [bullhorn.github.io/rest-api-docs](https://bullhorn.github.io/rest-api-docs).
- **Auth:** Multi-step OAuth 2.0 flow:
  1. GET `/oauth/authorize?client_id=...&response_type=code` → redirects with `?code=`
  2. GET `/oauth/token?grant_type=authorization_code&code=...` → returns `access_token`
  3. GET `/rest-services/login?access_token=...` → returns `BhRestToken` and `restUrl`
  4. All subsequent calls: `{restUrl}entity/Job?BhRestToken={token}`
- **Credentials required:** `BULLHORN_CLIENT_ID`, `BULLHORN_CLIENT_SECRET`, and either corporate OAuth redirect or username/password for headless flow.
- **Data scope:**
  - `GET /entity/Job` — job orders
  - `GET /entity/Candidate` — candidates
  - `GET /entity/JobSubmission` — applications/submissions
  - `GET /entity/Placement` — placements
  - `GET /entity/ClientCorporation` — client companies
- **Rate limit:** Not publicly documented; typically 100 req/s for enterprise accounts.
- **Verdict:** BUILD with complexity warning. Requires corporate Bullhorn subscription. Auth flow is non-trivial. Implement `BullhornConnector` that performs the full OAuth dance if all credentials are present.

### Google Sheets
- **Official API:** Google Sheets API v4 — documented at [developers.google.com/sheets/api](https://developers.google.com/sheets/api).
- **Auth (server-to-server):** Service Account JSON key. Create a service account in Google Cloud Console, download the JSON key, share the target spreadsheet with the service account email.
- **Auth (user OAuth):** OAuth 2.0 client ID + client secret + refresh token. More complex for server-side use.
- **Data scope:** Read and write any spreadsheet the service account or OAuth user has access to.
- **Rate limits:** 300 read requests/minute per project. 60 write requests/minute per user.
- **Required packages:** `google-api-python-client`, `google-auth`, `google-auth-httplib2`.
- **Verdict:** BUILD. Use service account JSON path as primary. Requires `GOOGLE_SHEETS_CREDENTIALS_JSON` (service account JSON contents, single-line escaped) and `GOOGLE_SHEETS_SPREADSHEET_ID`.

### CSV / Excel
- **Official path:** Direct file upload. No external API needed.
- **CSV:** Python `csv` module. Already implemented in `csv_connector.py`.
- **Excel (.xlsx):** `openpyxl` library. Not yet implemented. Add to `csv_connector.py` with auto-detection by file extension/MIME type.
- **Dirty-data handling:** Missing headers, blank rows, merged cells, inconsistent date formats — handle defensively in parser.
- **Verdict:** READY. CSV works. Add Excel support via `openpyxl`.

---

## Blocked-State API Response Schema

For blocked connectors (Indeed, CareerBuilder, Monster, Dice), the API returns:

```json
{
  "source": "indeed",
  "status": "blocked",
  "reason": "No official public API available.",
  "path_to_unblock": "Apply to Indeed Employer Integration Partner Program. Contact partnerprogram@indeed.com.",
  "workaround": "Export candidate list as CSV from your Indeed Employer dashboard and upload via the CSV connector.",
  "jobs": [],
  "candidates": [],
  "applications": []
}
```

Connector classes for blocked sources implement `BaseConnector` but return the above instead of raising exceptions, so the UI can display a helpful blocked-state card rather than an error.

---

## Environment Variables Required per Connector

| Connector | Required Env Vars |
|---|---|
| Greenhouse | `GREENHOUSE_API_KEY` |
| Lever | `LEVER_API_KEY` |
| Bullhorn | `BULLHORN_CLIENT_ID`, `BULLHORN_CLIENT_SECRET`, `BULLHORN_USERNAME` (optional for headless) |
| Google Sheets (read/write) | `GOOGLE_SHEETS_CREDENTIALS_JSON`, `GOOGLE_SHEETS_SPREADSHEET_ID` |
| CSV/Excel | None (file upload) |
| Indeed | _None — blocked_ |
| CareerBuilder | _None — blocked_ |
| Monster | _None — blocked_ |
| Dice | _None — blocked_ |

All secrets are stored encrypted at rest via `ENCRYPTION_KEY`. Never logged. Never returned in API responses.
