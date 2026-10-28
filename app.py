import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Mini-Aladdin: Terminal Financiera y Gestión de Riesgos",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Mini-Aladdin: Terminal Financiera Avanzada")
st.markdown("Terminal integral con cotizaciones en vivo vía **Yahoo Finance**, autocalculo de métricas, análisis técnico (Bollinger & RSI) y optimización de portafolios (Markowitz).")

# ==========================================
# 1. FUNCIONES AUXILIARES YFINANCE & MARKOWITZ
# ==========================================
@st.cache_data(ttl=300)
def obtener_precio_actual(ticker, asset_type):
    """Descarga el último precio de mercado en vivo."""
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

@st.cache_data(ttl=3600)
def obtener_historico_individual(ticker, asset_type, periodo="1y"):
    """Descarga el historial de precios para un activo individual."""
    ticker_yf = ticker.strip().upper()
    if asset_type == "Crypto" and not ticker_yf.endswith("-USD"):
        ticker_yf = f"{ticker_yf}-USD"
    try:
        return yf.Ticker(ticker_yf).history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def obtener_historicos_multiples(tickers, types, periodo="1y"):
    """Descarga precios de cierre combinados para análisis de portafolio."""
    data = {}
    for ticker, t_type in zip(tickers, types):
        t_yf = ticker.strip().upper()
        if t_type == "Crypto" and not t_yf.endswith("-USD"):
            t_yf = f"{t_yf}-USD"
        try:
            df = yf.Ticker(t_yf).history(period=period)
            if not df.empty:
                data[ticker] = df["Close"]
        except Exception:
            pass
    return pd.DataFrame(data).dropna()

def calcular_frontera_eficiente(df_precios):
    """Ejecuta una simulación de Monte Carlo para la Frontera Eficiente de Markowitz."""
    returns = np.log(df_precios / df_precios.shift(1)).dropna()
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    
    num_assets = len(df_precios.columns)
    num_portfolios = 5000
    
    results = np.zeros((3 + num_assets, num_portfolios))
    
    np.random.seed(42)
    for i in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        
        p_return = np.sum(weights * mean_returns)
        p_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        results[0, i] = p_return
        results[1, i] = p_volatility
        results[2, i] = p_return / p_volatility if p_volatility > 0 else 0
        
        for j in range(num_assets):
            results[3 + j, i] = weights[j]
            
    columns = ['Return', 'Volatility', 'Sharpe'] + list(df_precios.columns)
    df_results = pd.DataFrame(results.T, columns=columns)
    
    max_sharpe_idx = df_results['Sharpe'].idxmax()
    optimal_portfolio = df_results.iloc[max_sharpe_idx]
    
    return df_results, optimal_portfolio

# ==========================================
# 2. ESTADO DE LA SESIÓN (SESSION_STATE)
# ==========================================
if "portfolio" not in st.session_state:
    df_inicial = pd.DataFrame({
        "Asset": ["AAPL", "TSLA", "MSFT", "NVDA", "BTC", "ETH", "SPY", "QQQ"],
        "Type": ["Stock", "Stock", "Stock", "Stock", "Crypto", "Crypto", "ETF", "ETF"],
        "Shares": [30.0, 15.0, 20.0, 25.0, 1.2, 8.0, 15.0, 12.0],
        "Buy_Price": [150.0, 210.0, 380.0, 110.0, 50000.0, 2800.0, 450.0, 370.0],
        "Price": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    })
    st.session_state.portfolio = df_inicial

# Panel lateral
st.sidebar.header("💵 Configuración General")
initial_cash = st.sidebar.number_input(
    "Efectivo Libre / Liquidez ($)", 
    min_value=0.0, 
    value=25000.0, 
    step=1000.0,
    format="%.2f"
)

if st.sidebar.button("🔄 Actualizar Precios de Mercado"):
    st.cache_data.clear()
    st.sidebar.success("¡Caché limpiada y precios actualizados desde Yahoo Finance!")

# Sincronización automática de precios de mercado
with st.spinner("Sincronizando cotizaciones en vivo con Yahoo Finance..."):
    for idx, row in st.session_state.portfolio.iterrows():
        p_real = obtener_precio_actual(row["Asset"], row["Type"])
        if p_real:
            st.session_state.portfolio.loc[idx, "Price"] = p_real
        elif row["Price"] == 0.0:
            st.session_state.portfolio.loc[idx, "Price"] = row["Buy_Price"]

# ==========================================
# 3. ESTRUCTURA DE PESTAÑAS (TABS)
# ==========================================
tab_cartera, tab_tecnico, tab_markowitz = st.tabs([
    "💼 Cartera y Métricas", 
    "📈 Análisis Técnico (Bollinger & RSI)", 
    "🎯 Frontera Eficiente (Markowitz)"
])

