import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página web
st.set_page_config(
    page_title="Mini-Aladdin: Gestión de Capital",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Mini-Aladdin: Tu Gestor de Cartera y Riesgos")
st.markdown("Personaliza tu capital inicial, edita tus posiciones y consulta al agente en tiempo real.")

# ==========================================
# 1. GESTIÓN DE CAPITAL Y PORTAFOLIO EN SESSION_STATE
# ==========================================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame({
        "Asset": ["AAPL", "BTC", "GOOGL", "BOND_US10Y"],
        "Type": ["Stock", "Crypto", "Stock", "Fixed Income"],
        "Shares": [50.0, 1.5, 30.0, 100.0],
        "Price": [180.50, 65000.00, 140.20, 98.50]
    })

# Panel lateral para configurar el capital base en efectivo
st.sidebar.header("💵 Gestión de Efectivo")
initial_cash = st.sidebar.number_input(
    "Efectivo Libre / Liquidez ($)", 
    min_value=0.0, 
    value=15000.0, 
    step=1000.0,
    format="%.2f"
)

# ==========================================
# 2. TABLA INTERACTIVA DE ACTIVOS (EDICIÓN DE CAPITAL)
# ==========================================
st.subheader("📊 Tus Posiciones y Activos")
st.markdown("Haz clic en cualquier celda de la tabla para **añadir filas**, **modificar nombres**, **cambiar cantidades** o actualizar precios en tiempo real:")

# st.data_editor permite editar el DataFrame directamente desde la interfaz web
edited_df = st.data_editor(
    st.session_state.portfolio, 
    num_rows="dynamic", 
    use_container_width=True,
    key="portfolio_editor"
)

# Actualizar el estado de la cartera con los cambios del usuario
st.session_state.portfolio = edited_df

# Calcular valores automáticamente
st.session_state.portfolio["Total"] = st.session_state.portfolio["Shares"] * st.session_state.portfolio["Price"]
portfolio_assets_value = st.session_state.portfolio["Total"].sum()
total_net_worth = portfolio_assets_value + initial_cash

# Mostrar métricas generales en columnas
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Valor en Activos (Invertido)", f"${portfolio_assets_value:,.2f}")
col2.metric("Efectivo Libre", f"${initial_cash:,.2f}")
col3.metric("Patrimonio Total", f"${total_net_worth:,.2f}", delta=f"{((portfolio_assets_value/total_net_worth)*100):.1f}% en activos")

# ==========================================
# 3. GRÁFICO INTERACTIVO DE PLOTLY
# ==========================================
if not st.session_state.portfolio.empty:
    st.markdown("---")
    df_grouped = st.session_state.portfolio.groupby("Type")["Total"].sum().reset_index()
    
    fig = px.pie(
        df_grouped, 
        names="Type", 
        values="Total", 
        title="Distribución del Capital por Tipo de Activo",
        hole=0.4, 
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig.update_layout(
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. INTERFAZ DE CHAT CON EL AGENTE FINANCIERO
# ==========================================
st.markdown("---")
st.subheader("💬 Asistente de Inversión y Riesgos")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! He cargado tu capital y cartera. Pregúntame sobre tu patrimonio total, calcula el VaR de tus activos actuales o simula un choque de mercado."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Qué deseas analizar con tu capital actual?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Calculando métricas con tus datos actuales..."):
            prompt_lower = prompt.lower()
            
            if "patrimonio" in prompt_lower or "total" in prompt_lower or "resumen" in prompt_lower:
                response = f"💰 Tu patrimonio neto actual es de **${total_net_worth:,.2f}**, compuesto por **${portfolio_assets_value:,.2f}** invertidos en activos y **${initial_cash:,.2f}** en efectivo libre."
            elif "riesgo" in prompt_lower or "var" in prompt_lower:
                var_estimated = portfolio_assets_value * 0.025
                response = f"⚠️ **VaR Diario Estimado (95% confianza):** -${var_estimated:,.2f}. Esta es la pérdida máxima esperada en un día normal basada en el tamaño actual de tu cartera."
            elif "simula" in prompt_lower or "caída" in prompt_lower:
                sim_loss = portfolio_assets_value * 0.15
                response = f"📉 **Simulación de Escenario (-15% en activos):** Una caída generalizada del 15% en tus posiciones reduciría el valor de tus activos en **${sim_loss:,.2f}**."
            else:
                response = f"🤖 He procesado tu consulta (*'{prompt}'*). Al tener un patrimonio total de **${total_net_worth:,.2f}**, puedo ayudarte a rebalancear tus activos o auditar tu exposición al riesgo."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
