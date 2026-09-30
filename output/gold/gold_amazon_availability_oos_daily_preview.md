# Gold table preview, edge cases

| date | sku_id | sku | product_name | seller_id | seller_short_name | primary_marketplace_id | marketplaces_reported | amazon_sellable_qty | avg_units_7d | avg_units_30d | demand_velocity_used | demand_velocity_source | is_oos | local_replenishment_units | amazon_inventory_reach_days | total_inventory_reach_days | is_overstock | daily_net_revenue_at_risk_eur |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-01 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 10 | DE_MAIN | DE | DE | 5 | 4.0 | 3.0 | 4.0 | 7D | False | 10 | 1.25 | 3.75 | False | 0.0 |
| 2026-07-01 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 20 | FR_MAIN | DE | FR | 2 | 1.0 | 1.0 | 1.0 | 7D | False | 10 | 2.0 | 12.0 | False | 0.0 |
| 2026-07-04 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 20 | FR_MAIN | DE | FR | 2 | 1.0 | 1.0 | 1.0 | 7D | False | 7 | 2.0 | 9.0 | False | 0.0 |
| 2026-07-04 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 10 | DE_MAIN | DE | DE | 6000 | 4.0 | 3.0 | 4.0 | 7D | False | 7 | 1500.0 | 1501.75 | True | 0.0 |
| 2026-07-20 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 20 | FR_MAIN | DE | FR | 4 | 1.0 | 1.0 | 1.0 | 7D | False | 7 | 4.0 | 11.0 | False | 0.0 |
| 2026-07-20 | 1001 | SKU-COFFEE-250 | Filter Coffee 250g | 10 | DE_MAIN | DE | DE | 2 | 4.0 | 3.0 | 4.0 | 7D | True | 7 | 0.5 | 2.25 | False | 80.0 |
| 2026-07-01 | 1002 | SKU-GIFT-BUNDLE | Coffee Gift Bundle | 10 | DE_MAIN | DE | DE | 1 | 1.5 | 1.2 | 1.5 | 7D | True | 1 | 0.6666666666666666 | 1.3333333333333333 | False | 45.0 |
| 2026-07-04 | 1002 | SKU-GIFT-BUNDLE | Coffee Gift Bundle | 10 | DE_MAIN | DE | DE | 2000 | 1.5 | 1.2 | 1.5 | 7D | False | 2 | 1333.3333333333333 | 1334.6666666666667 | True | 0.0 |
| 2026-07-20 | 1002 | SKU-GIFT-BUNDLE | Coffee Gift Bundle | 10 | DE_MAIN | DE | DE | 0 | 1.5 | 1.2 | 1.5 | 7D | True | 2 | 0.0 | 1.3333333333333333 | False | 45.0 |
| 2026-07-01 | 1005 | SKU-ESPRESSO-500 | Espresso Beans 500g | 10 | DE_MAIN | DE | DE | 2 | nan | 3.0 | 3.0 | 30D | True | 0 | 0.6666666666666666 | 0.6666666666666666 | False | 75.0 |
| 2026-07-04 | 1005 | SKU-ESPRESSO-500 | Espresso Beans 500g | 10 | DE_MAIN | DE | DE | 4 | nan | 3.0 | 3.0 | 30D | False | 5 | 1.3333333333333333 | 3.0 | False | 0.0 |
| 2026-07-20 | 1005 | SKU-ESPRESSO-500 | Espresso Beans 500g | 10 | DE_MAIN | DE | DE | 2 | nan | 3.0 | 3.0 | 30D | True | 4 | 0.6666666666666666 | 2.0 | False | 75.0 |
| 2026-07-01 | 1006 | SKU-SLOW-MOVER | Slow Moving Accessory | 10 | DE_MAIN | DE | DE | 4 | 0.0 | 0.0 | nan | NONE | False | 0 | nan | nan | True | 0.0 |
| 2026-07-20 | 1006 | SKU-SLOW-MOVER | Slow Moving Accessory | 10 | DE_MAIN | DE | DE | 4 | 0.0 | 0.0 | nan | NONE | False | 0 | nan | nan | True | 0.0 |
| 2026-07-01 | 1007 | SKU-HYDRATION | Hydration Bottle | 10 | DE_MAIN | DE | AT,DE | 6 | 2.0 | 2.0 | 2.0 | 7D | False | 9 | 3.0 | 7.5 | False | 0.0 |
| 2026-07-04 | 1007 | SKU-HYDRATION | Hydration Bottle | 10 | DE_MAIN | DE | AT,DE | 2 | 2.0 | 2.0 | 2.0 | 7D | False | 6 | 1.0 | 4.0 | False | 0.0 |
| 2026-07-20 | 1007 | SKU-HYDRATION | Hydration Bottle | 10 | DE_MAIN | DE | AT,DE | 2 | 2.0 | 2.0 | 2.0 | 7D | False | 6 | 1.0 | 4.0 | False | 0.0 |
