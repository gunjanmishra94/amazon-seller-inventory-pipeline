"""Silver layer: dedup, filter to business-valid rows, conform grain."""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F


def dedup_amazon_stock(bronze_amazon: DataFrame) -> DataFrame:
    """Some stock_snapshot_id rows are same-day corrections; keep the latest one."""
    window = Window.partitionBy("stock_snapshot_id").orderBy(
        F.col("source_updated_at").desc()
    )
    return (
        bronze_amazon.withColumn("rn", F.row_number().over(window))
        .filter(F.col("rn") == 1)
        .drop("rn")
    )


def build_silver_amazon_stock(bronze_amazon: DataFrame) -> DataFrame:
    sellable = dedup_amazon_stock(bronze_amazon).filter(F.col("disposition") == "SELLABLE")
    return sellable.groupBy("date", "sku_id", "seller_id").agg(
        F.sum("stock_qty").alias("amazon_sellable_qty"),
        F.concat_ws(",", F.array_sort(F.collect_set("marketplace_id"))).alias(
            "marketplaces_reported"
        ),
    )


def build_silver_local_stock(bronze_local: DataFrame) -> DataFrame:
    """Only NEW, non-expired stock is usable. Negative quantities are a data-quality
    artifact and are floored at 0 rather than netted against other EANs' stock."""
    usable = bronze_local.filter(
        (F.col("status") == "NEW") & (F.col("is_expired") == 0)
    ).withColumn("qty", F.greatest(F.col("available_quantity"), F.lit(0)))

    return usable.groupBy("date", "ean_id").agg(F.sum("qty").alias("local_usable_qty"))


def build_silver_sales_velocity(bronze_velocity: DataFrame) -> DataFrame:
    return bronze_velocity.dropDuplicates(["date", "sku_id", "seller_id"])


def build_silver_local_replenishment(
    bronze_bridge: DataFrame, silver_local_stock: DataFrame
) -> DataFrame:
    """Complete SKU units the warehouse could assemble today. A SKU can need several
    EAN components in different quantities, so the bottleneck component caps the
    total: units = MIN over components of floor(local_usable_qty / qty_per_sku). A
    missing/non-positive qty_per_sku makes that component's requirement undefined,
    so it contributes 0 rather than being silently skipped."""
    component_stock = bronze_bridge.crossJoin(
        silver_local_stock.select("date").distinct()
    ).join(silver_local_stock, on=["date", "ean_id"], how="left")

    component_units = component_stock.withColumn(
        "local_usable_qty", F.coalesce(F.col("local_usable_qty"), F.lit(0))
    ).withColumn(
        "component_units",
        F.when(
            F.col("ean_quantity_per_sku").isNull() | (F.col("ean_quantity_per_sku") <= 0),
            F.lit(0),
        ).otherwise(F.floor(F.col("local_usable_qty") / F.col("ean_quantity_per_sku"))),
    )

    return component_units.groupBy("date", "sku_id").agg(
        F.min("component_units").alias("local_replenishment_units")
    )
