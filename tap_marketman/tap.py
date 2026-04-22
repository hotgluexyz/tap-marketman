"""Marketman tap class."""

from __future__ import annotations

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th
from typing_extensions import override

from tap_marketman.auth import fetch_auth_token, fetch_first_buyer_guid
from tap_marketman.streams import (
    InventoryCountsStream,
    InventoryItemsStream,
    LocationsStream,
    MenuItemsStream,
    PrepsStream,
    TransfersStream,
    WasteEventsStream,
)

STREAM_TYPES = [
    InventoryCountsStream,
    InventoryItemsStream,
    LocationsStream,
    MenuItemsStream,
    PrepsStream,
    TransfersStream,
    WasteEventsStream,
]


class TapMarketman(Tap):
    """Singer tap for Marketman."""

    name = "tap-marketman"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            required=True,
            description="Marketman API Partner key.",
        ),
        th.Property(
            "api_password",
            th.StringType,
            required=True,
            description="Marketman API Partner password.",
        ),
        th.Property(
            "buyer_guid",
            th.StringType,
            description=(
                "Marketman BuyerGuid to sync. If omitted, the first authorised "
                "buyer returned by GetAuthorisedAccounts is used."
            ),
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync (ISO-8601).",
            default="2020-01-01T00:00:00Z",
        ),
        th.Property(
            "api_url",
            th.StringType,
            description="Base URL for the Marketman API.",
            default="https://api.marketman.com/v3",
        ),
    ).to_dict()

    _auth_token: str | None = None
    _buyer_guid: str | None = None

    @property
    def api_url(self) -> str:
        """Return the configured API base URL."""
        return self.config["api_url"]

    @property
    def auth_token(self) -> str:
        """Fetch and cache the Marketman ``AUTH_TOKEN`` for this tap instance."""
        if self._auth_token is None:
            self._auth_token = fetch_auth_token(
                api_url=self.api_url,
                api_key=self.config["api_key"],
                api_password=self.config["api_password"],
            )
        return self._auth_token

    @property
    def buyer_guid(self) -> str:
        """Return the BuyerGuid to use, fetching it from the API if not configured."""
        if self._buyer_guid is None:
            configured = self.config.get("buyer_guid")
            self._buyer_guid = configured or fetch_first_buyer_guid(
                api_url=self.api_url,
                auth_token=self.auth_token,
            )
        return self._buyer_guid

    @override
    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapMarketman.cli()
