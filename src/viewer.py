"""Builds a self-contained HTML viewer for the Gold table using stlite
(https://github.com/whitphx/stlite): Streamlit running entirely in the
browser via WebAssembly (Pyodide), loaded from a CDN. No server, Docker, or
Spark needed to view it, just open the HTML file in a browser."""

STLITE_VERSION = "0.85.1"

APP_CODE = """import streamlit as st
import pandas as pd

st.set_page_config(page_title="___TITLE___", layout="wide")
st.title("___TITLE___")

df = pd.read_csv("gold.csv")
df["is_oos"] = df["is_oos"].astype(str).str.lower() == "true"
df["is_overstock"] = df["is_overstock"].astype(str).str.lower() == "true"

st.caption(f"{len(df)} rows, one row per product / seller / day")

c1, c2, c3, c4 = st.columns(4)
seller = c1.multiselect("Seller", sorted(df["seller_short_name"].dropna().unique()))
sku = c2.multiselect("SKU", sorted(df["sku"].dropna().unique()))
oos = c3.radio("OOS", ["All", "OOS only", "Not OOS"], horizontal=True)
overstock = c4.radio("Overstock", ["All", "Overstock only", "Not overstock"], horizontal=True)

filtered = df.copy()
if seller:
    filtered = filtered[filtered["seller_short_name"].isin(seller)]
if sku:
    filtered = filtered[filtered["sku"].isin(sku)]
if oos == "OOS only":
    filtered = filtered[filtered["is_oos"]]
elif oos == "Not OOS":
    filtered = filtered[~filtered["is_oos"]]
if overstock == "Overstock only":
    filtered = filtered[filtered["is_overstock"]]
elif overstock == "Not overstock":
    filtered = filtered[~filtered["is_overstock"]]

st.write(f"Showing {len(filtered)} of {len(df)} rows")
st.dataframe(filtered, use_container_width=True, hide_index=True)
"""

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="UTF-8" />
<title>___TITLE___</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@___STLITE_VERSION___/build/stlite.css" />
<script type="module" src="https://cdn.jsdelivr.net/npm/@stlite/browser@___STLITE_VERSION___/build/stlite.js"></script>
</head>
<body>
<streamlit-app>
<app-file name="streamlit_app.py" entrypoint>
___APP_CODE___
</app-file>
<app-file name="gold.csv">
___CSV_DATA___
</app-file>
<app-requirements>
pandas
</app-requirements>
</streamlit-app>
</body>
</html>
"""


def build_gold_viewer_html(pdf, title: str = "Amazon Availability / OOS - Gold Table") -> str:
    app_code = APP_CODE.replace("___TITLE___", title)
    csv_data = pdf.to_csv(index=False)
    html = HTML_TEMPLATE
    html = html.replace("___APP_CODE___", app_code)
    html = html.replace("___CSV_DATA___", csv_data)
    html = html.replace("___STLITE_VERSION___", STLITE_VERSION)
    html = html.replace("___TITLE___", title)
    return html
