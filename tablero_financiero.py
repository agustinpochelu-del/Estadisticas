import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero de Análisis Integral", layout="wide")

st.title("📊 Análisis Integral de Situación Patrimonial y Resultados")
st.markdown("Esquema de 4 Pilares: Evolución Patrimonial, Liquidez, Rentabilidad y Modelo DuPont.")

# Widget para subir el archivo
archivo_subido = st.file_uploader("Subí el archivo Excel de Balances (.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # --- 1. INGESTA Y PROCESAMIENTO BASE ---
    df_historico = pd.read_excel(archivo_subido, sheet_name="Balances Historicos")
    df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
    
    # --- 2. MOTOR DE CÁLCULOS (LOS 4 PILARES) ---
    
    # PILAR 1: Patrimonio y Estructura
    activo_corriente = df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0) + df_pivot.get('Bienes de cambio', 0)
    activo_no_corriente = df_pivot.get('Bienes de Uso', 0)
    activo_total = activo_corriente + activo_no_corriente
    
    pasivo_corriente = df_pivot.get('Deudas comerciales', 0) + df_pivot.get('Otros Pasivos', 0)
    pasivo_no_corriente = df_pivot.get('Pasivo no corriente', 0)
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    
    patrimonio_neto = df_pivot.get('patrimonio neto', 0)
    
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    # PILAR 2: Liquidez y Eficiencia
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    prueba_acida = (df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0)) / pasivo_corriente.replace(0, pd.NA)
    
    # PILAR 3: Rentabilidad y Generación de Caja
    ventas = df_pivot.get('ventas', 0)
    resultado_neto = df_pivot.get('Resultado Neto', 0)
    
    # Proxy EBITDA = Resultado Neto + Amortizaciones + Intereses + Impuestos
    ebitda_proxy = resultado_neto + df_pivot.get('Amortizacion', 0) + df_pivot.get('Intereses Financieros', 0) + df_pivot.get('impuesto a las gs', 0)
    margen_ebitda = (ebitda_proxy / ventas.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100
    
    # PILAR 4: Modelo DuPont
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

    # Consolidación en DataFrame
    df_kpis = pd.DataFrame({
        'Activo Corriente': activo_corriente, 'Activo No Corriente': activo_no_corriente, 'Activo Total': activo_total,
        'Pasivo Corriente': pasivo_corriente, 'Pasivo No Corriente': pasivo_no_corriente, 'Pasivo Total': pasivo_total,
        'Patrimonio Neto': patrimonio_neto, 'Endeudamiento': endeudamiento,
        'Liquidez Corriente': liquidez_corriente, 'Prueba Acida': prueba_acida,
        'Ventas': ventas, 'Resultado Neto': resultado_neto, 'EBITDA Proxy': ebitda_proxy,
        'Margen Neto (%)': margen_neto, 'Margen EBITDA (%)': margen_ebitda,
        'ROE (%)': roe, 'Rotacion Activos': rotacion_activos, 'Multiplicador Capital': multiplicador_capital
    }).dropna().round(2)

    st.divider()
    
    # KPIs Rápidos (Cabecera)
    años_disponibles = df_kpis.index.sort_values(ascending=False).tolist()
    año_seleccionado = st.selectbox("Seleccionar Año Base (Foto de cierre):", años_disponibles)
    datos_año = df_kpis.loc[año_seleccionado]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']}")
    col2.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']}")
    col3.metric("Margen EBITDA", f"{datos_año['Margen EBITDA (%)']}%")
    col4.metric("ROE (DuPont)", f"{datos_año['ROE (%)']}%")
    
    st.divider()
    
    # --- 3. ESQUEMA DE PESTAÑAS (LOS 4 PILARES) ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Estructura Patrimonial", 
        "2️⃣ Liquidez y Eficiencia", 
        "3️⃣ Rentabilidad Económica", 
        "4️⃣ Modelo DuPont (ROE)"
    ])
    
    # --- PILAR 1 ---
    with tab1:
        st.subheader("Análisis Vertical: Composición del Fondeo e Inversión")
        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            fig_pas = go.Figure()
            fig_pas.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Pasivo Corriente'], name='Pasivo Corto Plazo', marker_color='#ff7f0e'))
            fig_pas.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Pasivo No Corriente'], name='Pasivo Largo Plazo', marker_color='#d62728'))
            fig_pas.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Patrimonio Neto'], name='Patrimonio Neto', marker_color='#1f77b4'))
            fig_pas.update_layout(title="Estructura de Financiamiento", barmode='stack', hovermode="x unified")
            st.plotly_chart(fig_pas, use_container_width=True)
            
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c'))
            fig_act.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Activo No Corriente'], name='Activo No Corriente (Bienes Uso)', marker_color='#8c564b'))
            fig_act.update_layout(title="Estructura de Inversión (Activos)", barmode='stack', hovermode="x unified")
            st.plotly_chart(fig_act, use_container_width=True)

    # --- PILAR 2 ---
    with tab2:
        st.subheader("Capacidad de Respuesta a Corto Plazo")
        fig_liq = go.Figure()
        fig_liq.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf')))
        fig_liq.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot')))
        fig_liq.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Límite Riesgo (1.0)")
        fig_liq.update_layout(title="Evolución de Liquidez vs Prueba Ácida", hovermode="x unified")
        st.plotly_chart(fig_liq, use_container_width=True)

    # --- PILAR 3 ---
    with tab3:
        st.subheader("Generación de Valor y Caja Operativa")
        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['EBITDA Proxy'], name='Caja Operativa (EBITDA Proxy)', marker_color='#bcbd22', yaxis='y'))
        fig_rent.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Resultado Neto'], name='Resultado Neto', marker_color='#2ca02c', yaxis='y'))
        fig_rent.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['Margen EBITDA (%)'], mode='lines+markers', name='Margen EBITDA (%)', yaxis='y2', line=dict(color='black', width=2)))
        
        fig_rent.update_layout(
            title="EBITDA vs Resultado Neto Real",
            yaxis=dict(title="Pesos Ajustados"),
            yaxis2=dict(title="Margen (%)", overlaying='y', side='right', showgrid=False),
            barmode='group', hovermode="x unified"
        )
        st.plotly_chart(fig_rent, use_container_width=True)

    # --- PILAR 4 ---
    with tab4:
        st.subheader("Descomposición del ROE (Análisis DuPont)")
        st.markdown("¿De dónde viene la rentabilidad para el accionista? **ROE = Margen Neto x Rotación de Activos x Multiplicador de Capital**")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric("Margen Neto (Eficiencia)", f"{datos_año['Margen Neto (%)']}%")
        col_d2.metric("Rotación de Activos (Volumen)", f"{datos_año['Rotacion Activos']}x")
        col_d3.metric("Apalancamiento (Fondeo)", f"{datos_año['Multiplicador Capital']}x")
        
        fig_dupont = go.Figure()
        fig_dupont.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['ROE (%)'], mode='lines+markers', name='ROE (%)', line=dict(color='#e377c2', width=4)))
        fig_dupont.update_layout(title="Evolución Histórica del ROE", yaxis_title="Porcentaje (%)", hovermode="x unified")
        st.plotly_chart(fig_dupont, use_container_width=True)

else:
    st.info("👆 Por favor, subí el archivo Excel (.xlsx) para comenzar el análisis.")
