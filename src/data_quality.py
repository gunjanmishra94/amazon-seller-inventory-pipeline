"""Data quality checks, run right after each pipeline stage instead of all at
the end, so a problem is caught (and can stop the run) at the earliest point
it could actually be detected, not after Gold has already been built on top
of it.

Every check writes to a report file (see pipeline.py's `report` argument),
never to the console, the console only gets short status lines with no data
in them; the actual counts and findings live in output/quality_report.txt.

Checks performed, in plain business terms:

  data_quality_bronze (right after the raw files are read):
    1. Flags warehouse stock records that show a negative quantity on hand
    2. Flags bundle recipes that reference a product we don't recognize
    3. Flags bundle recipes missing a valid "how many needed" quantity
    4. Counts used/returned products (informational, actual exclusion
       happens later, when Gold is built)

  data_quality_silver (right after Silver is built):
    5. Confirms how many duplicate/corrected stock updates got cleaned up

  data_quality_gold (right after Gold is built):
    6. Counts products with no reliable recent sales data (so they can never
       be marked out of stock, since we have no sales-speed to compare against)
    7. Counts how many products are currently out of stock vs. overstocked
    8. Confirms the report has no duplicate rows, this is the one check that
       actually stops the run if it fails, not just a logged warning
"""

import sys
from typing import TextIO

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from silver import dedup_amazon_stock


def data_quality_bronze(bronze: dict, report: TextIO) -> None:
    report.write("\n-- Bronze data quality --\n")

    # Check 1: warehouse stock records with a negative quantity on hand
    negative_local_rows = bronze["local_stock_inventory"].filter(
        F.col("available_quantity") < 0
    ).count()
    report.write(
        f"- Warehouse stock: {negative_local_rows} record(s) showed a negative "
        f"quantity on hand; will be treated as zero, not trusted as-is\n"
    )

    # Check 2: bundle recipes referencing an unknown product
    bridge_skus = bronze["bridge_sku_ean"].select("sku_id").distinct()
    orphan_bridge_skus = bridge_skus.join(
        bronze["dim_sku"], on="sku_id", how="left_anti"
    ).count()
    report.write(
        f"- Bundle recipes: {orphan_bridge_skus} product(s) referenced in a bundle "
        f"recipe don't exist in the product catalog (worth investigating)\n"
    )

    # Check 3: bundle recipes missing a valid required quantity
    bad_bundle_rows = bronze["bridge_sku_ean"].filter(
        F.col("ean_quantity_per_sku").isNull() | (F.col("ean_quantity_per_sku") <= 0)
    ).count()
    report.write(
        f"- Bundle recipes: {bad_bundle_rows} component(s) are missing a valid "
        f"required quantity; will be treated as unavailable (0 units)\n"
    )

    # Check 4: used/returned products (informational)
    used_sku_count = bronze["dim_sku"].filter(F.col("is_used_sku") == 1).count()
    report.write(
        f"- Product catalog: {used_sku_count} used/returned product(s) will be "
        f"excluded once the report is built\n"
    )
    report.flush()


def data_quality_silver(bronze_amazon_stock: DataFrame, report: TextIO) -> None:
    report.write("\n-- Silver data quality --\n")

    # Check 5: how many duplicate/corrected stock updates got cleaned up
    raw_amazon_rows = bronze_amazon_stock.count()
    deduped_amazon_rows = dedup_amazon_stock(bronze_amazon_stock).count()
    report.write(
        f"- Amazon stock feed: cleaned up "
        f"{raw_amazon_rows - deduped_amazon_rows} duplicate/corrected stock "
        f"updates ({raw_amazon_rows} records -> {deduped_amazon_rows})\n"
    )
    report.flush()


def data_quality_gold(gold: DataFrame, report: TextIO) -> None:
    report.write("\n-- Gold data quality --\n")

    # Check 6: products with no reliable recent sales data
    total_rows = gold.count()
    no_velocity_rows = gold.filter(F.col("demand_velocity_source") == "NONE").count()
    report.write(
        f"- Report: {no_velocity_rows} of {total_rows} product/seller/day rows have "
        f"no reliable recent sales data, so they can never be marked out of stock\n"
    )

    # Check 7: out of stock vs. overstocked counts
    oos_rows = gold.filter(F.col("is_oos")).count()
    overstock_rows = gold.filter(F.col("is_overstock")).count()
    report.write(f"- Report: {oos_rows} row(s) are out of stock, {overstock_rows} row(s) are overstocked\n")

    # Check 8: no duplicate rows in the report (this one can fail the run)
    pk_violations = gold.groupBy("date", "sku_id", "seller_id").count().filter(
        F.col("count") > 1
    ).count()
    if pk_violations > 0:
        report.write(
            f"!! DATA INTEGRITY PROBLEM: {pk_violations} product/seller/day "
            f"combination(s) appear more than once in the report, stopping the run.\n"
        )
        report.flush()
        print("Data quality check failed, see output/quality_report.txt for details.")
        sys.exit(1)
    report.write("- Report: every product/seller/day combination appears exactly once.\n")
    report.flush()
