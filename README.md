# Solution: Amazon Availability / OOS Gold Model

Live viewer: https://gunjanmishra94.github.io/amazon-seller-inventory-pipeline/

A daily Amazon availability / out-of-stock (OOS) report. It runs as a
local stand-in for a Microsoft Fabric Lakehouse notebook: PySpark
executed inside Docker, writing a medallion (Bronze → Silver → Gold)
layout under `lakehouse/`.

## How to run it

```bash
make run
```

- Requires Docker Desktop. Nothing else needs installing.
- Reads `data/*.csv`, writes tables to `lakehouse/` and a preview to `output/`.
- `make shell`: open a shell in the same container, for debugging.
- `make clean`: delete the generated `lakehouse/` and `output/` folders.

Note: tables are written as plain Parquet, not Delta. Real Fabric would use
Delta, but that's a one-line change at write time, same logic either way.
Delta was skipped here to avoid an extra dependency.

## Target model

**One Gold table**, `gold_amazon_availability_oos_daily`, at grain
**(date, sku_id, seller_id)**.

| Column | Meaning |
|---|---|
| `sku_id`, `sku`, `product_name` | SKU identity (used/return SKUs already excluded) |
| `seller_id`, `seller_short_name` | Seller/account identity |
| `primary_marketplace_id` | Business-maintained marketplace from `dim_sku` |
| `marketplaces_reported` | Which Amazon marketplace(s) contributed to this row's stock (see below) |
| `amazon_sellable_qty` | Current usable Amazon inventory (SELLABLE only) |
| `avg_units_7d`, `avg_units_30d` | Pass-through demand signals |
| `demand_velocity_used`, `demand_velocity_source` | The velocity actually used for OOS/reach/revenue, and which window it came from (`7D` / `30D` / `NONE`) |
| `is_oos` | The OOS flag |
| `local_replenishment_units` | How many complete SKU units the local warehouse could currently assemble |
| `amazon_inventory_reach_days` | Days of stock from Amazon inventory alone |
| `total_inventory_reach_days` | Days of stock from Amazon + local combined |
| `is_overstock` | Overstock flag |
| `daily_net_revenue_at_risk_eur` | Revenue at risk, 0 unless `is_oos` |

A single table (rather than a star schema of separate fact/dimension Gold
objects) was chosen because the case study asks for one clear, reviewable
availability/OOS report, not a general-purpose semantic model.

## Key modeling decisions and assumptions

**1. Grain: `(date, sku_id, seller_id)`, no `marketplace_id`.**
Demand/revenue data has no marketplace column, but one seller can report
stock in two marketplaces (seller 10: `DE` + `AT`). So SELLABLE stock is
summed per seller before comparing to demand; the marketplaces are kept in
`marketplaces_reported` so nothing is hidden.

**2. Amazon stock is deduplicated on `stock_snapshot_id` first.**
The data has same-day corrections (same id, different qty/timestamp). Only
the latest `source_updated_at` per id is kept.

**3. Used/return SKUs (`is_used_sku = 1`) are excluded before Gold, not
filtered after.** They're removed via an inner join to `dim_sku`, so they
never touch stock, demand, or bundle calculations.

**4. Local replenishment is a bottleneck (kitting) calculation.**
A bundle's producible units = `MIN` across components of
`floor(local_qty / qty_per_sku)`; whichever component runs out first caps
the whole bundle. A missing/zero `qty_per_sku` (both occur in the data)
counts as 0, not ignored.

**5. Local stock never changes `is_oos`.**
Only `amazon_sellable_qty` vs. demand decides OOS; local stock only feeds
reach and replenishment.

**6. Negative `available_quantity` is floored at 0, not dropped.**
One row has `-2`. Dropping it would just as silently understate stock;
flooring it is visible in the data-quality report instead.

**7. Velocity, revenue, and overstock share one rule: 7-day value if
positive, else 30-day if positive, else nothing.**
An explicit zero/negative counts as "no demand," not missing data, so it
can't trigger OOS, and (per the overstock rule) is itself an overstock
signal.

**8. `NULL` 30-day velocity is not the same as non-positive, for overstock.**
The contract flags non-positive 30-day velocity as overstock; `NULL` is
unknown, not non-positive, so it isn't flagged. (Not in the sample data;
handled defensively.)

**9. Orphan and malformed reference data is surfaced, not hidden.**
`sku_id` 1010 in the bundle table has no match in `dim_sku`; it can never
reach Gold, but the data-quality report counts it so it's visible, not a
silent gap.

## Requirement Traceability

### Business questions

The five business questions all land as columns in the one Gold output file:
`output/gold/gold_amazon_availability_oos_daily/*.csv` (one row per
product/seller/day; a smaller edge-case preview is at
`output/gold/gold_amazon_availability_oos_daily_preview.md`). The right-hand
column below is the code that computes each one.

