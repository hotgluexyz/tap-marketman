"""Stream classes for tap-marketman.

Marketman exposes the following endpoints relevant to this tap (all under
``/v3/buyers/`` and POST-only):

* ``partneraccounts/GetAuthorisedAccounts`` — list locations
* ``inventory/GetInventoryItems``           — items with pricing (paginated)
* ``inventory/GetMenuItems``                — POS-facing menu items (paginated)
* ``inventory/GetPreps``                    — recipe prep items (paginated)
* ``inventory/GetInventoryCounts``          — physical counts (date range)
* ``inventory/GetTransfers``                — transfers between locations
* ``inventory/GetWasteEvents``              — waste events
"""

from __future__ import annotations

from typing import Any

from hotglue_singer_sdk import typing as th
from typing_extensions import override

from tap_marketman.client import (
    DateFilteredMarketmanStream,
    MarketmanStream,
    UpdateDateFilteredMarketmanStream,
)

SUB_ITEM_PROPERTIES = th.PropertiesList(
    th.Property("ItemID", th.StringType),
    th.Property("ItemName", th.StringType),
    th.Property("ItemTypeName", th.StringType),
    th.Property("UsageNet", th.NumberType),
    th.Property("LossPercent", th.NumberType),
    th.Property("ActualUsage", th.NumberType),
    th.Property("SortIndex", th.IntegerType),
    th.Property("ItemMeasureTypeID", th.IntegerType),
)


class LocationsStream(MarketmanStream):
    """Authorised buyer accounts (locations) the API key has access to."""

    name = "locations"
    path = "/buyers/partneraccounts/GetAuthorisedAccounts"

    primary_keys = ["Guid"]
    replication_key = None
    requires_buyer_guid = False
    paginate = False

    records_jsonpath = "$.Buyers[*]"
    records_envelope_key = "Buyers"

    schema = th.PropertiesList(
        th.Property("Guid", th.StringType, required=True),
        th.Property("BuyerName", th.StringType),
    ).to_dict()


class InventoryItemsStream(UpdateDateFilteredMarketmanStream):
    """Inventory items (with pricing) for the configured BuyerGuid."""

    name = "inventory_items"
    path = "/buyers/inventory/GetInventoryItems"

    primary_keys = ["ID"]
    replication_key = "UpdateDate"
    paginate = True

    records_jsonpath = "$.Items[*]"
    records_envelope_key = "Items"

    schema = th.PropertiesList(
        th.Property("ID", th.StringType, required=True),
        th.Property("Name", th.StringType),
        th.Property("UpdateDate", th.DateTimeType),
        th.Property("CategoryID", th.IntegerType),
        th.Property("CategoryName", th.StringType),
        th.Property("AboutTheItem", th.StringType),
        th.Property("UOMName", th.StringType),
        th.Property("UOMID", th.IntegerType),
        th.Property("ReportingUOM", th.StringType),
        th.Property("MinOnHand", th.NumberType),
        th.Property("ParLevel", th.NumberType),
        th.Property("MinOrderQty", th.NumberType),
        th.Property("MaxOrderQty", th.NumberType),
        th.Property("DateRangeType", th.StringType),
        th.Property("StorageNames", th.ArrayType(th.StringType)),
        th.Property("StorageIDs", th.ArrayType(th.IntegerType)),
        th.Property("OnHand", th.NumberType),
        th.Property("BOMPrice", th.NumberType),
        th.Property("DebitAccountName", th.StringType),
        th.Property("IsDeleted", th.BooleanType),
        th.Property("CountDefOptions", th.ArrayType(th.ObjectType())),
        th.Property(
            "PurchaseItems",
            th.ArrayType(
                th.PropertiesList(
                    th.Property("Name", th.StringType),
                    th.Property("SupplierName", th.StringType),
                    th.Property("VendorName", th.StringType),
                    th.Property("VendorGuid", th.StringType),
                    th.Property("PackQty", th.NumberType),
                    th.Property("PacksPerCase", th.NumberType),
                    th.Property("UOMName", th.StringType),
                    th.Property("UOMID", th.IntegerType),
                    th.Property("ProductCode", th.StringType),
                    th.Property("Price", th.NumberType),
                    th.Property("MinOrderQty", th.NumberType),
                    th.Property("PriceType", th.StringType),
                    th.Property("CatalogItemCode", th.IntegerType),
                    th.Property("TaxLevelID", th.IntegerType),
                    th.Property("TaxValue", th.NumberType),
                    th.Property("PriceWithVat", th.NumberType),
                    th.Property("ScanBarcode", th.StringType),
                    th.Property("Ratio", th.NumberType),
                    th.Property("IsMainPurchaseOption", th.BooleanType),
                    th.Property("DeletedFromSupplier", th.BooleanType),
                    th.Property("IsForOrdering", th.BooleanType),
                ),
            ),
        ),
    ).to_dict()


