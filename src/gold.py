"""Gold layer: the business-facing OOS / availability report.
Each function below implements exactly one rule from the business contract."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

OVERSTOCK_DAYS_THRESHOLD = 90
GOLD_TABLE_NAME = "gold_amazon_availability_oos_daily"


def with_demand_velocity(df: DataFrame) -> DataFrame:
    """7d velocity if positive, else 30d if positive, else no signal. Explicit
    zero/negative values must not themselves imply demand."""
    return df.withColumn(
        "demand_velocity_used",
        F.when(F.col("avg_units_7d") > 0, F.col("avg_units_7d")).when(
            F.col("avg_units_30d") > 0, F.col("avg_units_30d")
        ),
    ).withColumn(
        "demand_velocity_source",
        F.when(F.col("avg_units_7d") > 0, F.lit("7D"))
        .when(F.col("avg_units_30d") > 0, F.lit("30D"))
        .otherwise(F.lit("NONE")),
    )


def with_oos_flag(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "is_oos",
        F.col("demand_velocity_used").isNotNull()
        & (F.col("amazon_sellable_qty") < F.col("demand_velocity_used")),
    )


def with_revenue_at_risk(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "daily_net_revenue_at_risk_eur",
        F.when(~F.col("is_oos"), F.lit(0.0))
        .when(F.col("demand_velocity_source") == "7D", F.col("avg_net_revenue_eur_7d"))
        .otherwise(F.col("avg_net_revenue_eur_30d")),
    )


def with_inventory_reach(df: DataFrame) -> DataFrame:
    # Dividing by a null demand_velocity_used naturally yields a null reach.
    return df.withColumn(
        "amazon_inventory_reach_days",
        F.col("amazon_sellable_qty") / F.col("demand_velocity_used"),
    ).withColumn(
        "total_inventory_reach_days",
        (F.col("amazon_sellable_qty") + F.col("local_replenishment_units"))
        / F.col("demand_velocity_used"),
    )


def with_overstock_flag(df: DataFrame) -> DataFrame:
    """>90 days of stock at a positive 30d velocity, or any stock at all when the
    30d velocity is explicitly non-positive (not merely unknown/null)."""
    days_of_stock = F.col("amazon_sellable_qty") / F.col("avg_units_30d")
    return df.withColumn(
        "is_overstock",
        F.when(
            (F.col("avg_units_30d") > 0) & (days_of_stock > OVERSTOCK_DAYS_THRESHOLD),
            True,
        )
        .when((F.col("avg_units_30d") <= 0) & (F.col("amazon_sellable_qty") > 0), True)
        .otherwise(False),
    )


GOLD_COLUMNS = [
    "date",
    "sku_id",
    "sku",
    "product_name",
    "seller_id",
    "seller_short_name",
    "primary_marketplace_id",
    "marketplaces_reported",
    "amazon_sellable_qty",
    "avg_units_7d",
    "avg_units_30d",
    "demand_velocity_used",
    "demand_velocity_source",
    "is_oos",
    "local_replenishment_units",
    "amazon_inventory_reach_days",
    "total_inventory_reach_days",
    "is_overstock",
    "daily_net_revenue_at_risk_eur",
]


def build_gold(
    silver_amazon_stock: DataFrame,
    silver_velocity: DataFrame,
    silver_local_replenishment: DataFrame,
    dim_sku: DataFrame,
    dim_seller: DataFrame,
) -> DataFrame:
    valid_skus = dim_sku.filter(F.col("is_used_sku") != 1)

    df = (
        silver_amazon_stock.join(valid_skus, "sku_id")
        .join(dim_seller, "seller_id", "left")
        .join(silver_velocity, ["date", "sku_id", "seller_id"], "left")
        .join(silver_local_replenishment, ["date", "sku_id"], "left")
        .fillna({"local_replenishment_units": 0})
    )

    df = (
        df.transform(with_demand_velocity)
        .transform(with_oos_flag)
        .transform(with_revenue_at_risk)
        .transform(with_inventory_reach)
        .transform(with_overstock_flag)
    )

    return df.select(*GOLD_COLUMNS)
