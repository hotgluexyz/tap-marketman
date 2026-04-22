# tap-marketman

A [Singer](https://www.singer.io/) tap that extracts data from **Marketman**. It is built with [hotglue-singer-sdk](https://github.com/hotgluexyz/HotglueSingerSDK) and speaks the standard Singer message protocol on stdout, so you can pair it with any compatible target.

## Features

- **REST**-style HTTP streams (see `client.py` / `streams.py`).
- **Custom / N/A** authentication — finish wiring in `client.py` as needed.

- Configurable **`api_url`** and optional **`start_date`** (see [Configuration](#configuration)).
- Incremental sync is scaffolded with placeholder **`id`** (primary key) and **`modified_at`** (replication key); replace with real fields per stream in `streams.py`.

### Streams

| Stream | Endpoint / notes | Primary key | Replication key |
| ------ | ---------------- | ----------- | ----------------- |
| `locations` | `GET` + `/locations` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `inventory_items` | `GET` + `/inventory_items` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `menu_items` | `GET` + `/menu_items` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `preps` | `GET` + `/preps` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `inventory_counts` | `GET` + `/inventory_counts` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `transfers` | `GET` + `/transfers` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |
| `waste_events` | `GET` + `/waste_events` (default path; TODO: confirm with API) | `id` (TODO) | `modified_at` (TODO) |

TODO: Describe pagination, rate limits, and any stream-specific query parameters in this section.

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
| `start_date` | string (datetime) | no | `2000-01-01T00:00:00Z` | Earliest record date to sync. |
| `api_url` | string | no | `https://api.marketman.com/v3` | Base URL for the API. |
| `api_key` | string | yes | — | API credential (adjust name/location in code if your API differs). |

Run `tap-marketman --about` (or `tap-marketman --about --format=markdown`) for the authoritative schema for your installed version.

### Example `config.json`

```json
{
  "start_date": "2000-01-01T00:00:00Z",
  "api_url": "https://api.marketman.com/v3",
  "api_key": "YOUR_API_KEY"
}
```

Do not commit real credentials. Prefer environment variables or a secrets manager in production.

### Environment-based config

You can load settings from the process environment using `--config=ENV` (the SDK merges env into config). Env names follow the tap’s setting keys (see `tap-marketman --about`).

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

TODO: Add your vendor’s base URLs, auth docs, and links (compare to the “API hosts” section in a finished tap README).
