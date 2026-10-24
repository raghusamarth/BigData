"""Streamlit BDA dashboard: Market Overview | Stock Explorer | Big Data Analytics | Pipeline."""
import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Stock BDA Platform", layout="wide")
st.title("Stock Market Big Data Analytics (MongoDB + PySpark)")

tab1, tab2, tab3, tab4 = st.tabs(["Market Overview", "Stock Explorer", "Big Data Analytics", "Data Pipeline"])

with tab1:
    st.subheader("Top Gainers / Volatility / Sectors (live Mongo aggregations)")
    c1, c2 = st.columns(2)
    try:
        r = requests.get(f"{API}/analytics/volatility", params={"limit": 10}, timeout=10).json()
        if isinstance(r, list) and r:
            st.dataframe(pd.DataFrame(r))
            st.bar_chart(pd.DataFrame(r).set_index("symbol")["coef_var"])
        else:
            st.info(f"No data yet: {r}")
    except Exception as e:
        st.warning(f"API offline ({e}). Start: uvicorn main:app --reload")

with tab2:
    sym = st.text_input("Symbol", "RELIANCE.NS")
    if st.button("Load history"):
        try:
            r = requests.get(f"{API}/stocks/{sym}/history", params={"limit": 500}, timeout=15).json()
            df = pd.DataFrame(r.get("data", []))
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                st.line_chart(df.set_index("timestamp")["close"])
                st.dataframe(df.tail(20))
            else:
                st.info(f"No rows: {r}")
        except Exception as e:
            st.warning(str(e))

with tab3:
    st.subheader("Spark job outputs (cached in analytics_results)")
    try:
        corr = requests.get(f"{API}/analytics/correlation", timeout=10).json()
        st.json(corr)
        an = requests.get(f"{API}/analytics/anomalies", timeout=10).json()
        if isinstance(an, list) and an:
            st.dataframe(pd.DataFrame(an).head(50))
        else:
            st.info(str(an)[:500])
    except Exception as e:
        st.warning(str(e))

with tab4:
    st.subheader("Pipeline health + 5Vs evidence")
    st.code("yfinance -> ingest(clean/validate) -> MongoDB time-series -> [Mongo Agg | PySpark] -> analytics_results -> FastAPI -> Streamlit", language="text")
    try:
        s = requests.get(f"{API}/pipeline/stats", timeout=10).json()
        st.metric("Total price docs", s.get("total_price_docs", 0))
        st.metric("Symbols", s.get("symbols", 0))
        st.metric("Indicator docs", s.get("indicator_docs", 0))
        if s.get("per_symbol"):
            st.dataframe(pd.DataFrame(s["per_symbol"]))
        st.json(s.get("recent_jobs", []))
    except Exception as e:
        st.warning(str(e))
