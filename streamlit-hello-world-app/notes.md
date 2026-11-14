# Allianz Data Quality Dashboard - Project Notes

## What it is
A Streamlit app on **Databricks Apps** (`data-quality-dashboard`) that runs **10 data quality checks** on either an uploaded CSV file or a Unity Catalog table, then shows:
- Summary numbers (KPI cards)
- A pass/fail card per check
- Failed records, with a CSV download
- A breakdown by column
- A donut chart of failures

## What each file does

| File | Role |
| --- | --- |
| `app.py` | The page itself: header (user name and time), choice of data source, summary numbers, check cards, failed-records table with CSV download, column breakdown, donut chart |
| `data_service.py` | The checks engine: finds the key column, runs the 10 checks, builds the report, generates SQL for fixing bad rows, lists catalog schemas and tables, and holds the fake data used when a query fails |
| `obo_auth.py` | Sign-in and data access: reads the user's token, finds the workspace address, creates the SDK client, runs SQL, and has the warehouse connection test |
| `styles.py` | The white corporate look (CSS), with green for passed and red for failed |
| `.streamlit/config.toml` | Forces the light theme so Streamlit's own controls match the custom styling |
| `app.yaml` | How the app starts (`streamlit run app.py`) and the warehouse it uses (`DATABRICKS_WAREHOUSE_ID`) |
| `requirements.txt` | Python packages: streamlit (1.42 or later), pandas, plotly, databricks-sql-connector, databricks-sdk |

## How it works
1. You pick a source: an uploaded CSV, or a table from the `samples` catalog. Schema and table lists are fetched live.
2. For a table, the app runs `SELECT * ... LIMIT n` on the SQL warehouse with the signed-in user's token.
3. If the query fails, the app shows realistic fake data instead and displays a notice.
4. The checks engine runs, and the page displays the report.

## OBO (On-Behalf-Of) explained
- The app queries data **as the person using it**, not as the app's own built-in account (its service principal).
- Databricks Apps passes the user's token to the app in the request header `X-Forwarded-Access-Token`, so no personal access token is needed.
- Because queries run as that user, Unity Catalog's rules apply to them: their grants, row filters and column masks. Each user sees only what they're allowed to see.
- What the token may do is limited by **scopes**:
  - `sql`: run queries
  - `catalog.*:read`: list catalogs, schemas and tables
- The user has to approve these scopes once. If scopes are added later, the user has to approve them again.
  - Check a user's saved approval: `GET /api/2.0/oauth-app-integrations/<app-integration-id>/user-consent/me`
  - Delete it to force a new approval prompt: `DELETE` on the same path, then open the app in a private window.
- SDK detail: the app also has the service principal's login details as environment variables (`DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`). So the code uses `Config(host, token, auth_type="pat")` to make the SDK use only the user's token.

## Concepts involved
- **Databricks Apps**: hosted web apps, `app.yaml`, deployments, the app's service principal, user authorization scopes.
- **Unity Catalog**: the catalog, schema and table hierarchy, and permissions.
- **SQL warehouse access**, two ways:
  - The `databricks-sql-connector` package.
  - The Statement Execution API through the SDK. This route waits while the warehouse starts, reads results in chunks, and converts columns back to proper types.
- **Streamlit**: page reruns, session state, columns and containers, custom CSS, theme config.
- **Data quality dimensions**: uniqueness, completeness, validity, consistency, accuracy, conformity, integrity, cleanliness.
- **Quarantine** (also called a dead letter queue): bad records are separated out with the reasons they failed.

## The 10 checks

| # | Check | Dimension | What it flags |
| --- | --- | --- | --- |
| 1 | Uniqueness | Uniqueness | Exact duplicate rows, plus duplicate keys when a key column is found |
| 2 | Null | Completeness | Any missing value in a row |
| 3 | Format | Validity | Bad email addresses in columns whose name contains `email` |
| 4 | Completeness | Completeness | Rows with blank fields or an empty key |
| 5 | Consistency | Consistency | Dates in the future (compared in UTC) in date/time columns |
| 6 | Accuracy | Accuracy | Negative amounts (revenue, amount, price, fare, premium and similar) and credit scores outside 300-850 |
| 7 | Conformity | Conformity | Placeholder text such as `N/A`, `null`, `unknown`, `-`, `?` |
| 8 | Range & Boundary | Integrity | Percentage or rate columns outside 0-100 |
| 9 | Key Integrity | Integrity | Missing or badly formed keys. Shows N/A when the table has no key column |
| 10 | Whitespace | Cleanliness | Spaces at the start or end, or double spaces |

## How results are scored
- Strict pass/fail: a check fails if even one row fails it.
- Each check's pass rate = 1 - (failing rows / total rows).
- Quality score = the average of the 10 pass rates.
- Failed records = the distinct rows that failed at least one check. Each comes with the checks it failed and the reasons.

## How the key column is found
1. **By name**: `id`, `*_id`, `*key`, `pk_*`, `*_number`, `*_no`. A fully unique match is preferred.
2. **Otherwise inferred**: a column whose values are all filled in, all unique and look like IDs.
3. **Otherwise no key**. The key-based checks are then skipped.

## Issues fixed during this work
- A crash from a variable that was never defined (`pk_dup_count`).
- The selector card was built from separate HTML pieces, so it didn't wrap its controls. It's now a proper bordered container (`st.container(border=True)`).
- Dark mode made text hard to read. The light theme is now forced.
- The SDK failed because it saw two sign-in methods at once ("oauth and pat"). Fixed with `auth_type="pat"`.
- Query results came back as text and didn't include all rows.
- Timezone-aware timestamps broke the future-date check.
- The key check failed every row on tables without an ID column.
- The user's saved approval for the app was missing the `sql` permission. Fixed by deleting the approval so a new prompt appears.
