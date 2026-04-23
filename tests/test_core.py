"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from hotglue_singer_sdk.testing import get_tap_test_class

from tap_marketman.tap import TapMarketman

SAMPLE_CONFIG = {
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    "api_key": "test-api-key",
    "api_password": "test-api-password",
    "buyer_guid": "00000000000000000000000000000000",
}


# Run standard built-in tap tests from the SDK:
TestTapMarketman = get_tap_test_class(
    tap_class=TapMarketman,
    config=SAMPLE_CONFIG,
)


# TODO: Create additional tests as appropriate for your tap.