# ------------------------------------------
# PESTAÑA 1: CARTERA, MÉTRICAS Y CHAT
# ------------------------------------------
with tab_cartera:
    st.subheader("📊 Tus Posiciones y Cotizaciones en Vivo")
    st.markdown("Ajusta **Shares** o **Buy_Price**. Las ganancias, el ROI y el valor actual se autocompletan al instante:")

    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor",
        disabled=["Invertido", "Valor_Actual", "Ganancia_$", "ROI_%"]
    )

    # Autocalculo cuantitativo
    edited_df["Invertido"] = edited_df["Shares"] * edited_df["Buy_Price"]
    edited_df["Valor_Actual"] = edited_df["Shares"] * edited_df["Price"]
    edited_df["Ganancia_$"] = edited_df["Valor_Actual"] - edited_df["Invertido"]
    edited_df["ROI_%"] = np.where(
        edited_df["Invertido"] > 0, 
        ((edited_df["Valor_Actual"] - edited_df["Invertido"]) / edited_df["Invertido"]) * 100, 
        0.0
    )
    st.session_state.portfolio = edited_df

    total_invertido = edited_df["Invertido"].sum()
    total_actual = edited_df["Valor_Actual"].sum()
    ganancia_neta = edited_df["Ganancia_$"].sum()
    roi_global = (ganancia_neta / total_invertido) * 100 if total_invertido > 0 else 0
    net_worth_total = total_actual + initial_cash

    # Panel superior de métricas
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

    # Visualizaciones
    if not st.session_state.portfolio.empty:
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            df_grouped = st.session_state.portfolio.groupby("Type")["Valor_Actual"].sum().reset_index()
            fig_pie = px.pie(
                df_grouped, names="Type", values="Valor_Actual", 
                title="Distribución por Tipo de Activo", hole=0.4, 
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            df_melted = pd.melt(
                st.session_state.portfolio, id_vars=["Asset"],
                value_vars=["Invertido", "Valor_Actual"],
                var_name="Métrica", value_name="Monto ($)"
            )
            fig_bar = px.bar(
                df_melted, x="Asset", y="Monto ($)", color="Métrica", barmode="group",
                title="Capital Invertido vs. Valor de Mercado",
                color_discrete_sequence=["#3366CC", "#109618"]
            )
            fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_bar, use_container_width=True)

    # Exportación
    st.markdown("---")
    st.subheader("📥 Exportar Datos")
    csv_data = st.session_state.portfolio.copy().to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📂 Descargar Cartera en CSV",
        data=csv_data,
        file_name="mini_aladdin_cartera.csv",
        mime="text/csv"
    )

    # Asistente Virtual
    st.markdown("---")
    st.subheader("💬 Asistente de Inversión y Riesgos")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "¡Hola! Mi conexión con Yahoo Finance está lista. Pregúntame sobre tu rentabilidad, patrimonio o simula escenarios de riesgo."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("¿Qué deseas consultar sobre tu cartera?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando información..."):
                p_lower = prompt.lower()
                if "roi" in p_lower or "rentabilidad" in p_lower:
                    response = f"📈 Tu **ROI global** es del **{roi_global:.2f}%** (Ganancia neta acumulada: **${ganancia_neta:,.2f}**)."
                elif "patrimonio" in p_lower or "total" in p_lower:
                    response = f"💰 Tu patrimonio neto total asciende a **${net_worth_total:,.2f}**."
                elif "riesgo" in p_lower or "var" in p_lower:
                    response = f"⚠️ **VaR Diario Estimado (95% confianza):** -${total_actual * 0.025:,.2f}."
                elif "simula" in p_lower or "caída" in p_lower:
                    response = f"📉 Una corrección del 15% implicaría una pérdida no realizada de **${total_actual * 0.15:,.2f}**."
                else:
                    response = f"🤖 Con un patrimonio de **${net_worth_total:,.2f}** y un ROI del **{roi_global:.2f}%**, ¿te gustaría auditar algún activo en particular o ver la frontera eficiente?"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ------------------------------------------