class MenuItemsStream(MarketmanStream):
    """POS-facing menu items for the configured BuyerGuid.

    No server-side date filter, and ``UpdateDate`` is left ``null`` on items
    created via the API (only set when an item is edited in the Marketman UI),
    so this stream must be full-refresh — using ``UpdateDate`` as a replication
    key would crash the SDK on the first ``None`` value.
    """

    name = "menu_items"
    path = "/buyers/inventory/GetMenuItems"

    primary_keys = ["ID"]
    replication_key = None
    paginate = True

    records_jsonpath = "$.Items[*]"
    records_envelope_key = "Items"

    schema = th.PropertiesList(
        th.Property("ID", th.IntegerType, required=True),
        th.Property("Name", th.StringType),
        th.Property("UpdateDate", th.DateTimeType),
        th.Property("CategoryID", th.IntegerType),
        th.Property("CategoryName", th.StringType),
        th.Property("POSCodes", th.StringType),
        th.Property("Skus", th.ArrayType(th.StringType)),
        th.Property("SalePriceWithoutVAT", th.NumberType),
        th.Property("SalePriceWithVAT", th.NumberType),
        th.Property("Type", th.StringType),
        th.Property("MinOnHand", th.NumberType),
        th.Property("ParLevel", th.NumberType),
        th.Property("BOMPrice", th.NumberType),
        th.Property("BOMPriceFC", th.NumberType),
        th.Property("MaxFC", th.NumberType),
        th.Property("PrepTime", th.NumberType),
        th.Property("CookTime", th.NumberType),
        th.Property("CookingInstructions", th.StringType),
        th.Property("AboutTheItem", th.StringType),
        th.Property("IsDeleted", th.BooleanType),
        th.Property("SubItems", th.ArrayType(SUB_ITEM_PROPERTIES)),
        th.Property(
            "LocationSyncInfos",
            th.ArrayType(
                th.PropertiesList(
                    th.Property("LocationGuid", th.StringType),
                    th.Property("LocationName", th.StringType),
                    th.Property("IsSync", th.BooleanType),
                    th.Property("SyncStatus", th.StringType),
                ),
            ),
        ),
    ).to_dict()


class PrepsStream(UpdateDateFilteredMarketmanStream):
    """Prep / recipe items for the configured BuyerGuid."""

    name = "preps"
    path = "/buyers/inventory/GetPreps"

    primary_keys = ["ID"]
    replication_key = "UpdateDate"
    paginate = True

    records_jsonpath = "$.Items[*]"
    records_envelope_key = "Items"

    schema = th.PropertiesList(
        th.Property("ID", th.StringType, required=True),
        th.Property("Name", th.StringType),
        th.Property("UpdateDate", th.DateTimeType),
        th.Property("IsSelfStock", th.BooleanType),
        th.Property("CategoryID", th.IntegerType),
        th.Property("CategoryName", th.StringType),
        th.Property("UOMName", th.StringType),
        th.Property("UOMID", th.IntegerType),
        th.Property("MinOnHand", th.NumberType),
        th.Property("ParLevel", th.NumberType),
        th.Property("StorageNames", th.ArrayType(th.StringType)),
        th.Property("StorageIDs", th.ArrayType(th.IntegerType)),
        th.Property("ProdQuantity", th.NumberType),
        th.Property("OnHand", th.NumberType),
        th.Property("BOMPrice", th.NumberType),
        th.Property("PrepTimeSecs", th.NumberType),
        th.Property("CookTimeSecs", th.NumberType),
        th.Property("IsDeleted", th.BooleanType),
        th.Property("SubItems", th.ArrayType(SUB_ITEM_PROPERTIES)),
    ).to_dict()


