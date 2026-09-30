"""
Amazon OOS / Availability Gold pipeline, local stand-in for a Microsoft Fabric
Lakehouse notebook (PySpark).

    data/*.csv -> Bronze (typed) -> Silver (deduped, filtered) -> Gold

Business logic lives one file per pipeline stage, bronze.py, silver.py,
gold.py, quality.py, and spark_io.py holds generic Spark/file helpers. This
file only wires those stages together and decides where things get read from
and written to.

Tables are written as Parquet, not Delta, see README.md for that tradeoff
and all other decisions.

Gold grain: (date, sku_id, seller_id). avg_sales_velocity.csv has no marketplace_id,
so Amazon SELLABLE stock is summed across all marketplaces reported for a seller
before comparing it to demand; the marketplaces are kept in `marketplaces_reported`
for transparency.
"""

from pyspark.sql import functions as F

from bronze import SCHEMAS, read_bronze
from gold import GOLD_TABLE_NAME, build_gold
from data_quality import data_quality_bronze, data_quality_gold, data_quality_silver
from silver import (
    build_silver_amazon_stock,
    build_silver_local_replenishment,
    build_silver_local_stock,
    build_silver_sales_velocity,
)
from spark_io import build_spark, dataframe_to_markdown, write_csv_preview, write_table, write_text
from viewer import build_gold_viewer_html

DATA_DIR = "data"
LAKEHOUSE_DIR = "lakehouse"
OUTPUT_DIR = "output"


def lakehouse_path(layer: str, name: str) -> str:
    return f"{LAKEHOUSE_DIR}/{layer}/{name}"


def output_path(layer: str, name: str) -> str:
    return f"{OUTPUT_DIR}/{layer}/{name}"


def main() -> None:
    spark = build_spark("oos-gold-pipeline")

    bronze = {name: read_bronze(spark, DATA_DIR, name) for name in SCHEMAS}
    for name, df in bronze.items():
        write_table(df, lakehouse_path("bronze", name))
        write_csv_preview(df, output_path("bronze", name))

    report = open(f"{OUTPUT_DIR}/quality_report.txt", "w")
    data_quality_bronze(bronze, report)

    silver_amazon_stock = write_table(
        build_silver_amazon_stock(bronze["amazon_stock_daily"]),
        lakehouse_path("silver", "amazon_stock"),
    )
    silver_local_stock = write_table(
        build_silver_local_stock(bronze["local_stock_inventory"]),
        lakehouse_path("silver", "local_stock"),
    )
    silver_velocity = write_table(
        build_silver_sales_velocity(bronze["avg_sales_velocity"]),
        lakehouse_path("silver", "sales_velocity"),
    )
    silver_local_replenishment = write_table(
        build_silver_local_replenishment(bronze["bridge_sku_ean"], silver_local_stock),
        lakehouse_path("silver", "local_replenishment"),
    )
    for name, df in [
        ("amazon_stock", silver_amazon_stock),
        ("local_stock", silver_local_stock),
        ("sales_velocity", silver_velocity),
        ("local_replenishment", silver_local_replenishment),
    ]:
        write_csv_preview(df, output_path("silver", name))
    data_quality_silver(bronze["amazon_stock_daily"], report)

    gold = build_gold(
        silver_amazon_stock,
        silver_velocity,
        silver_local_replenishment,
        bronze["dim_sku"],
        bronze["dim_seller"],
    )
    write_table(gold, lakehouse_path("gold", GOLD_TABLE_NAME))
    gold_sorted = gold.orderBy("date", "sku_id", "seller_id")
    write_csv_preview(gold_sorted, output_path("gold", GOLD_TABLE_NAME))
    write_text(build_gold_viewer_html(gold_sorted.toPandas()), f"{OUTPUT_DIR}/viewer.html")
    data_quality_gold(gold, report)
    report.close()

    interesting = gold.filter(
        F.col("sku_id").isin(1001, 1002, 1003, 1005, 1006, 1007)
        & F.col("date").isin("2026-07-01", "2026-07-04", "2026-07-20")
    ).orderBy("sku_id", "date")

    pdf = interesting.toPandas()
    with open(f"{OUTPUT_DIR}/gold/{GOLD_TABLE_NAME}_preview.md", "w") as f:
        f.write("# Gold table preview, edge cases\n\n")
        f.write(dataframe_to_markdown(pdf))
        f.write("\n")

    spark.stop()
    print("Pipeline finished. See output/ for results, output/viewer.html to browse the Gold table in a browser, and output/quality_report.txt for the quality report.")


if __name__ == "__main__":
    main()
