import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(page_title="Tablero de Análisis Integral", layout="wide")

# --- FUNCIONES AUXILIARES (SEMAFOROS Y DELTAS) ---
def semaforo(valor, metrica):
    """Devuelve un emoji de semáforo basado en rangos de salud financiera."""
    if pd.isna(valor): return "📊"
    
    if metrica == 'Liquidez Corriente':
        return "🟢" if valor >= 1.5 else "🟡" if valor >= 1.0 else "🔴"
    elif metrica == 'Prueba Acida':
        return "🟢" if valor >= 1.0 else "🟡" if valor >= 0.8 else "🔴"
    elif metrica == 'Endeudamiento':
        return "🟢" if valor <= 1.5 else "🟡" if valor <= 2.5 else "🔴"
    elif metrica == 'Margen Neto':
        return "🟢" if valor >= 10 else "🟡" if valor >= 5 else "🔴"
    elif metrica == 'ROE':
        return "🟢" if valor >= 15 else "🟡" if valor > 0 else "🔴"
    elif metrica == 'Solvencia':
        return "🟢" if valor >= 2.0 else "🟡" if valor >= 1.5 else "🔴"
    return "📊"

def calc_delta(val_actual, val_ant, inverso=False):
    """Calcula la variación para el parámetro delta de st.metric."""
    if val_ant is None or pd.isna(val_ant) or pd.isna(val_actual):
        return None
    diff = val_actual - val_ant
    return float(diff)

# --- FUNCIÓN DE PANTALLA COMPLETA (POP-UP) ---
@st.dialog("🔍 Vista Ampliada del Análisis", width="large")
def mostrar_grafico_ampliado(figura):
    fig_xl = go.Figure(figura)
    fig_xl.update_layout(height=650)
    st.plotly_chart(fig_xl, use_container_width=True)

