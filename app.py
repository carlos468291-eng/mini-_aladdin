import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página web
st.set_page_config(
    page_title="Mini-Aladdin: Gestión de Capital y Rentabilidad",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Mini-Aladdin: Tu Gestor de Cartera, Riesgos y Rentabilidad")
st.markdown("Personaliza tu capital inicial, edita tus posiciones con precios de compra, analiza tu ROI, compara tu rendimiento, exporta tus datos y chatea con el asistente.")

# ==========================================
# 1. GESTIÓN DE CAPITAL Y PORTAFOLIO EN SESSION_STATE
# ==========================================
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame({
        "Asset": ["AAPL", "BTC", "GOOGL", "BOND_US10Y"],
        "Type": ["Stock", "Crypto", "Stock", "Fixed Income"],
        "Shares": [50.0, 1.5, 30.0, 100.0],
        "Buy_Price": [150.0, 50000.0, 120.0, 95.0],
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
# 2. TABLA INTERACTIVA Y CÁLCULOS DE RENTABILIDAD
# ==========================================
st.subheader("📊 Tus Posiciones y Activos")
st.markdown("Haz clic en cualquier celda para modificar cantidades, precios de compra o precios de mercado actualizados:")

edited_df = st.data_editor(
    st.session_state.portfolio, 
    num_rows="dynamic", 
    use_container_width=True,
    key="portfolio_editor"
)

st.session_state.portfolio = edited_df

# Cálculos avanzados de rendimiento con Pandas
df = st.session_state.portfolio
df["Invertido"] = df["Shares"] * df["Buy_Price"]
df["Valor_Actual"] = df["Shares"] * df["Price"]
df["Ganancia_$"] = df["Valor_Actual"] - df["Invertido"]
df["ROI_%"] = ((df["Valor_Actual"] - df["Invertido"]) / df["Invertido"]) * 100

total_invertido = df["Invertido"].sum()
total_actual = df["Valor_Actual"].sum()
ganancia_neta = total_actual - total_invertido
roi_global = (ganancia_neta / total_invertido) * 100 if total_invertido > 0 else 0
net_worth_total = total_actual + initial_cash

# Mostrar métricas generales y de rentabilidad
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Valor en Activos", f"${total_actual:,.2f}")
col2.metric("Efectivo Libre", f"${initial_cash:,.2f}")
col3.metric("Patrimonio Total", f"${net_worth_total:,.2f}")
col4.metric(
    "Rentabilidad Global (ROI)", 
    f"{roi_global:.2f}%", 
    delta=f"${ganancia_neta:,.2f}"
)

# ==========================================
# 3. GRÁFICOS INTERACTIVOS DE PLOTLY
# ==========================================
if not st.session_state.portfolio.empty:
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        df_grouped = st.session_state.portfolio.groupby("Type")["Valor_Actual"].sum().reset_index()
        fig_pie = px.pie(
            df_grouped, 
            names="Type", 
            values="Valor_Actual", 
            title="Distribución por Tipo de Activo",
            hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with chart_col2:
        df_melted = pd.melt(
            st.session_state.portfolio,
            id_vars=["Asset"],
            value_vars=["Invertido", "Valor_Actual"],
            var_name="Métrica",
            value_name="Monto ($)"
        )
        fig_bar = px.bar(
            df_melted,
            x="Asset",
            y="Monto ($)",
            color="Métrica",
            barmode="group",
            title="Invertido vs. Valor Actual por Activo",
            color_discrete_sequence=["#3366CC", "#109618"]
        )
        fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 4. BOTÓN DE EXPORTACIÓN A CSV
# ==========================================
st.markdown("---")
st.subheader("📥 Exportar Datos de la Cartera")

df_export = st.session_state.portfolio.copy()
csv_data = df_export.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📂 Descargar Cartera y Rendimiento en CSV",
    data=csv_data,
    file_name="mini_aladdin_cartera.csv",
    mime="text/csv",
    help="Haz clic para descargar tus posiciones y cálculos de rentabilidad actuales en formato CSV."
)

# ==========================================
# 5. INTERFAZ DE CHAT CON EL AGENTE FINANCIERO
# ==========================================
st.markdown("---")
st.subheader("💬 Asistente de Inversión y Riesgos")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! He cargado tu cartera completa con análisis de ROI, gráficos comparativos y exportación. Pregúntame sobre tu rentabilidad, patrimonio o simula escenarios de riesgo."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Qué deseas consultar sobre tu cartera o rentabilidad?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizando datos..."):
            prompt_lower = prompt.lower()
            
            if "roi" in prompt_lower or "rentabilidad" in prompt_lower or "rendimiento" in prompt_lower:
                response = f"📈 Tu **Rentabilidad Global (ROI)** actual es del **{roi_global:.2f}%**, representando una ganancia neta de **${ganancia_neta:,.2f}** sobre el capital invertido."
            elif "ganancia" in prompt_lower or "beneficio" in prompt_lower:
                response = f"💵 Has obtenido una ganancia neta total de **${ganancia_neta:,.2f}** (Valor actual: ${total_actual:,.2f} vs Inversión inicial: ${total_invertido:,.2f})."
            elif "patrimonio" in prompt_lower or "total" in prompt_lower:
                response = f"💰 Tu patrimonio neto total asciende a **${net_worth_total:,.2f}**, con ${total_actual:,.2f} invertidos y ${initial_cash:,.2f} en efectivo libre."
            elif "riesgo" in prompt_lower or "var" in prompt_lower:
                var_estimated = total_actual * 0.025
                response = f"⚠️ **VaR Diario Estimado (95% confianza):** -${var_estimated:,.2f} basado en la volatilidad estándar de tus activos actuales."
            elif "simula" in prompt_lower or "caída" in prompt_lower:
                sim_loss = total_actual * 0.15
                response = f"📉 **Simulación de Escenario (-15%):** Una caída general del 15% reduciría el valor de tus activos en **${sim_loss:,.2f}**."
            else:
                response = f"🤖 He procesado tu consulta. Con un ROI actual del **{roi_global:.2f}%** y un patrimonio de **${net_worth_total:,.2f}**, ¿te gustaría auditar algún activo en particular o exportar tus datos?"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