class InventoryCountsStream(DateFilteredMarketmanStream):
    """Physical inventory counts within a UTC date range."""

    name = "inventory_counts"
    path = "/buyers/inventory/GetInventoryCounts"

    primary_keys = ["ID"]
    replication_key = "CountDateUTC"

    records_jsonpath = "$.InventoryCounts[*]"
    records_envelope_key = "InventoryCounts"

    schema = th.PropertiesList(
        th.Property("ID", th.StringType, required=True),
        th.Property("BuyerName", th.StringType),
        th.Property("BuyerGuid", th.StringType),
        th.Property("CountDateUTC", th.DateTimeType),
        th.Property("CountDateType", th.IntegerType),
        th.Property("IsLocked", th.BooleanType),
        th.Property("PriceTotalWithoutVAT", th.NumberType),
        th.Property("Commments", th.StringType),
        th.Property(
            "Lines",
            th.ArrayType(
                th.PropertiesList(
                    th.Property("LineID", th.StringType),
                    th.Property("ItemID", th.StringType),
                    th.Property("ItemName", th.StringType),
                    th.Property("ParentItemID", th.StringType),
                    th.Property("TotalCount", th.NumberType),
                    th.Property("TotalValue", th.NumberType),
                    th.Property("CountDefDetails", th.ArrayType(th.PropertiesList(
                        th.Property("CountDefID", th.IntegerType),
                        th.Property("CountDefName", th.StringType),
                        th.Property("CountDefAmount", th.NumberType),
                    ))),
                ),
            ),
        ),
    ).to_dict()

    @override
    def extra_payload(self, context: dict | None) -> dict[str, Any]:
        """Add ``GetLineDetails`` so we receive the line-level breakdown."""
        payload = super().extra_payload(context)
        payload["GetLineDetails"] = True
        payload["GetCountDefDetails"] = True
        return payload


class TransfersStream(DateFilteredMarketmanStream):
    """Inventory transfers between buyer locations within a UTC date range."""

    name = "transfers"
    path = "/buyers/inventory/GetTransfers"

    primary_keys = ["ID"]
    replication_key = "DateUTC"

    records_jsonpath = "$.Transfers[*]"
    records_envelope_key = "Transfers"

    schema = th.PropertiesList(
        th.Property("ID", th.StringType, required=True),
        th.Property("BuyerFromName", th.StringType),
        th.Property("BuyerFromGuid", th.StringType),
        th.Property("BuyerToName", th.StringType),
        th.Property("BuyerToGuid", th.StringType),
        th.Property("DateUTC", th.DateTimeType),
        th.Property("TotalPriceWithoutVAT", th.NumberType),
        th.Property("Commments", th.StringType),
        th.Property("TransferStatus", th.StringType),
        th.Property(
            "Lines",
            th.ArrayType(
                th.PropertiesList(
                    th.Property("LineID", th.StringType),
                    th.Property("ItemID", th.StringType),
                    th.Property("ItemName", th.StringType),
                    th.Property("Quantity", th.NumberType),
                    th.Property("TotalPriceWithoutVAT", th.NumberType),
                    th.Property("UOMID", th.StringType),
                    th.Property("UOMName", th.StringType),
                ),
            ),
        ),
    ).to_dict()


class WasteEventsStream(DateFilteredMarketmanStream):
    """Waste events recorded against the buyer's inventory within a date range."""

    name = "waste_events"
    path = "/buyers/inventory/GetWasteEvents"

    primary_keys = ["ID"]
    replication_key = "DateUTC"

    records_jsonpath = "$.WasteEvents[*]"
    records_envelope_key = "WasteEvents"

    schema = th.PropertiesList(
        th.Property("ID", th.StringType, required=True),
        th.Property("BuyerName", th.StringType),
        th.Property("BuyerGuid", th.StringType),
        th.Property("DateUTC", th.DateTimeType),
        th.Property("TotalPriceWithoutVAT", th.NumberType),
        th.Property("Commments", th.StringType),
        th.Property(
            "Lines",
            th.ArrayType(
                th.PropertiesList(
                    th.Property("LineID", th.StringType),
                    th.Property("ItemID", th.StringType),
                    th.Property("ItemName", th.StringType),
                    th.Property("Quantity", th.NumberType),
                    th.Property("TotalPriceWithoutVAT", th.NumberType),
                    th.Property("UOMID", th.StringType),
                    th.Property("UOMName", th.StringType),
                    th.Property("ItemType", th.StringType),
                    th.Property("ItemCategory", th.StringType),
                ),
            ),
        ),
    ).to_dict()