# --- FUNCIÓN OPTIMIZADA PARA IMPRESIÓN EJECUTIVA EN A4 HORIZONTAL ---
def insertar_boton_impresion():
    st.markdown("""
        <style>
        @media print {
            @page { size: A4 landscape; margin: 15mm 12mm 15mm 12mm; }
            [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], footer, button, .stButton { display: none !important; }
            .main, .block-container, div { overflow: visible !important; height: auto !important; width: 100% !important; max-width: 100% !important; padding-top: 0 !important; padding-bottom: 0 !important; }
            .js-plotly-plot, .plotly { width: 100% !important; height: auto !important; page-break-inside: avoid !important; }
            div[data-testid="stMetric"] { page-break-inside: avoid !important; background-color: #fafafa !important; border: 1px solid #e6e6e6 !important; padding: 10px !important; border-radius: 6px !important; }
            .stInfo { page-break-inside: avoid !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    components.html("""
        <button onclick="window.parent.print()" style="
            background-color: #1E3A8A; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: 600; font-size: 14px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); transition: background-color 0.2s;
        " onmouseover="this.style.backgroundColor='#172554'" onmouseout="this.style.backgroundColor='#1E3A8A'">
            🖨️ Generar Reporte de Impresión / Guardar PDF Ejecutivo
        </button>
    """, height=45)

# LEYENDAS Y PALETA NORDIC CORPORATE
config_leyenda_abajo = dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5)
COLOR_ACT_CORR = '#10B981'   # Verde esmeralda
COLOR_ACT_NOCORR = '#047857' # Verde oscuro
COLOR_PAS_CORR = '#F97316'   # Naranja
COLOR_PAS_NOCORR = '#C2410C' # Naranja oscuro
COLOR_PN = '#1E3A8A'         # Azul profundo
COLOR_VENTAS = '#3B82F6'     # Azul claro

# --- INYECCIÓN DE CSS PARA CABECERA FLOTANTE FIJA (STICKY HEADER) ---
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlock"] > div:has(div.sticky-header) {
        position: sticky; top: 2.875rem; background-color: white; z-index: 999; border-bottom: 1px solid #f0f2f6; padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    archivo_subido = st.file_uploader("Subí el archivo Excel (.xlsx)", type=["xlsx"])
    nombre_empresa, cuit_empresa, domicilio_empresa, cierre_empresa, leyenda_ipc = "Empresa no identificada", "", "", "", ""

    if archivo_subido is not None:
        try:
            df_empresa_raw = pd.read_excel(archivo_subido, sheet_name="Datos Empresa", header=None)
            dict_empresa = dict(zip(df_empresa_raw[0].astype(str).str.strip(), df_empresa_raw[1]))
            nombre_empresa = dict_empresa.get("Empresa", "Empresa Registrada")
            cuit_empresa = dict_empresa.get("CUIT", "")
            domicilio_empresa = dict_empresa.get("Domicilio", "")
            raw_cierre = dict_empresa.get("Cierre Ejercicio", "")
            if pd.api.types.is_datetime64_any_dtype(pd.Series([raw_cierre])) or isinstance(raw_cierre, (pd.Timestamp, np.datetime64)):
                cierre_empresa = pd.to_datetime(raw_cierre).strftime('%Y-%m-%d')
            else:
                cierre_empresa = str(raw_cierre).split(" ")[0] if " " in str(raw_cierre) else str(raw_cierre)
        except Exception: pass

        try:
            df_ipc = pd.read_excel(archivo_subido, sheet_name="IPC")
            df_ipc['MES'] = pd.to_datetime(df_ipc['MES'])
            df_ipc_valido = df_ipc.dropna(subset=['IPC NACIONAL EMPALME IPIM'])
            if not df_ipc_valido.empty:
                ultima_fecha_ipc = df_ipc_valido['MES'].max()
                meses_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
                leyenda_ipc = f"Los datos monetarios están actualizados al {meses_es[ultima_fecha_ipc.month]} de {ultima_fecha_ipc.year}"
        except Exception: pass

        df_historico = pd.read_excel(archivo_subido, sheet_name="Balances Historicos")
        df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
        lista_años = sorted(df_pivot.index.tolist())

        st.markdown("---")
        año_seleccionado = st.selectbox("Ejercicio Económico:", options=sorted(lista_años, reverse=True), index=0)
        rango_años = st.slider("Tendencia Histórica:", min_value=int(min(lista_años)), max_value=int(max(lista_años)), value=(int(min(lista_años)), int(max(lista_años))))
        
        st.markdown("---")
        solapa_seleccionada = st.radio(
            "Seleccioná la sección:",
            options=[
                "🏠 Resumen Ejecutivo", 
                "🏛️ Estructura Patrimonial", 
                "💧 Liquidez y Solvencia", 
                "🔄 Ciclo Operativo",
                "📈 Rentabilidad y Margenes"
            ]
        )
        st.markdown("---")
        if leyenda_ipc: st.caption(f"ℹ️ {leyenda_ipc}")
        if cierre_empresa: st.caption(f"📅 Cierre: {cierre_empresa}")

# --- CUERPO PRINCIPAL ---
if archivo_subido is not None:
    df_rubros_raw = pd.read_excel(archivo_subido, sheet_name="Rubros Grales", header=None)
    try:
        fila_inicio = df_rubros_raw[df_rubros_raw[0] == 'Sub Rubro'].index[0]
        df_mapeo = df_rubros_raw.iloc[fila_inicio+1:].dropna(subset=[0, 1]).copy()
        df_mapeo.columns = ['Sub Rubro', 'Cuenta']
        df_mapeo['Sub Rubro'] = df_mapeo['Sub Rubro'].astype(str).str.strip()
        df_mapeo['Cuenta'] = df_mapeo['Cuenta'].astype(str).str.strip()
    except Exception:
        st.error("⚠️ Error en la solapa 'Rubros Grales'.")
        st.stop()

    def sumar_sub_rubro(df_datos, df_map, sub_rubro_nombre):
        cuentas = df_map[df_map['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
        cuentas_existing = [c for c in cuentas if c in df_datos.columns]
        if not cuentas_existing: return pd.Series(0, index=df_datos.index)
        return df_datos[cuentas_existing].sum(axis=1)

    # Variables
    activo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo Corriente')
    activo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo No Corriente')
    activo_total = activo_corriente + activo_no_corriente
    pasivo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo Corriente')
    pasivo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo no Corriente')
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    patrimonio_neto = sumar_sub_rubro(df_pivot, df_mapeo, 'Patrimonio Neto')
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    activo_liquido_puro = df_pivot.get('activo liquido', pd.Series(0, index=df_pivot.index))
    creditos_comerciales_puros = df_pivot.get('creditos comerciales', pd.Series(0, index=df_pivot.index))
    prueba_acida = (activo_liquido_puro + creditos_comerciales_puros) / pasivo_corriente.replace(0, pd.NA)
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    capital_trabajo = activo_corriente - pasivo_corriente
    solvencia = activo_total / pasivo_total.replace(0, pd.NA)
    indice_garantia = patrimonio_neto / pasivo_total.replace(0, pd.NA)
    
    ventas = df_pivot.get('ventas', pd.Series(0, index=df_pivot.index))
    resultado_neto = df_pivot.get('Resultado Neto', pd.Series(0, index=df_pivot.index))
    ebitda_proxy = resultado_neto + df_pivot.get('Amortizacion', 0) + df_pivot.get('Intereses Financieros', 0) + df_pivot.get('impuesto a las gs', 0)
    margen_ebitda = (ebitda_proxy / ventas.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100
    efecto_palanca = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) / ((resultado_neto + df_pivot.get('Intereses Financieros', 0)) / (patrimonio_neto + pasivo_no_corriente).replace(0, pd.NA)).replace(0, pd.NA)
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

    cmv = df_pivot.get('Costo Mercaderia Vendida', pd.Series(0, index=df_pivot.index))
    cmv_seguro = np.where(cmv == 0, ventas, cmv)
    rot_activo_total = ventas / activo_total.replace(0, pd.NA)
    rot_activo_corriente = ventas / activo_corriente.replace(0, pd.NA)
    rot_bienes_uso = ventas / df_pivot.get('Bienes de Uso', pd.Series(0, index=df_pivot.index)).replace(0, pd.NA)
    dias_cobro = (creditos_comerciales_puros / ventas.replace(0, pd.NA)) * 365
    dias_inventario = (df_pivot.get('Bienes de cambio', pd.Series(0, index=df_pivot.index)) / pd.Series(cmv_seguro, index=df_pivot.index).replace(0, pd.NA)) * 365
    dias_pago = (df_pivot.get('Deudas comerciales', pd.Series(0, index=df_pivot.index)) / pd.Series(cmv_seguro, index=df_pivot.index).replace(0, pd.NA)) * 365

    df_kpis = pd.DataFrame({
        'Activo Corriente': activo_corriente / 1e6, 'Activo No Corriente': activo_no_corriente / 1e6, 'Activo Total': activo_total / 1e6,
        'Pasivo Corriente': pasivo_corriente / 1e6, 'Pasivo No Corriente': pasivo_no_corriente / 1e6, 'Pasivo Total': pasivo_total / 1e6,
        'Patrimonio Neto': patrimonio_neto / 1e6, 'Endeudamiento': endeudamiento,
        'Liquidez Corriente': liquidez_corriente, 'Prueba Acida': prueba_acida, 'Capital de Trabajo': capital_trabajo / 1e6,
        'Solvencia': solvencia, 'Garantia': indice_garantia, 'Efecto Palanca': efecto_palanca,
        'Ventas': ventas / 1e6, 'Resultado Neto': resultado_neto / 1e6, 'EBITDA Proxy': ebitda_proxy / 1e6,
        'Margen Neto (%)': margen_neto, 'Margen EBITDA (%)': margen_ebitda, 'ROE (%)': roe, 
        'Rotacion Activos': rotacion_activos, 'Multiplicador Capital': multiplicador_capital,
        'Rotacion Activo Total': rot_activo_total, 'Rotacion Activo Corriente': rot_activo_corriente,
        'Rotacion Bienes Uso': rot_bienes_uso,
        'Dias Cobro': dias_cobro, 'Dias Inventario': dias_inventario, 'Dias Pago': dias_pago
    }).dropna(how='all').round(2)

    datos_año = df_kpis.loc[año_seleccionado]
    df_filtrado = df_kpis.loc[rango_años[0]:rango_años[1]]

    # Calcular Datos Año Anterior para las flechas (Delta)
    idx_año = lista_años.index(año_seleccionado)
    if idx_año > 0: # Como la lista está en orden normal ascendente o descendente? lista_años = sorted(...) -> ascendente.
        # Espera, selectbox reverse=True. idx_año en lista_años que es ascendente.
        pass 
    
    # Búsqueda segura del año anterior
    año_ant = None
    datos_año_ant = None
    lista_desc = sorted(lista_años, reverse=True)
    idx_desc = lista_desc.index(año_seleccionado)
    if idx_desc < len(lista_desc) - 1:
        año_ant = lista_desc[idx_desc + 1]
        datos_año_ant = df_kpis.loc[año_ant]

    # --- CONTENEDOR DE TÍTULO FIJO / STICKY HEADER ---
    st.markdown(
        f"""
        <div class="sticky-header" style="text-align: center;">
            <h2 style='margin: 0; font-size: 26px; font-weight: bold; color: {COLOR_PN};'>🏢 {nombre_empresa} | Tablero de Control</h2>
            <p style='margin: 0; color: #666; font-size: 15px;'>{solapa_seleccionada} | Ejercicio Seleccionado: {año_seleccionado}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.write("")

    # --- ENRUTADOR DE CONTENIDO ---
    if solapa_seleccionada == "🏠 Resumen Ejecutivo":
        st.subheader(f"📊 Resumen Ejecutivo - Ejercicio {año_seleccionado}")
        insertar_boton_impresion()
        
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("📊 Volumen de Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M", delta=calc_delta(datos_año['Ventas'], datos_año_ant['Ventas'] if datos_año_ant is not None else None), help="Facturación neta total del ejercicio expresada en Millones.")
        col_p2.metric(f"{semaforo(datos_año['Resultado Neto'], 'Resultado')} Resultado Neto del Ejercicio", f"$ {datos_año['Resultado Neto']:,.2f} M", delta=calc_delta(datos_año['Resultado Neto'], datos_año_ant['Resultado Neto'] if datos_año_ant is not None else None), help="Ganancia final limpia del ejercicio después de impuestos y amortizaciones.")
        col_p3.metric("📊 Caja Operativa (EBITDA Proxy)", f"$ {datos_año['EBITDA Proxy']:,.2f} M", delta=calc_delta(datos_año['EBITDA Proxy'], datos_año_ant['EBITDA Proxy'] if datos_año_ant is not None else None), help="Capacidad pura del negocio core para generar fondos líquidos aislando amortizaciones e intereses.")
        
        st.write("")
        col_p4, col_p5, col_p6 = st.columns(3)
        col_p4.metric(f"{semaforo(datos_año['ROE (%)'], 'ROE')} Rentabilidad s/ Capital (ROE)", f"{datos_año['ROE (%)']:.2f}%", delta=calc_delta(datos_año['ROE (%)'], datos_año_ant['ROE (%)'] if datos_año_ant is not None else None), help="Métrica reina del accionista: rendimiento obtenido por cada peso invertido en el PN.")
        col_p5.metric(f"{semaforo(datos_año['Margen Neto (%)'], 'Margen Neto')} Margen de Eficiencia Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=calc_delta(datos_año['Margen Neto (%)'], datos_año_ant['Margen Neto (%)'] if datos_año_ant is not None else None), help="Porcentaje de cada peso facturado que se convierte en utilidad neta final.")
        col_p6.metric(f"{semaforo(datos_año['Liquidez Corriente'], 'Liquidez Corriente')} Índice de Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}", delta=calc_delta(datos_año['Liquidez Corriente'], datos_año_ant['Liquidez Corriente'] if datos_año_ant is not None else None), help="Relación de cobertura de corto plazo. Valores > 1.0 indican colchón monetario positivo.")
        
        st.write("")
        st.markdown("---")
        
        col_rad1, col_rad2, col_rad3 = st.columns([1, 2, 1])
        with col_rad2:
            st.markdown("<p style='text-align: center; font-weight: bold;'>🎯 Radar de Desempeño (Dimensiones Normalizadas)</p>", unsafe_allow_html=True)
            categorias = ['Liquidez', 'Solvencia', 'Rentabilidad (Margen)', 'Retorno Accionista (ROE)', 'Endeudamiento (Inverso)']
            val_liq = min(datos_año['Liquidez Corriente'] * 20, 100)
            val_solv = min(datos_año['Solvencia'] * 20, 100)
            val_marg = max(min(datos_año['Margen Neto (%)'] * 3, 100), 0)
            val_roe = max(min(datos_año['ROE (%)'] * 2, 100), 0)
            val_end = max(min((2 / (datos_año['Endeudamiento'] + 0.1)) * 50, 100), 0)
            
            valores_radar = [val_liq, val_solv, val_marg, val_roe, val_end]
            valores_radar.append(valores_radar[0])
            categorias.append(categorias[0])
            
            fig_radar = go.Figure(go.Scatterpolar(
                r=valores_radar, theta=categorias, fill='toself', fillcolor='rgba(30, 58, 138, 0.25)', line=dict(color=COLOR_PN, width=3),
                name=f'Ejercicio {año_seleccionado}', hovertemplate="Nivel de Salud: %{r:.1f}/100<extra></extra>"
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False), angularaxis=dict(tickfont=dict(size=12))), showlegend=False, height=450, margin=dict(t=30, b=20, l=40, r=40))
            st.plotly_chart(fig_radar, use_container_width=True)

        st.info("**💡 Interpretación:** El polígono integra las fuerzas vitales de la firma. Mayor extensión hacia los extremos indica mejor salud global.")

    elif solapa_seleccionada == "🏛️ Estructura Patrimonial":
        insertar_boton_impresion()
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("📊 Activo Total", f"$ {datos_año['Activo Total']:,.2f} M", delta=calc_delta(datos_año['Activo Total'], datos_año_ant['Activo Total'] if datos_año_ant is not None else None))
        col_a2.metric("🟢 Activo Corriente", f"$ {datos_año['Activo Corriente']:,.2f} M", delta=calc_delta(datos_año['Activo Corriente'], datos_año_ant['Activo Corriente'] if datos_año_ant is not None else None))
        col_a3.metric("🟢 Activo No Corriente", f"$ {datos_año['Activo No Corriente']:,.2f} M", delta=calc_delta(datos_año['Activo No Corriente'], datos_año_ant['Activo No Corriente'] if datos_año_ant is not None else None))
        
        st.write("")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("🔵 Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M", delta=calc_delta(datos_año['Patrimonio Neto'], datos_año_ant['Patrimonio Neto'] if datos_año_ant is not None else None))
        col_m2.metric("🟠 Pasivo Total", f"$ {datos_año['Pasivo Total']:,.2f} M", delta=calc_delta(datos_año['Pasivo Total'], datos_año_ant['Pasivo Total'] if datos_año_ant is not None else None), delta_color="inverse")
        col_m3.metric(f"{semaforo(datos_año['Endeudamiento'], 'Endeudamiento')} Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}", delta=calc_delta(datos_año['Endeudamiento'], datos_año_ant['Endeudamiento'] if datos_año_ant is not None else None), delta_color="inverse")
        
        st.write("")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Bar(x=['Activo'], y=[datos_año['Activo No Corriente']], name='Activo No Corriente', marker_color=COLOR_ACT_NOCORR, text=[datos_año['Activo No Corriente']], texttemplate="<b>Activo No Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle'))
        fig_eq.add_trace(go.Bar(x=['Activo'], y=[datos_año['Activo Corriente']], name='Activo Corriente', marker_color=COLOR_ACT_CORR, text=[datos_año['Activo Corriente']], texttemplate="<b>Activo Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle'))
        fig_eq.add_trace(go.Bar(x=['Pasivo + PN'], y=[datos_año['Patrimonio Neto']], name='Patrimonio Neto', marker_color=COLOR_PN, text=[datos_año['Patrimonio Neto']], texttemplate="<b>Patrimonio Neto</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle'))
        fig_eq.add_trace(go.Bar(x=['Pasivo + PN'], y=[datos_año['Pasivo No Corriente']], name='Pasivo No Corriente', marker_color=COLOR_PAS_NOCORR, text=[datos_año['Pasivo No Corriente']], texttemplate="<b>Pasivo No Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle'))
        fig_eq.add_trace(go.Bar(x=['Pasivo + PN'], y=[datos_año['Pasivo Corriente']], name='Pasivo Corriente', marker_color=COLOR_PAS_CORR, text=[datos_año['Pasivo Corriente']], texttemplate="<b>Pasivo Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle'))
        fig_eq.update_layout(barmode='stack', bargap=0, showlegend=False, height=420, margin=dict(t=10, b=10), plot_bgcolor='rgba(0,0,0,0)')
        
        col_eq_izq, col_eq_centro, col_eq_der = st.columns([1, 2, 1])
        with col_eq_centro:
            st.markdown("<p style='text-align: center; font-weight: bold;'>📋 Estructura Patrimonial</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_eq, use_container_width=True)

        st.write("")
        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            fig_pas = go.Figure()
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo Corriente'], name='Pasivo Corto Plazo', marker_color=COLOR_PAS_CORR))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo No Corriente'], name='Pasivo Largo Plazo', marker_color=COLOR_PAS_NOCORR))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Patrimonio Neto'], name='Patrimonio Neto', marker_color=COLOR_PN))
            fig_pas.update_layout(title="Evolución del Pasivo + PN", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_pas, use_container_width=True)
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color=COLOR_ACT_CORR))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente', marker_color=COLOR_ACT_NOCORR))
            fig_act.update_layout(title="Evolución de los Activos", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_act, use_container_width=True)

    elif solapa_seleccionada == "💧 Liquidez y Solvencia":
        insertar_boton_impresion()
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric(f"{semaforo(datos_año['Liquidez Corriente'], 'Liquidez Corriente')} Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}", delta=calc_delta(datos_año['Liquidez Corriente'], datos_año_ant['Liquidez Corriente'] if datos_año_ant is not None else None))
        col_m5.metric(f"{semaforo(datos_año['Prueba Acida'], 'Prueba Acida')} Prueba Ácida", f"{datos_año['Prueba Acida']:.2f}", delta=calc_delta(datos_año['Prueba Acida'], datos_año_ant['Prueba Acida'] if datos_año_ant is not None else None))
        col_m6.metric("📊 Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M", delta=calc_delta(datos_año['Capital de Trabajo'], datos_año_ant['Capital de Trabajo'] if datos_año_ant is not None else None))
        
        st.write("")
        col_m11, col_m12, col_m13 = st.columns(3)
        col_m11.metric(f"{semaforo(datos_año['Solvencia'], 'Solvencia')} Índice de Solvencia", f"{datos_año['Solvencia']:.2f}", delta=calc_delta(datos_año['Solvencia'], datos_año_ant['Solvencia'] if datos_año_ant is not None else None))
        col_m12.metric("📊 Índice de Garantía", f"{datos_año['Garantia']:.2f}", delta=calc_delta(datos_año['Garantia'], datos_año_ant['Garantia'] if datos_año_ant is not None else None))
        col_m13.metric("📊 Efecto Palanca (GAF)", f"{datos_año['Efecto Palanca']:.2f}x", delta=calc_delta(datos_año['Efecto Palanca'], datos_año_ant['Efecto Palanca'] if datos_año_ant is not None else None))
        
        st.write("")
        col_t2a, col_t2b = st.columns(2)
        with col_t2a:
            fig_liq = go.Figure()
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color=COLOR_ACT_CORR)))
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color=COLOR_PN, dash='dot')))
            fig_liq.add_hline(y=1.0, line_dash="dash", line_color=COLOR_PAS_CORR)
            fig_liq.update_layout(title="Evolución de Índices de Liquidez", hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_liq, use_container_width=True)
        with col_t2b:
            fig_solv = go.Figure()
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Solvencia'], mode='lines+markers', name='Solvencia', line=dict(width=3, color=COLOR_PN)))
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Garantia'], mode='lines+markers', name='Garantía', line=dict(width=3, color=COLOR_ACT_NOCORR, dash='dash')))
            fig_solv.update_layout(title="Evolución de Solvencia y Respaldo", hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_solv, use_container_width=True)

    elif solapa_seleccionada == "🔄 Ciclo Operativo":
        insertar_boton_impresion()
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("📊 Plazo Medio Cobranza", f"{datos_año['Dias Cobro']:.0f} días", delta=calc_delta(datos_año['Dias Cobro'], datos_año_ant['Dias Cobro'] if datos_año_ant is not None else None), delta_color="inverse")
        col_r2.metric("📊 Días de Stock", f"{datos_año['Dias Inventario']:.0f} días", delta=calc_delta(datos_año['Dias Inventario'], datos_año_ant['Dias Inventario'] if datos_año_ant is not None else None), delta_color="inverse")
        col_r3.metric("📊 Plazo Medio Pago", f"{datos_año['Dias Pago']:.0f} días", delta=calc_delta(datos_año['Dias Pago'], datos_año_ant['Dias Pago'] if datos_año_ant is not None else None))
        
        st.write("")
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            fig_ciclos = go.Figure()
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Cobro'], mode='lines+markers', name='Plazo Cobro', line=dict(color=COLOR_PN, width=3)))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Inventario'], mode='lines+markers', name='Plazo Stock', line=dict(color=COLOR_ACT_CORR, width=3)))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Pago'], mode='lines+markers', name='Plazo Pago', line=dict(color=COLOR_PAS_CORR, width=3, dash='dash')))
            fig_ciclos.update_layout(title="Evolución del Ciclo Operativo (Días)", yaxis=dict(range=[0, 365], showgrid=True), hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_ciclos, use_container_width=True)
        with col_tr2:
            fig_rot_act = go.Figure()
            fig_rot_act.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Total'], mode='lines+markers', name='Rot. Activo Total', line=dict(color=COLOR_ACT_NOCORR, width=3)))
            fig_rot_act.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Corriente'], mode='lines+markers', name='Rot. Activo Corriente', line=dict(color=COLOR_ACT_CORR, width=2, dash='dash')))
            fig_rot_act.update_layout(title="Intensidad de Rotación (Veces)", hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rot_act, use_container_width=True)

    elif solapa_seleccionada == "📈 Rentabilidad y Margenes":
        insertar_boton_impresion()
        col_m7, col_m8, col_m9, col_m10 = st.columns(4)
        col_m7.metric("📊 Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M", delta=calc_delta(datos_año['Ventas'], datos_año_ant['Ventas'] if datos_año_ant is not None else None))
        col_m8.metric("📊 Margen EBITDA", f"{datos_año['Margen EBITDA (%)']:.2f}%", delta=calc_delta(datos_año['Margen EBITDA (%)'], datos_año_ant['Margen EBITDA (%)'] if datos_año_ant is not None else None))
        col_m9.metric(f"{semaforo(datos_año['Margen Neto (%)'], 'Margen Neto')} Margen Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=calc_delta(datos_año['Margen Neto (%)'], datos_año_ant['Margen Neto (%)'] if datos_año_ant is not None else None))
        col_m10.metric(f"{semaforo(datos_año['ROE (%)'], 'ROE')} ROE Final", f"{datos_año['ROE (%)']:.2f}%", delta=calc_delta(datos_año['ROE (%)'], datos_año_ant['ROE (%)'] if datos_año_ant is not None else None))
        
        st.write("")
        col_t3a, col_t3b = st.columns(2)
        with col_t3a:
            fig_ventas = go.Figure()
            fig_ventas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Ventas'], name='Ventas', marker_color=COLOR_PN, yaxis='y'))
            fig_ventas.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%)', yaxis='y2', line=dict(color=COLOR_ACT_CORR, width=3)))
            fig_ventas.update_layout(title="Ventas vs Margen Neto Final", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_ventas, use_container_width=True)
        with col_t3b:
            fig_rent = go.Figure()
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='EBITDA', marker_color='#38BDF8'))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto', marker_color=COLOR_ACT_NOCORR))
            fig_rent.update_layout(title="EBITDA vs Resultado Neto Real", barmode='group', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rent, use_container_width=True)

        st.write("")
        st.markdown("---")
        fig_dupont_rent = go.Figure()
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], mode='lines+markers', name='ROE (%) [Eje Izq]', line=dict(color='#8B5CF6', width=4)))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%) [Eje Izq]', line=dict(color=COLOR_ACT_CORR, width=2, dash='dash')))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activos'], mode='lines+markers', name='Rotación Activos [Eje Der]', yaxis='y2', line=dict(color=COLOR_PN, width=2)))
        fig_dupont_rent.update_layout(title="🎯 Descomposición DuPont", yaxis2=dict(overlaying='y', side='right', showgrid=False), hovermode="x unified", height=450, legend=config_leyenda_abajo)
        st.plotly_chart(fig_dupont_rent, use_container_width=True)
else:
    st.info("👆 Por favor, abrí el panel de la barra lateral izquierda y subí el archivo Excel (.xlsx) para comenzar el análisis.")
