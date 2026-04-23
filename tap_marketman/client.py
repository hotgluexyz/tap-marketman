"""REST client base class for the Marketman tap.

Marketman exposes JSON-over-HTTP endpoints under https://api.marketman.com/v3 .
All read endpoints are POST requests with a JSON body. Authentication is
performed by issuing a separate ``GetToken`` call (handled on the tap) and
attaching the resulting token in an ``AUTH_TOKEN`` header.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import cached_property
from typing import TYPE_CHECKING, Any

import requests
from hotglue_singer_sdk.authenticators import APIKeyAuthenticator
from hotglue_singer_sdk.exceptions import FatalAPIError
from hotglue_singer_sdk.streams import RESTStream
from typing_extensions import override

if TYPE_CHECKING:
    from tap_marketman.tap import TapMarketman

API_BASE_URL = "https://api.marketman.com/v3"
DATETIME_FMT = "%Y/%m/%d %H:%M:%S"
PAGE_SIZE = 500


class MarketmanStream(RESTStream):
    """Base class for all Marketman streams.

    Subclasses must set ``path`` and ``records_jsonpath`` (or override
    ``parse_response``). Most subclasses pass ``BuyerGuid`` in the request
    body; date-filtered endpoints additionally pass ``DateTimeFromUTC`` /
    ``DateTimeToUTC``.
    """

    rest_method = "POST"

    primary_keys: list[str] = ["ID"]
    replication_key: str | None = None

    requires_buyer_guid: bool = True
    paginate: bool = False
    records_envelope_key: str = "Items"

    @override
    @property
    def url_base(self) -> str:
        """Return the Marketman API base URL."""
        return API_BASE_URL

    @override
    @property
    def http_headers(self) -> dict[str, str]:
        """Marketman accepts JSON bodies; the auth header is injected by the authenticator."""
        return {"Content-Type": "application/json"}

    @override
    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Authenticate every request with the cached ``AUTH_TOKEN`` header."""
        tap: TapMarketman = self._tap  # type: ignore[assignment]
        return APIKeyAuthenticator(
            stream=self,
            key="AUTH_TOKEN",
            value=tap.auth_token,
            location="header",
        )

    def _format_marketman_datetime(self, value: datetime) -> str:
        """Format a datetime as Marketman expects (yyyy/mm/dd HH:MM:SS, UTC)."""
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.strftime(DATETIME_FMT)

    def _date_range(self, context: dict | None) -> tuple[str, str]:
        """Return (DateTimeFromUTC, DateTimeToUTC) for date-filtered endpoints."""
        starting = self.get_starting_timestamp(context)
        if starting is None:
            starting = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime.now(timezone.utc)
        return self._format_marketman_datetime(starting), self._format_marketman_datetime(end)

    @override
    def prepare_request_payload(
        self,
        context: dict | None,
        next_page_token: Any | None,
    ) -> dict | None:
        """Return the JSON body for a Marketman POST request.

        Subclasses should override ``extra_payload`` instead of this method
        to inject endpoint-specific fields (e.g. date ranges).
        """
        payload: dict[str, Any] = {}
        if self.requires_buyer_guid:
            tap: TapMarketman = self._tap  # type: ignore[assignment]
            payload["BuyerGuid"] = tap.buyer_guid
        if self.paginate:
            payload["Skip"] = int(next_page_token or 0)
            payload["Take"] = PAGE_SIZE
        payload.update(self.extra_payload(context))
        return payload

    def extra_payload(self, context: dict | None) -> dict[str, Any]:
        """Hook for subclasses to add endpoint-specific body fields."""
        return {}

    @override
    def get_next_page_token(
        self,
        response: requests.Response,
        previous_token: Any | None,
    ) -> Any | None:
        """Page through endpoints that expose a ``Page`` envelope.

        Marketman returns ``Page = {Skip, Take, Total}`` for paginated
        endpoints. We continue while the response contains a full page worth
        of records; stop when fewer than ``PAGE_SIZE`` records come back.
        """
        if not self.paginate:
            return None
        try:
            body = response.json()
        except ValueError:
            return None
        records = body.get(self.records_envelope_key) or []
        if len(records) < PAGE_SIZE:
            return None
        previous_skip = int(previous_token or 0)
        return previous_skip + PAGE_SIZE

    @override
    def post_process(
        self,
        row: dict,
        context: dict | None = None,
    ) -> dict | None:
        """Convert Marketman's ``yyyy/mm/dd HH:MM:SS`` timestamps to ISO 8601.

        Every Marketman datetime field is UTC by name, so we rewrite them as ISO 8601 UTC.
        """
        for prop_name in self._datetime_properties:
            value = row.get(prop_name)
            if not isinstance(value, str) or not value:
                continue
            try:
                parsed = datetime.strptime(value, DATETIME_FMT)
            except ValueError:
                continue
            row[prop_name] = parsed.replace(tzinfo=timezone.utc).isoformat()
        return row

    @cached_property
    def _datetime_properties(self) -> set[str]:
        """Top-level schema property names declared as ``format: date-time``."""
        return {
            name
            for name, spec in (self.schema.get("properties") or {}).items()
            if isinstance(spec, dict) and spec.get("format") == "date-time"
        }

    @override
    def validate_response(self, response: requests.Response) -> None:
        """Validate Marketman responses, raising on transport or API errors."""
        super().validate_response(response)
        try:
            body = response.json()
        except ValueError:
            return
        if isinstance(body, dict) and body.get("IsSuccess") is False:
            error = body.get("ErrorMessage") or "Unknown error"
            raise FatalAPIError(f"Marketman {self.name} returned IsSuccess=false: {error}")


class DateFilteredMarketmanStream(MarketmanStream):
    """Base class for Marketman endpoints that take a UTC date range.

    Concrete subclasses inherit ``DateTimeFromUTC`` / ``DateTimeToUTC``
    body fields derived from the stream's replication state.
    """

    @override
    def extra_payload(self, context: dict | None) -> dict[str, Any]:
        """Inject the ``DateTimeFromUTC`` and ``DateTimeToUTC`` body fields."""
        date_from, date_to = self._date_range(context)
        return {
            "DateTimeFromUTC": date_from,
            "DateTimeToUTC": date_to,
        }


class UpdateDateFilteredMarketmanStream(MarketmanStream):
    """Base class for Marketman endpoints that take an ``UpdateDate`` filter.

    Concrete subclasses inherit a body that includes ``UpdateDate`` set to
    the stream's starting timestamp (omitted on the initial sync, when no
    bookmark exists yet).
    """

    @override
    def extra_payload(self, context: dict | None) -> dict[str, Any]:
        """Inject the ``UpdateDate`` body field from the stream's starting timestamp."""
        starting = self.get_starting_timestamp(context)
        if starting is None:
            return {}
        return {"UpdateDate": self._format_marketman_datetime(starting)}
