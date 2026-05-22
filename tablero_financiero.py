import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero de Análisis Integral", layout="wide")

# --- FUNCIÓN DE PANTALLA COMPLETA (POP-UP) ---
@st.dialog("🔍 Vista Ampliada del Análisis", width="large")
def mostrar_grafico_ampliado(figura):
    # Clonamos el gráfico y le damos altura extra para la vista XL
    fig_xl = go.Figure(figura)
    fig_xl.update_layout(height=650)
    st.plotly_chart(fig_xl, use_container_width=True)

# Encabezado
st.title("📊 Análisis Integral de Situación Patrimonial y Resultados")
st.markdown("Esquema de Análisis Completo y Automatizado para la Toma de Decisiones.")

# Widget para subir el archivo
archivo_subido = st.file_uploader("Subí el archivo Excel de Balances (.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # --- 1. INGESTA Y PROCESAMIENTO BASE ---
    df_historico = pd.read_excel(archivo_subido, sheet_name="Balances Historicos")
    df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
    
    # --- 2. MOTOR DE CÁLCULOS ---
    # PILAR 1: Patrimonio y Estructura
    activo_corriente = df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0) + df_pivot.get('Bienes de cambio', 0)
    activo_no_corriente = df_pivot.get('Bienes de Uso', 0)
    activo_total = activo_corriente + activo_no_corriente
    
    pasivo_corriente = df_pivot.get('Deudas comerciales', 0) + df_pivot.get('Otros Pasivos', 0)
    pasivo_no_corriente = df_pivot.get('Pasivo no corriente', 0)
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    
    patrimonio_neto = df_pivot.get('patrimonio neto', 0)
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    # PILAR 2: Liquidez
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    prueba_acida = (df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0)) / pasivo_corriente.replace(0, pd.NA)
    capital_trabajo = activo_corriente - pasivo_corriente
    
    # PILAR 3: Rentabilidad y Caja Operativa
    ventas = df_pivot.get('ventas', 0)
    resultado_neto = df_pivot.get('Resultado Neto', 0)
    ebitda_proxy = resultado_neto + df_pivot.get('Amortizacion', 0) + df_pivot.get('Intereses Financieros', 0) + df_pivot.get('impuesto a las gs', 0)
    margen_ebitda = (ebitda_proxy / ventas.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100
    
    # PILAR 4: Modelo DuPont
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

    # Consolidación en DataFrame (Expresando valores monetarios en Millones para mejor visualización)
    df_kpis = pd.DataFrame({
        'Activo Corriente': activo_corriente / 1e6, 
        'Activo No Corriente': activo_no_corriente / 1e6, 
        'Activo Total': activo_total / 1e6,
        'Pasivo Corriente': pasivo_corriente / 1e6, 
        'Pasivo No Corriente': pasivo_no_corriente / 1e6, 
        'Pasivo Total': pasivo_total / 1e6,
        'Patrimonio Neto': patrimonio_neto / 1e6, 
        'Endeudamiento': endeudamiento,
        'Liquidez Corriente': liquidez_corriente, 
        'Prueba Acida': prueba_acida, 
        'Capital de Trabajo': capital_trabajo / 1e6,
        'Ventas': ventas / 1e6, 
        'Resultado Neto': resultado_neto / 1e6, 
        'EBITDA Proxy': ebitda_proxy / 1e6,
        'Margen Neto (%)': margen_neto, 
        'Margen EBITDA (%)': margen_ebitda,
        'ROE (%)': roe, 
        'Rotacion Activos': rotacion_activos, 
        'Multiplicador Capital': multiplicador_capital
    }).dropna().round(2)

    # --- CONTROLES EN LA BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("🔍 Filtros del Tablero")
    
    # Filtro de rango de años
    lista_años = sorted(df_kpis.index.tolist())
    rango_años = st.sidebar.slider(
        "Seleccionar Período de Análisis:",
        min_value=int(min(lista_años)),
        max_value=int(max(lista_años)),
        value=(int(min(lista_años)), int(max(lista_años)))
    )
    
    df_filtrado = df_kpis.loc[rango_años[0]:rango_años[1]]
    
    # Selector de año puntual
    años_disponibles = df_filtrado.index.sort_values(ascending=False).tolist()
    año_seleccionado = st.sidebar.selectbox("📅 Ejercicio para análisis puntual:", años_disponibles)
    datos_año = df_filtrado.loc[año_seleccionado]
    
    st.divider()
    
    # --- 3. ESTRUCTURA DE SOLAPAS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏛️ Estructura Patrimonial", 
        "💧 Liquidez y Corto Plazo", 
        "📈 Rentabilidad Económica", 
        "🎯 Análisis DuPont (ROE)"
    ])
    
    # --- SOLAPA 1: PATRIMONIO ---
    with tab1:
        st.subheader(f"Análisis Patrimonial - Ejercicio {año_seleccionado}")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M")
        col_m2.metric("Pasivo Total (Fondeo Terceros)", f"$ {datos_año['Pasivo Total']:,.2f} M")
        col_m3.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}")
        
        st.write("")
        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            fig_pas = go.Figure()
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo Corriente'], name='Pasivo Corto Plazo', marker_color='#ff7f0e'))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo No Corriente'], name='Pasivo Largo Plazo', marker_color='#d62728'))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Patrimonio Neto'], name='Patrimonio Neto', marker_color='#1f77b4'))
            fig_pas.update_layout(title="Evolución del Fondeo Histórico (Pasivo + PN)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450)
            st.plotly_chart(fig_pas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Fondeo", key="btn_pas", use_container_width=True):
                mostrar_grafico_ampliado(fig_pas)
            
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c'))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente (Bienes Uso)', marker_color='#8c564b'))
            fig_act.update_layout(title="Evolución de la Inversión Histórica (Activos)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450)
            st.plotly_chart(fig_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Inversión", key="btn_act", use_container_width=True):
                mostrar_grafico_ampliado(fig_act)
            
        st.info("""
        **💡 Guía de interpretación:**
        - **Índice de Endeudamiento (Pasivo / PN):** Mide cuántos pesos de deuda tiene la empresa por cada peso de capital propio aportado por los socios. 
        - **Estructura de Bloques:** El gráfico de Fondeo debe coordinar con el de Inversión. Idealmente, los activos a largo plazo (Bienes de Uso) deben financiarse con patrimonio neto o pasivos a largo plazo para no asfixiar la caja operativa.
        """)

    # --- SOLAPA 2: LIQUIDEZ ---
    with tab2:
        st.subheader(f"Situación de Corto Plazo - Ejercicio {año_seleccionado}")
        
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}")
        col_m5.metric("Prueba Ácida (Líquida)", f"{datos_año['Prueba Acida']:.2f}")
        col_m6.metric("Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M")
        
        st.write("")
        fig_liq = go.Figure()
        fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf')))
        fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot')))
        fig_liq.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Límite Técnico (1.0)")
        fig_liq.update_layout(title="Evolución Histórica de los Índices de Liquidez", yaxis_title="Índice", hovermode="x unified", height=500)
        st.plotly_chart(fig_liq, use_container_width=True)
        if st.button("🔍 Ampliar Gráfico de Liquidez", key="btn_liq", use_container_width=True):
            mostrar_grafico_ampliado(fig_liq)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **Liquidez Corriente (Activo Corriente / Pasivo Corriente):** Indica cuántos pesos en bienes líquidos o de rápido vencimiento tiene la empresa para cubrir cada peso de deuda que vence dentro del año.
        - **Prueba Ácida:** Es un filtro más exigente que resta los inventarios (Bienes de cambio), evaluando si la empresa puede responder a sus deudas inmediatas utilizando únicamente caja y cuentas a cobrar rápidas.
        """)

    # --- SOLAPA 3: RENTABILIDAD ---
    with tab3:
        st.subheader(f"Rendimiento Económico - Ejercicio {año_seleccionado}")
        
        col_m7, col_m8, col_m9 = st.columns(3)
        col_m7.metric("Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M")
        col_m8.metric("Margen EBITDA", f"{datos_año['Margen EBITDA (%)']:.2f}%")
        col_m9.metric("Margen Neto Final", f"{datos_año['Margen Neto (%)']:.2f}%")
        
        st.write("")
        col_t3a, col_t3b = st.columns(2)
        
        with col_t3a:
            st.markdown("##### 🛒 Volumen de Ventas vs Eficiencia (ROS)")
            fig_ventas = go.Figure()
            fig_ventas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Ventas'], name='Ventas Netas', marker_color='#17becf', yaxis='y'))
            fig_ventas.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%)', yaxis='y2', line=dict(color='#ff7f0e', width=3)))
            fig_ventas.update_layout(
                title="Evolución de Ventas vs Margen Neto Final",
                yaxis=dict(title="Millones de Pesos"),
                yaxis2=dict(title="Margen Neto (%)", overlaying='y', side='right', showgrid=False),
                barmode='group', hovermode="x unified", height=450
            )
            st.plotly_chart(fig_ventas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Ventas", key="btn_ventas", use_container_width=True):
                mostrar_grafico_ampliado(fig_ventas)
            
        with col_t3b:
            st.markdown("##### 💰 Generación de Caja Operativa")
            fig_rent = go.Figure()
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='Caja Operativa (EBITDA)', marker_color='#bcbd22', yaxis='y'))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto Final', marker_color='#2ca02c', yaxis='y'))
            fig_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen EBITDA (%)'], mode='lines+markers', name='Margen EBITDA (%)', yaxis='y2', line=dict(color='black', width=2)))
            fig_rent.update_layout(
                title="EBITDA vs Resultado Neto Real",
                yaxis=dict(title="Millones de Pesos"),
                yaxis2=dict(title="Margen EBITDA (%)", overlaying='y', side='right', showgrid=False),
                barmode='group', hovermode="x unified", height=450
            )
            st.plotly_chart(fig_rent, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Caja", key="btn_caja", use_container_width=True):
                mostrar_grafico_ampliado(fig_rent)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **Ventas vs. Margen Neto (ROS):** Permite evaluar si el crecimiento en el volumen de actividad se traduce en una mayor eficiencia final.
        - **Caja Operativa (EBITDA Proxy):** Muestra el verdadero potencial del negocio para generar fondos, aislando amortizaciones e impuestos.
        """)

    # --- SOLAPA 4: DUPONT ---
    with tab4:
        st.subheader(f"Descomposición del ROE (Esquema DuPont) - Ejercicio {año_seleccionado}")
        
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        col_d1.metric("Margen Neto (Eficiencia)", f"{datos_año['Margen Neto (%)']:.2f}%")
        col_d2.metric("Rotación Activos (Eficacia)", f"{datos_año['Rotacion Activos']:.2f}x")
        col_d3.metric("Multiplicador (Apalancamiento)", f"{datos_año['Multiplicador Capital']:.2f}x")
        col_d4.metric("ROE Final (Rendimiento PN)", f"{datos_año['ROE (%)']:.2f}%")
        
        st.write("")
        fig_dupont = go.Figure()
        fig_dupont.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], mode='lines+markers', name='ROE (%) Histórico', line=dict(color='#e377c2', width=4)))
        fig_dupont.update_layout(title="Evolución de la Rentabilidad del Capital Propio (ROE)", yaxis_title="Porcentaje (%)", hovermode="x unified", height=500)
        st.plotly_chart(fig_dupont, use_container_width=True)
        if st.button("🔍 Ampliar Gráfico DuPont", key="btn_dupont", use_container_width=True):
            mostrar_grafico_ampliado(fig_dupont)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **El Modelo DuPont** desarma el ROE para revelar la verdadera palanca del negocio multiplicando tres frentes: Rentabilidad (Margen), Eficiencia (Rotación de Activos) y Fondeo (Apalancamiento).
        """)

else:
    st.info("👆 Por favor, subí el archivo Excel (.xlsx) para comenzar el análisis.")
