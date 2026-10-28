import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf

# Configuración de la página web
st.set_page_config(
    page_title="Mini-Aladdin: Terminal en Vivo y Gestión de Cartera",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Mini-Aladdin: Terminal Financiera en Vivo (yfinance)")
st.markdown("Los precios de mercado se obtienen directamente en tiempo real desde **Yahoo Finance**. Edita tus posiciones, revisa tu ROI y analiza tus métricas actualizadas al instante.")

# ==========================================
# 1. FUNCIÓN CON CACHÉ PARA OBTENER PRECIOS EN VIVO (yfinance)
# ==========================================
@st.cache_data(ttl=300) # El caché guarda los datos por 5 minutos (300s)
def obtener_precio_mercado(ticker, asset_type):
    """
    Descarga el último precio de cierre en vivo desde Yahoo Finance.
    Soporta Acciones, ETFs y Criptomonedas (convirtiendo automáticamente a sufijo -USD).
    """
    # Ajustar ticker para criptomonedas si no incluye el par USD
    ticker_yf = ticker.strip().upper()
    if asset_type == "Crypto" and not ticker_yf.endswith("-USD"):
        ticker_yf = f"{ticker_yf}-USD"
    
    try:
        data = yf.Ticker(ticker_yf).history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        return None
    except Exception:
        return None

# ==========================================
# 2. GESTIÓN DE CAPITAL Y PORTAFOLIO EN SESSION_STATE
# ==========================================
if "portfolio" not in st.session_state:
    df_inicial = pd.DataFrame({
        "Asset": ["AAPL", "TSLA", "MSFT", "NVDA", "BTC", "ETH", "SPY", "QQQ"],
        "Type": ["Stock", "Stock", "Stock", "Stock", "Crypto", "Crypto", "ETF", "ETF"],
        "Shares": [30.0, 15.0, 20.0, 25.0, 1.2, 8.0, 15.0, 12.0],
        "Buy_Price": [150.0, 210.0, 380.0, 110.0, 50000.0, 2800.0, 450.0, 370.0],
        "Price": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] # Se poblará con yfinance
    })
    st.session_state.portfolio = df_inicial

# Panel lateral para la gestión de dinero y actualización manual
st.sidebar.header("💵 Gestión de Efectivo y Datos")
initial_cash = st.sidebar.number_input(
    "Efectivo Libre / Liquidez ($)", 
    min_value=0.0, 
    value=25000.0, 
    step=1000.0,
    format="%.2f"
)

if st.sidebar.button("🔄 Actualizar Precios en Vivo"):
    st.cache_data.clear()
    st.sidebar.success("Precios actualizados desde Yahoo Finance.")

# ==========================================
# 3. CONEXIÓN YFINANCE: ACTUALIZACIÓN AUTOMÁTICA DE PRECIOS
# ==========================================
with st.spinner("Conectando con Yahoo Finance y descargando cotizaciones en tiempo real..."):
    for idx, row in st.session_state.portfolio.iterrows():
        ticker = row["Asset"]
        asset_type = row["Type"]
        
        precio_real = obtener_precio_mercado(ticker, asset_type)
        if precio_real is not None:
            st.session_state.portfolio.loc[idx, "Price"] = precio_real
        elif row["Price"] == 0.0:
            # Respaldo si falla la conexión y no había precio previo
            st.session_state.portfolio.loc[idx, "Price"] = row["Buy_Price"]

# ==========================================
# 4. TABLA INTERACTIVA Y CÁLCULOS AUTOMÁTICOS
# ==========================================
st.subheader("📊 Tus Posiciones y Cotizaciones en Tiempo Real")
st.markdown("Puedes ajustar tus **Shares** o **Buy_Price**. La columna **Price** se sincroniza con el mercado y las métricas se autocalculan:")

edited_df = st.data_editor(
    st.session_state.portfolio, 
    num_rows="dynamic", 
    use_container_width=True,
    key="portfolio_editor",
    disabled=["Invertido", "Valor_Actual", "Ganancia_$", "ROI_%"]
)

