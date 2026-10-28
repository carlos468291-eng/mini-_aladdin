%%writefile app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Mini-Aladdin Colab", page_icon="💰", layout="wide")

st.title("💰 Mini-Aladdin: Gestor de Cartera en Google Colab")

# Datos de la cartera
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame({
        "Asset": ["AAPL", "BTC", "GOOGL", "BOND_US10Y"],
        "Type": ["Stock", "Crypto", "Stock", "Fixed Income"],
        "Shares": [50.0, 1.5, 30.0, 100.0],
        "Price": [180.50, 65000.00, 140.20, 98.50]
    })

st.sidebar.header("💵 Efectivo Libre")
initial_cash = st.sidebar.number_input("Efectivo ($)", min_value=0.0, value=15000.0, step=1000.0)

st.subheader("📊 Tus Posiciones")
edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True)
st.session_state.portfolio = edited_df
st.session_state.portfolio["Total"] = st.session_state.portfolio["Shares"] * st.session_state.portfolio["Price"]

portfolio_val = st.session_state.portfolio["Total"].sum()
total_net = portfolio_val + initial_cash

col1, col2, col3 = st.columns(3)
col1.metric("Activos", f"${portfolio_val:,.2f}")
col2.metric("Efectivo", f"${initial_cash:,.2f}")
col3.metric("Patrimonio Total", f"${total_net:,.2f}")

# Gráfico Plotly
if not st.session_state.portfolio.empty:
    st.markdown("---")
    df_g = st.session_state.portfolio.groupby("Type")["Total"].sum().reset_index()
    fig = px.pie(df_g, names="Type", values="Total", title="Distribución de Capital", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)
