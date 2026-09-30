"""Generic Spark session and I/O helpers. Nothing here knows about the OOS
pipeline's business logic, schemas, or folder layout, see pipeline.py
for that."""

import glob
import os

from pyspark.sql import DataFrame, SparkSession


def build_spark(app_name: str) -> SparkSession:
    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def read_csv(spark: SparkSession, path: str, schema) -> DataFrame:
    return spark.read.option("header", True).schema(schema).csv(path)


def write_table(df: DataFrame, path: str) -> DataFrame:
    df.write.mode("overwrite").parquet(path)
    return df


def write_csv_preview(df: DataFrame, path: str) -> DataFrame:
    """Human-readable CSV copy of a table. Spark's _SUCCESS/.crc marker files are
    Hadoop write-job bookkeeping, not anything a human opening this CSV needs,
    so they're removed after writing."""
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(path)
    for marker in glob.glob(f"{path}/_SUCCESS") + glob.glob(f"{path}/.*.crc"):
        os.remove(marker)
    return df


def write_text(content: str, path: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def dataframe_to_markdown(pdf) -> str:
    cols = list(pdf.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in pdf.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.tolist()) + " |")
    return "\n".join(lines)