# Cálculos automáticos de rendimiento
edited_df["Invertido"] = edited_df["Shares"] * edited_df["Buy_Price"]
edited_df["Valor_Actual"] = edited_df["Shares"] * edited_df["Price"]
edited_df["Ganancia_$"] = edited_df["Valor_Actual"] - edited_df["Invertido"]
edited_df["ROI_%"] = np.where(
    edited_df["Invertido"] > 0, 
    ((edited_df["Valor_Actual"] - edited_df["Invertido"]) / edited_df["Invertido"]) * 100, 
    0.0
)

st.session_state.portfolio = edited_df

# Totales globales de la cartera
total_invertido = edited_df["Invertido"].sum()
total_actual = edited_df["Valor_Actual"].sum()
ganancia_neta = edited_df["Ganancia_$"].sum()
roi_global = (ganancia_neta / total_invertido) * 100 if total_invertido > 0 else 0
net_worth_total = total_actual + initial_cash

# Mostrar métricas clave superiores
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
# 5. GRÁFICOS INTERACTIVOS DE PLOTLY
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
            title="Distribución por Tipo de Activo (Tiempo Real)",
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
            title="Comparativa: Invertido vs. Valor de Mercado",
            color_discrete_sequence=["#3366CC", "#109618"]
        )
        fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 6. BOTÓN DE EXPORTACIÓN A CSV
# ==========================================
st.markdown("---")
st.subheader("📥 Exportar Datos de la Cartera")

df_export = st.session_state.portfolio.copy()
csv_data = df_export.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📂 Descargar Cartera Actualizada en CSV",
    data=csv_data,
    file_name="mini_aladdin_realtime.csv",
    mime="text/csv",
    help="Haz clic para exportar las cotizaciones en tiempo real y tus resultados en formato CSV."
)

# ==========================================
# 7. INTERFAZ DE CHAT CON EL AGENTE FINANCIERO
# ==========================================
st.markdown("---")
st.subheader("💬 Asistente de Inversión y Riesgos")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Mi conexión con Yahoo Finance está activa. Tu cartera está actualizada en tiempo real. Pregúntame sobre tus posiciones, tu patrimonio o simula caídas de mercado."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("¿Qué deseas consultar sobre tu cartera en vivo?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analizando datos de la cartera..."):
            prompt_lower = prompt.lower()
            
            if "roi" in prompt_lower or "rentabilidad" in prompt_lower or "rendimiento" in prompt_lower:
                response = f"📈 Tu **Rentabilidad Global (ROI)** basada en precios de mercado reales es del **{roi_global:.2f}%**, lo que equivale a una ganancia neta de **${ganancia_neta:,.2f}**."
            elif "ganancia" in prompt_lower or "beneficio" in prompt_lower:
                response = f"💵 La ganancia neta en tiempo real es de **${ganancia_neta:,.2f}** (Valor de mercado: ${total_actual:,.2f} vs Capital invertido: ${total_invertido:,.2f})."
            elif "patrimonio" in prompt_lower or "total" in prompt_lower:
                response = f"💰 Tu patrimonio neto consolidado es de **${net_worth_total:,.2f}** (${total_actual:,.2f} en mercado + ${initial_cash:,.2f} en liquidez)."
            elif "riesgo" in prompt_lower or "var" in prompt_lower:
                var_estimated = total_actual * 0.025
                response = f"⚠️ **VaR Diario Estimado (95% confianza):** -${var_estimated:,.2f} de riesgo máximo esperado en un día para tus posiciones actuales."
            elif "simula" in prompt_lower or "caída" in prompt_lower:
                sim_loss = total_actual * 0.15
                response = f"📉 **Simulación (-15% en mercado):** Una corrección del 15% implicaría una pérdida no realizada de **${sim_loss:,.2f}** en tus activos."
            else:
                response = f"🤖 He analizado tu consulta. Con tu patrimonio actual de **${net_worth_total:,.2f}** y un ROI en tiempo real del **{roi_global:.2f}%**, ¿te gustaría revisar algún ticker en particular?"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
