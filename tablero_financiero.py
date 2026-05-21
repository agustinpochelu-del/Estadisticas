import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Tablero Financiero y Patrimonial", layout="wide")

st.title("📊 Análisis de Situación Patrimonial y Resultados")
st.markdown("Cargá la base de datos histórica para visualizar la evolución del negocio.")

# Widget para subir el archivo
archivo_subido = st.file_uploader("Subí el archivo 'Balances Historicos.csv'", type=["csv"])

if archivo_subido is not None:
    # 1. Ingesta y limpieza de datos
    df_historico = pd.read_csv(archivo_subido)
    
    # Pivotear los datos para tener los años en filas y las cuentas en columnas usando 'Saldos Ajustados'
    df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
    
    # 2. Motor de cálculo de ratios financieros
    # Liquidez
    activo_corriente = df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0) + df_pivot.get('Bienes de cambio', 0)
    pasivo_corriente = df_pivot.get('Deudas comerciales', 0) + df_pivot.get('Otros Pasivos', 0)
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    
    # Endeudamiento y Solidez
    pasivo_total = pasivo_corriente + df_pivot.get('Pasivo no corriente', 0)
    patrimonio_neto = df_pivot.get('patrimonio neto', 0)
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    # Rentabilidad
    resultado_neto = df_pivot.get('Resultado Neto', 0)
    ventas = df_pivot.get('ventas', 0)
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100

    # Armar un dataframe consolidado con los KPIs
    df_kpis = pd.DataFrame({
        'Liquidez Corriente': liquidez_corriente,
        'Endeudamiento': endeudamiento,
        'ROE (%)': roe,
        'Margen Neto (%)': margen_neto
    }).dropna().round(2)

    # 3. Interfaz Visual del Tablero
    st.divider()
    
    # Selector de año para ver la foto de un periodo específico
    años_disponibles = df_kpis.index.sort_values(ascending=False).tolist()
    año_seleccionado = st.selectbox("Seleccionar Año de Análisis:", años_disponibles)
    
    # Tarjetas de resumen (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    
    datos_año = df_kpis.loc[año_seleccionado]
    
    col1.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']}")
    col2.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']}")
    col3.metric("ROE (Rentabilidad sobre PN)", f"{datos_año['ROE (%)']}%")
    col4.metric("Margen Neto", f"{datos_año['Margen Neto (%)']}%")
    
    st.divider()
    
    # Gráficos Interactivos con Plotly
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("📈 Evolución de Liquidez y Endeudamiento")
        fig_solidez = go.Figure()
        fig_solidez.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(color='#1f77b4', width=3)))
        fig_solidez.add_trace(go.Scatter(x=df_kpis.index, y=df_kpis['Endeudamiento'], mode='lines+markers', name='Endeudamiento', line=dict(color='#d62728', width=3)))
        fig_solidez.update_layout(xaxis_title="Año", yaxis_title="Índice", hovermode="x unified")
        st.plotly_chart(fig_solidez, use_container_width=True)
        
    with col_graf2:
        st.subheader("💰 Evolución de la Rentabilidad (ROE y Margen)")
        fig_rentabilidad = go.Figure()
        fig_rentabilidad.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['ROE (%)'], name='ROE (%)', marker_color='#2ca02c'))
        fig_rentabilidad.add_trace(go.Bar(x=df_kpis.index, y=df_kpis['Margen Neto (%)'], name='Margen Neto (%)', marker_color='#ff7f0e'))
        fig_rentabilidad.update_layout(xaxis_title="Año", yaxis_title="Porcentaje (%)", barmode='group', hovermode="x unified")
        st.plotly_chart(fig_rentabilidad, use_container_width=True)
        
else:
    st.info("👆 Por favor, subí el archivo CSV para comenzar el análisis.")