# PESTAÑA 2: ANÁLISIS TÉCNICO (BOLLINGER & RSI)
# ------------------------------------------
with tab_tecnico:
    st.subheader("📈 Bandas de Bollinger e Índice RSI")
    st.markdown("Selecciona un activo para evaluar zonas de sobrecompra o sobreventa en base a volatilidad e impulso:")

    lista_activos = st.session_state.portfolio["Asset"].tolist()
    if lista_activos:
        sel_asset = st.selectbox("Seleccionar Activo:", lista_activos, key="sel_tech_asset")
        sel_period = st.select_slider("Temporalidad:", options=["1mo", "3mo", "6mo", "1y", "2y", "max"], value="1y", key="sel_tech_period")
        
        tipo_act = st.session_state.portfolio.loc[st.session_state.portfolio["Asset"] == sel_asset, "Type"].values[0]
        
        with st.spinner(f"Calculando indicadores técnicos para {sel_asset}..."):
            df_h = obtener_historico_individual(sel_asset, tipo_act, sel_period)
            
        if not df_h.empty and len(df_h) >= 20:
            # Bandas de Bollinger (20, 2)
            window = 20
            df_h['SMA'] = df_h['Close'].rolling(window=window).mean()
            df_h['STD'] = df_h['Close'].rolling(window=window).std()
            df_h['Upper'] = df_h['SMA'] + (df_h['STD'] * 2)
            df_h['Lower'] = df_h['SMA'] - (df_h['STD'] * 2)
            
            # RSI (14)
            delta = df_h['Close'].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_g = gain.ewm(alpha=1/14, min_periods=14).mean()
            avg_l = loss.ewm(alpha=1/14, min_periods=14).mean()
            rs = avg_g / avg_l
            df_h['RSI'] = 100 - (100 / (1 + rs))
            
            # Gráfico Bollinger
            fig_boll = go.Figure()
            fig_boll.add_trace(go.Scatter(x=df_h.index, y=df_h['Upper'], name='Banda Superior', line=dict(color='rgba(250,0,0,0.4)', dash='dash')))
            fig_boll.add_trace(go.Scatter(x=df_h.index, y=df_h['Lower'], name='Banda Inferior', line=dict(color='rgba(0,150,0,0.4)', dash='dash'), fill='tonexty', fillcolor='rgba(200,200,200,0.15)'))
            fig_boll.add_trace(go.Scatter(x=df_h.index, y=df_h['SMA'], name='SMA 20', line=dict(color='orange', width=1)))
            fig_boll.add_trace(go.Scatter(x=df_h.index, y=df_h['Close'], name='Precio Cierre', line=dict(color='#1a73e8', width=2)))
            fig_boll.update_layout(title=f"Bandas de Bollinger - {sel_asset}", xaxis_title="Fecha", yaxis_title="Precio ($)", hovermode="x unified", margin=dict(t=40, b=10, l=10, r=10))
            
            # Gráfico RSI
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df_h.index, y=df_h['RSI'], name='RSI (14)', line=dict(color='#9467bd', width=1.5)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecompra (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobreventa (30)")
            fig_rsi.update_layout(title=f"Índice de Fuerza Relativa (RSI) - {sel_asset}", xaxis_title="Fecha", yaxis_title="RSI", yaxis=dict(range=[0, 100]), hovermode="x unified", margin=dict(t=40, b=10, l=10, r=10))
            
            st.plotly_chart(fig_boll, use_container_width=True)
            st.plotly_chart(fig_rsi, use_container_width=True)
        else:
            st.warning("Se necesitan al menos 20 registros históricos para calcular los indicadores.")
    else:
        st.info("Añade activos a tu cartera para analizar su comportamiento técnico.")

# ------------------------------------------
# PESTAÑA 3: OPTIMIZACIÓN DE MARKOWITZ
# ------------------------------------------
with tab_markowitz:
    st.subheader("🎯 Optimización de Portafolio por Markowitz")
    st.markdown("Simulación de Monte Carlo con 5,000 combinaciones para calcular el **Portafolio Óptimo (Máximo Ratio de Sharpe)**:")

    tickers_port = st.session_state.portfolio["Asset"].tolist()
    types_port = st.session_state.portfolio["Type"].tolist()

    if len(tickers_port) >= 2:
        with st.spinner("Procesando simulaciones de Monte Carlo y covarianza..."):
            df_hist_prices = obtener_historicos_multiples(tickers_port, types_port, periodo="1y")
            
        if not df_hist_prices.empty and len(df_hist_prices.columns) >= 2:
            df_simulaciones, port_optimo = calcular_frontera_eficiente(df_hist_prices)
            
            # Gráfico Scatter
            fig_front = px.scatter(
                df_simulaciones,
                x="Volatility",
                y="Return",
                color="Sharpe",
                color_continuous_scale="Viridis",
                title="Frontera Eficiente (Relación Riesgo/Rendimiento)",
                labels={"Volatility": "Volatilidad Anualizada (Riesgo)", "Return": "Retorno Esperado Anual", "Sharpe": "Ratio de Sharpe"}
            )
            
            # Estrella del Portafolio Óptimo
            fig_front.add_trace(go.Scatter(
                x=[port_optimo["Volatility"]],
                y=[port_optimo["Return"]],
                mode="markers",
                marker=dict(color="red", size=15, symbol="star"),
                name="Portafolio Óptimo (Máx. Sharpe)"
            ))
            
            fig_front.update_layout(margin=dict(t=40, b=10, l=10, r=10), hovermode="closest")
            st.plotly_chart(fig_front, use_container_width=True)
            
            # Mostrar tabla de pesos óptimos
            st.markdown("### 🏆 Distribución Recomendada de Pesos (Máxima Eficiencia)")
            pesos_activos = port_optimo[df_hist_prices.columns] * 100
            df_pesos = pd.DataFrame({"Activo": df_hist_prices.columns, "Peso Óptimo (%)": pesos_activos.values})
            df_pesos["Peso Óptimo (%)"] = df_pesos["Peso Óptimo (%)"].map("{:.2f}%".format)
            st.dataframe(df_pesos, use_container_width=True)
        else:
            st.warning("Se necesitan al menos 2 activos válidos con datos en Yahoo Finance para la optimización de Markowitz.")
    else:
        st.info("Añade al menos 2 activos en la pestaña de cartera para habilitar la optimización.")