| Case study asked for | Column in that CSV | Computed by |
|---|---|---|
| Which products are currently OOS on Amazon | `is_oos` | `with_oos_flag` in `src/gold.py` |
| How much usable Amazon inventory is available | `amazon_sellable_qty` | `build_silver_amazon_stock` in `src/silver.py` |
| What local inventory could potentially support replenishment | `local_replenishment_units` | `build_silver_local_replenishment` in `src/silver.py` |
| How long available inventory is expected to last | `amazon_inventory_reach_days` / `total_inventory_reach_days` | `with_inventory_reach` in `src/gold.py` |
| What daily net revenue is at risk when OOS | `daily_net_revenue_at_risk_eur` | `with_revenue_at_risk` in `src/gold.py` |

`is_overstock` is also in that CSV. It isn't one of the five questions above;
it answers the case study's separate "Overstock" business rule instead, computed
by `with_overstock_flag` in `src/gold.py`.

### Modeling design decisions

| Case study asked for | Where it's answered |
|---|---|
| Which target table(s)/view(s) are appropriate | "Target model" above, one Gold table |
| The grain of each target object | "Target model" above, `(date, sku_id, seller_id)` |
| How the different source grains should be modeled | Decisions #1, #4, #5 in "Key modeling decisions" above |
| Which metrics/attributes are required | The column table in "Target model" above |
| How the sources should be combined | `build_gold` in `src/gold.py`, and Decisions #1-#9 above for the reasoning |

## Data quality checks included

- Checks run right after each stage (Bronze, Silver, Gold), not all at the
  end, so a problem is caught as early as it's detectable.
- Every check writes to `output/quality_report.txt`: row counts before/after
  dedup, corrected negative quantities, excluded used-SKUs, orphan bridge
  references, malformed bundle quantities, rows with no demand signal, and
  OOS/overstock counts.
- The Gold check also asserts `(date, sku_id, seller_id)` is unique,
  failing the run if that primary key is violated.

## Result preview

`output/` mirrors `lakehouse/`'s Bronze/Silver/Gold layout as CSV instead of
Parquet. Every table at every layer gets a CSV copy, not just the final one:

- Gold (the deliverable): `output/gold/gold_amazon_availability_oos_daily/`
- **Interactive viewer:** `output/viewer.html`, a filterable/sortable table
  of the Gold data. Just open it in a browser (no Docker, Spark, or server
  needed); first load takes ~10-30s to start up.
- Edge-case preview (the decisions discussed above): `output/gold/gold_amazon_availability_oos_daily_preview.md`
- Silver (cleaned/deduped/aggregated): `output/silver/{amazon_stock,local_stock,sales_velocity,local_replenishment}/`
- Bronze (typed, 1:1 with source CSVs): `output/bronze/<source_name>/`
- Parquet originals of all of the above: `lakehouse/`

## Evolving this into a reliable daily Fabric production pipeline

This local demo proves out the business logic on a static CSV extract. Here's
what I'd prioritize to run it daily and reliably on real Microsoft Fabric:

- **Scalability**
  - Right-size compute: a small/medium autoscaling Spark pool, not a fixed
    large one. The transformation (dedup, group-by, a few joins) scales
    linearly, so it doesn't need more than that even as data volume grows.
  - Power BI should read Gold via Direct Lake straight from OneLake instead
    of Import mode, so growing data doesn't mean a growing duplicate copy.

- **Reliability**
  - Incremental ingestion, not full reprocessing. Bronze currently reads the
    whole CSV every run; in production it would ingest only the
    new/changed partition (by `date`, or a watermark on
    `source_updated_at`) using `MERGE INTO` on Delta tables, not `overwrite`.
  - Real data quality gates, not just a report file. Today's checks write to
    a report and can fail the run; in production they'd be pipeline gate
    steps (e.g. a Fabric Data Pipeline activity that stops before bad data
    reaches Gold), with failures routed to a Teams/email alert.

- **Maintainability**
  - Git-backed deployment pipeline: Fabric Git integration with Dev → Test
    → Prod workspaces, so a change to the Gold logic is reviewed and tested
    against a copy of the lakehouse before it reaches the Prod semantic
    model the business dashboard reads from.
  - The Silver/Gold functions are already pure `DataFrame -> DataFrame`
    transforms for exactly this reason: testable in CI without a Fabric
    workspace at all.

- **Cost efficiency**
  - Incremental ingestion (above) is the single biggest lever: full
    reprocessing of a growing Amazon stock/local inventory feed is the main
    avoidable Spark-pool cost.
  - An autoscaling pool and Direct Lake (above) mean paying for actual
    usage, not a fixed-size pool or a duplicate copy of the data.

**Deliberately out of scope:** a star schema of separate Gold tables,
streaming ingestion (the source is a daily batch extract), and a generic
semantic layer. All three earn their cost once there's a second consumer of
this data; none are needed for a single daily report.
