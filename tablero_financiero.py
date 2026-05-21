import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Tablero Financiero y Patrimonial", layout="wide")

st.title("📊 Análisis de Situación Patrimonial y Resultados")
st.markdown("Cargá la base de datos histórica para visualizar la evolución del negocio.")

# Widget para subir el archivo (acepta xlsx)
archivo_subido = st.file_uploader("Subí el archivo Excel de Balances (.xlsx)", type=["xlsx"])

if archivo_subido is not None:
    # 1. Ingesta de datos
    df_historico = pd.read_excel(archivo_subido, sheet_name="Balances Historicos")
    
    # Pivotear los datos para tener los años en filas y las cuentas en columnas
    df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
    
    # 2. Motor de cálculo de ratios financieros
    # Liquidez
    activo_corriente = df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0) + df_pivot.get('Bienes de cambio', 0)
    pasivo_corriente = df_pivot.get('Deudas comerciales', 0) + df_pivot.get('Otros Pasivos', 0)
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    
    # Estructura Patrimonial (Activo, Pasivo y PN Totales)
    activo_no_corriente = df_pivot.get('Bienes de Uso', 0)
    activo_total = activo_corriente + activo_no_corriente
    
    pasivo_no_corriente = df_pivot.get('Pasivo no corriente', 0)
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    
    patrimonio_neto = df_pivot.get('patrimonio neto', 0)
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    # Rentabilidad y Ventas
    resultado_neto = df_pivot.get('Resultado Neto', 0)
    ventas = df_pivot.get('ventas', 0)
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100

    # Armar un dataframe consolidado con todos los KPIs
    df_kpis = pd.DataFrame({
        'Liquidez Corriente': liquidez_corriente,
        'Endeudamiento': endeudamiento,
        'ROE (%)': roe,
        'Margen Neto (%)': margen_neto,
        'Activo Total': activo_total,
        'Pasivo Total': pasivo_total,
        'Patrimonio Neto': patrimonio_neto,
        'Ventas': ventas,
        'Resultado Neto': resultado_neto
    }).dropna().round(2)

    # 3. Interfaz Visual del Tablero
    st.divider()
    
    # Selector de año para ver la foto de un periodo específico
    años_disponibles = df_kpis.index.sort_values(ascending=False).tolist()
    año_seleccionado = st.selectbox("Seleccionar Año de Análisis (Foto al Cierre):", años_disponibles)
    
    # Tarjetas de resumen (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    
    datos_año = df_kpis.loc[año_seleccionado]
    
    col1.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']}")
    col2.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']}")
    col3.metric("ROE (Rentabilidad sobre PN)", f"{datos_año['ROE (%)']}%")
