"""Bronze layer: typed, 1:1 ingestion of the raw source CSVs. No business logic."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from spark_io import read_csv

SCHEMAS = {
    "amazon_stock_daily": StructType(
        [
            StructField("stock_snapshot_id", StringType()),
            StructField("date", DateType()),
            StructField("sku_id", LongType()),
            StructField("seller_id", LongType()),
            StructField("marketplace_id", StringType()),
            StructField("disposition", StringType()),
            StructField("stock_qty", LongType()),
            StructField("source_updated_at", TimestampType()),
        ]
    ),
    "local_stock_inventory": StructType(
        [
            StructField("local_stock_id", StringType()),
            StructField("date", DateType()),
            StructField("ean_id", LongType()),
            StructField("storage_location", StringType()),
            StructField("status", StringType()),
            StructField("available_quantity", LongType()),
            StructField("best_before_date", DateType()),
            StructField("is_expired", IntegerType()),
        ]
    ),
    "avg_sales_velocity": StructType(
        [
            StructField("date", DateType()),
            StructField("sku_id", LongType()),
            StructField("seller_id", LongType()),
            StructField("avg_units_7d", DoubleType()),
            StructField("avg_units_30d", DoubleType()),
            StructField("avg_net_revenue_eur_7d", DoubleType()),
            StructField("avg_net_revenue_eur_30d", DoubleType()),
        ]
    ),
    "dim_sku": StructType(
        [
            StructField("sku_id", LongType()),
            StructField("sku", StringType()),
            StructField("product_name", StringType()),
            StructField("is_used_sku", IntegerType()),
            StructField("primary_marketplace_id", StringType()),
        ]
    ),
    "dim_ean": StructType(
        [
            StructField("ean_id", LongType()),
            StructField("ean", StringType()),
            StructField("brand", StringType()),
            StructField("product_name", StringType()),
        ]
    ),
    "bridge_sku_ean": StructType(
        [
            StructField("sku_id", LongType()),
            StructField("ean_id", LongType()),
            StructField("ean_quantity_per_sku", DoubleType()),
        ]
    ),
    "dim_seller": StructType(
        [
            StructField("seller_id", LongType()),
            StructField("seller_short_name", StringType()),
            StructField("seller_name", StringType()),
        ]
    ),
}


def read_bronze(spark: SparkSession, data_dir: str, name: str) -> DataFrame:
    return read_csv(spark, f"{data_dir}/{name}.csv", SCHEMAS[name])
