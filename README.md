# tap-marketman

A [Singer](https://www.singer.io/) tap that extracts data from **Marketman**. It is built with [hotglue-singer-sdk](https://github.com/hotgluexyz/HotglueSingerSDK) and speaks the standard Singer message protocol on stdout, so you can pair it with any compatible target.

## Features

- POST-based JSON HTTP streams against the Marketman REST API (see `client.py` / `streams.py`).
- API-key + password authentication: the tap exchanges your credentials for a short-lived `AUTH_TOKEN` (via `POST /buyers/auth/GetToken`) and attaches it to every subsequent request as an `AUTH_TOKEN` header (see `auth.py`).
- Automatic `BuyerGuid` discovery — if `buyer_guid` is not configured, the first authorised buyer returned by `GetAuthorisedAccounts` is used.
- Configurable `api_url`, `start_date`, and optional `buyer_guid` (see [Configuration](#configuration)).
- Incremental sync where the API supports it: `inventory_items` and `preps` use `UpdateDate`, while `inventory_counts`, `transfers`, and `waste_events` use a UTC `DateTimeFromUTC`/`DateTimeToUTC` window. `locations` and `menu_items` are full-refresh.

### Streams

| Stream | Endpoint (POST) | Primary key | Replication key | Notes |
| ------ | --------------- | ----------- | --------------- | ----- |
| `locations` | `/buyers/partneraccounts/GetAuthorisedAccounts` | `Guid` | — | Full refresh; does not require `BuyerGuid`. |
| `inventory_items` | `/buyers/inventory/GetInventoryItems` | `ID` | `UpdateDate` | Paginated (`Skip`/`Take`). |
| `menu_items` | `/buyers/inventory/GetMenuItems` | `ID` | — | Paginated; full refresh because `UpdateDate` is `null` for items created via the API. |
| `preps` | `/buyers/inventory/GetPreps` | `ID` | `UpdateDate` | Paginated (`Skip`/`Take`). |
| `inventory_counts` | `/buyers/inventory/GetInventoryCounts` | `ID` | `CountDateUTC` | Date-range filter; line and count-definition details are requested. |
| `transfers` | `/buyers/inventory/GetTransfers` | `ID` | `DateUTC` | Date-range filter. |
| `waste_events` | `/buyers/inventory/GetWasteEvents` | `ID` | `DateUTC` | Date-range filter. |

#### Pagination

Marketman paginates `inventory_items`, `menu_items`, and `preps` via `Skip`/`Take` body fields. The tap requests pages of 500 records and stops when a page returns fewer than 500 records.

#### Date filtering

For date-filtered streams, the tap derives `DateTimeFromUTC` from the stream's bookmark (or `start_date` on the first sync) and `DateTimeToUTC` from the current UTC time, formatted as `yyyy/MM/dd HH:mm:ss`.

#### Datetime normalization

Marketman returns timestamps in `yyyy/MM/dd HH:mm:ss` UTC. The tap rewrites every top-level `format: date-time` field to ISO 8601 UTC before emitting records.

## Requirements

- Python **3.10+** (see `requires-python` in `pyproject.toml`).

## Installation

1. **Clone** this repository and `cd` into the project directory.
2. **Create `config.json`** in the project root with your credentials and settings (see [Configuration](#configuration) for the fields and an example).
3. **Create a virtual environment** and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, use `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

4. **Install the package** in editable mode:

```bash
pip install -e .
```

5. **Run the tap** (with the venv still activated):

```bash
tap-marketman --help
```

## Configuration

| Setting | Type | Required | Default | Description |
| ------- | ---- | -------- | ------- | ----------- |
| `api_key` | string | yes | — | Marketman API Partner key. |
| `api_password` | string | yes | — | Marketman API Partner password. |
| `buyer_guid` | string | no | first authorised buyer | `BuyerGuid` to sync. If omitted, the first buyer returned by `GetAuthorisedAccounts` is used. |
| `start_date` | string (datetime) | no | `2020-01-01T00:00:00Z` | Earliest record date to sync (ISO-8601). |
| `api_url` | string | no | `https://api.marketman.com/v3` | Base URL for the Marketman API. |

Run `tap-marketman --about` (or `tap-marketman --about --format=markdown`) for the authoritative schema for your installed version.

### Example `config.json`

```json
{
  "api_key": "YOUR_API_KEY",
  "api_password": "YOUR_API_PASSWORD",
  "buyer_guid": "00000000-0000-0000-0000-000000000000",
  "start_date": "2020-01-01T00:00:00Z",
  "api_url": "https://api.marketman.com/v3"
}
```

Do not commit real credentials. Prefer environment variables or a secrets manager in production.

### Environment-based config

You can load settings from the process environment using `--config=ENV` (the SDK merges env into config). Env names follow the tap's setting keys (see `tap-marketman --about`).

## Usage

With your virtual environment **activated** and `config.json` in place:

Discover stream catalog:

```bash
tap-marketman --config config.json --discover > catalog.json
```

Run a sync (with optional state):

```bash
tap-marketman --config config.json --catalog catalog.json --state state.json
```

Pipe to any Singer target:

```bash
tap-marketman --config config.json --catalog catalog.json | target-jsonl
```

Inspect built-in settings and stream metadata:

```bash
tap-marketman --about
```

## API / documentation

- API base URL: `https://api.marketman.com/v3`
- Marketman API portal: <https://api-doc.marketman.com/>
- Auth endpoint: `POST /buyers/auth/GetToken` (returns an `AUTH_TOKEN` used as a request header on subsequent calls)
