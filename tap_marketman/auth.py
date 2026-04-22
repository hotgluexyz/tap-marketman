"""Authentication helpers for the Marketman tap.

Marketman exposes two auth-related endpoints:

* ``POST /buyers/auth/GetToken`` — exchanges an API key + password for a
  short-lived token.
* ``POST /buyers/partneraccounts/GetAuthorisedAccounts`` — lists the buyer
  accounts (locations) the API key can access.

The token is then passed to every subsequent call as an ``AUTH_TOKEN``
header (wired up in ``client.MarketmanStream.authenticator``).
"""

from __future__ import annotations

import requests

REQUEST_TIMEOUT_SECONDS = 60


def fetch_auth_token(api_url: str, api_key: str, api_password: str) -> str:
    """Exchange the API key/password for a Marketman ``AUTH_TOKEN``."""
    url = f"{api_url}/buyers/auth/GetToken"
    resp = requests.post(
        url,
        json={"APIKey": api_key, "APIPassword": api_password},
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"Marketman GetToken failed [{resp.status_code}]: {resp.text}") from exc
    data = resp.json()
    if not data.get("IsSuccess") or not data.get("Token"):
        raise RuntimeError(f"Marketman GetToken returned an error: {data.get('ErrorMessage')}")
    return data["Token"]


def fetch_first_buyer_guid(api_url: str, auth_token: str) -> str:
    """Return the first ``BuyerGuid`` accessible to ``auth_token``."""
    url = f"{api_url}/buyers/partneraccounts/GetAuthorisedAccounts"
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "AUTH_TOKEN": auth_token,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Marketman GetAuthorisedAccounts failed [{resp.status_code}]: {resp.text}"
        ) from exc
    data = resp.json()
    buyers = data.get("Buyers") or []
    if not buyers:
        raise RuntimeError(
            "Marketman GetAuthorisedAccounts returned no buyers; "
            "set `buyer_guid` explicitly in config."
        )
    return buyers[0]["Guid"]
