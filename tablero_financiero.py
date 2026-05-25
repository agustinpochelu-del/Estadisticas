import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit.components.v1 as components

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tablero de Control Integral", layout="wide")

# 2. ESTÉTICA Y CONTRASTE (CSS)
st.markdown(
    """
    <style>
    .stApp { background-color: #F1F5F9; }
    
    /* Sticky Header con Contraste Oscuro */
    div[data-testid="stVerticalBlock"] > div:has(div.sticky-header) {
        positiimport streamlit as st
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

def calc_delta(val_actual, val_ant, unidad=""):
    """Calcula la variación estricta a 2 decimales concatenando su unidad de medida."""
    if val_ant is None or pd.isna(val_ant) or pd.isna(val_actual):
        return None
    diff = val_actual - val_ant
    return f"{diff:+.2f} {unidad}".strip()

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
    nombre_empresa, cuit_empresa, domicilio_empresa = "Empresa no identificada", "", ""
    dia_cierre, mes_cierre = 31, 12
    leyenda_ipc = ""

    if archivo_subido is not None:
        try:
            df_empresa_raw = pd.read_excel(archivo_subido, sheet_name="Datos Empresa", header=None)
            dict_empresa = dict(zip(df_empresa_raw[0].astype(str).str.strip(), df_empresa_raw[1]))
            nombre_empresa = dict_empresa.get("Empresa", "Empresa Registrada")
            
            # Lógica robusta para extraer solo día y mes del cierre
            raw_cierre = dict_empresa.get("Cierre Ejercicio", "31/12")
            if isinstance(raw_cierre, str) and "/" in raw_cierre:
                partes = raw_cierre.split("/")
                dia_cierre, mes_cierre = int(partes[0]), int(partes[1])
            else:
                fecha_obj = pd.to_datetime(raw_cierre)
                dia_cierre, mes_cierre = fecha_obj.day, fecha_obj.month
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

        # Cálculo dinámico de fechas de balance
        ultimo_año_base = int(max(lista_años))
        fecha_ultimo_balance = f"{dia_cierre:02d}/{mes_cierre:02d}/{ultimo_año_base}"
        fecha_proximo_cierre = f"{dia_cierre:02d}/{mes_cierre:02d}/{ultimo_año_base + 1}"

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
        st.caption(f"📅 **Último balance:** {fecha_ultimo_balance}")
        st.caption(f"⏳ **Próximo cierre:** {fecha_proximo_cierre}")

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

    # Variables y cálculos
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

    # Búsqueda segura del año anterior para los deltas
    año_ant, datos_año_ant = None, None
    lista_desc = sorted(lista_años, reverse=True)
    idx_desc = lista_desc.index(año_seleccionado)
    if idx_desc < len(lista_desc) - 1:
        año_ant = lista_desc[idx_desc + 1]
        datos_año_ant = df_kpis.loc[año_ant]

    def get_delta(col_name, unidad=""):
        if datos_año_ant is None: return None
        return calc_delta(datos_año[col_name], datos_año_ant[col_name], unidad)

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
        
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric("📊 Volumen de Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M", delta=get_delta('Ventas', 'M'), help="Facturación neta total del ejercicio expresada en Millones.")
        col_p2.metric(f"{semaforo(datos_año['Resultado Neto'], 'Resultado')} Resultado Neto del Ejercicio", f"$ {datos_año['Resultado Neto']:,.2f} M", delta=get_delta('Resultado Neto', 'M'), help="Ganancia final limpia del ejercicio después de impuestos y amortizaciones.")
        col_p3.metric("📊 Caja Operativa (EBITDA Proxy)", f"$ {datos_año['EBITDA Proxy']:,.2f} M", delta=get_delta('EBITDA Proxy', 'M'), help="Capacidad pura del negocio core para generar fondos líquidos aislando amortizaciones e intereses.")
        
        st.write("")
        col_p4, col_p5, col_p6 = st.columns(3)
        col_p4.metric(f"{semaforo(datos_año['ROE (%)'], 'ROE')} Rentabilidad s/ Capital (ROE)", f"{datos_año['ROE (%)']:.2f}%", delta=get_delta('ROE (%)', '%'), help="Métrica reina del accionista: rendimiento obtenido por cada peso invertido en el PN.")
        col_p5.metric(f"{semaforo(datos_año['Margen Neto (%)'], 'Margen Neto')} Margen de Eficiencia Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=get_delta('Margen Neto (%)', '%'), help="Porcentaje de cada peso facturado que se convierte en utilidad neta final.")
        col_p6.metric(f"{semaforo(datos_año['Liquidez Corriente'], 'Liquidez Corriente')} Índice de Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}", delta=get_delta('Liquidez Corriente', 'x'), help="Relación de cobertura de corto plazo. Valores > 1.0 indican colchón monetario positivo.")
        
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
            
            valores_radar = [val_liq, val_solv, val_marg, val_roe, val_end, val_liq]
            categorias.append(categorias[0])
            
            fig_radar = go.Figure(go.Scatterpolar(
                r=valores_radar, theta=categorias, fill='toself', fillcolor='rgba(30, 58, 138, 0.25)', line=dict(color=COLOR_PN, width=3),
                name=f'Ejercicio {año_seleccionado}', hovertemplate="Nivel de Salud: %{r:.1f}/100<extra></extra>"
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False), angularaxis=dict(tickfont=dict(size=12))), showlegend=False, height=450, margin=dict(t=30, b=20, l=40, r=40))
            st.plotly_chart(fig_radar, use_container_width=True)

        st.write("")
        insertar_boton_impresion()
        st.info("**💡 Interpretación:** El polígono integra las fuerzas vitales de la firma. Mayor extensión hacia los extremos indica mejor salud global.")

    elif solapa_seleccionada == "🏛️ Estructura Patrimonial":
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("📊 Activo Total", f"$ {datos_año['Activo Total']:,.2f} M", delta=get_delta('Activo Total', 'M'))
        col_a2.metric("🟢 Activo Corriente", f"$ {datos_año['Activo Corriente']:,.2f} M", delta=get_delta('Activo Corriente', 'M'))
        col_a3.metric("🟢 Activo No Corriente", f"$ {datos_año['Activo No Corriente']:,.2f} M", delta=get_delta('Activo No Corriente', 'M'))
        
        st.write("")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("🔵 Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M", delta=get_delta('Patrimonio Neto', 'M'))
        # Pasivo y Endeudamiento se invierten los colores (Subir deuda es delta negativo visualmente)
        col_m2.metric("🟠 Pasivo Total", f"$ {datos_año['Pasivo Total']:,.2f} M", delta=get_delta('Pasivo Total', 'M'), delta_color="inverse")
        col_m3.metric(f"{semaforo(datos_año['Endeudamiento'], 'Endeudamiento')} Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}", delta=get_delta('Endeudamiento', 'x'), delta_color="inverse")
        
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

        st.write("")
        insertar_boton_impresion()
        st.info("**💡 Guía de Interpretación:** La Estructura Patrimonial refleja la partida doble ($A = P + PN$). Permite evaluar si las inversiones de largo plazo están calzadas con fondeo genuino.")

    elif solapa_seleccionada == "💧 Liquidez y Solvencia":
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric(f"{semaforo(datos_año['Liquidez Corriente'], 'Liquidez Corriente')} Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}", delta=get_delta('Liquidez Corriente', 'x'))
        col_m5.metric(f"{semaforo(datos_año['Prueba Acida'], 'Prueba Acida')} Prueba Ácida", f"{datos_año['Prueba Acida']:.2f}", delta=get_delta('Prueba Acida', 'x'))
        col_m6.metric("📊 Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M", delta=get_delta('Capital de Trabajo', 'M'))
        
        st.write("")
        col_m11, col_m12, col_m13 = st.columns(3)
        col_m11.metric(f"{semaforo(datos_año['Solvencia'], 'Solvencia')} Índice de Solvencia", f"{datos_año['Solvencia']:.2f}", delta=get_delta('Solvencia', 'x'))
        col_m12.metric("📊 Índice de Garantía", f"{datos_año['Garantia']:.2f}", delta=get_delta('Garantia', 'x'))
        col_m13.metric("📊 Efecto Palanca (GAF)", f"{datos_año['Efecto Palanca']:.2f}x", delta=get_delta('Efecto Palanca', 'x'))
        
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

        st.write("")
        insertar_boton_impresion()
        st.info("**💡 Guía de Interpretación:** Valores de liquidez > 1.0 indican un colchón monetario positivo. El efecto palanca expone si el uso de deuda externa beneficia o erosiona el retorno del negocio.")

    elif solapa_seleccionada == "🔄 Ciclo Operativo":
        col_r1, col_r2, col_r3 = st.columns(3)
        # Menos días de cobro y stock es mejor (inverse). Más días de pago suele ser mejor (normal).
        col_r1.metric("📊 Plazo Medio Cobranza", f"{datos_año['Dias Cobro']:.0f} días", delta=get_delta('Dias Cobro', 'días'), delta_color="inverse")
        col_r2.metric("📊 Días de Stock", f"{datos_año['Dias Inventario']:.0f} días", delta=get_delta('Dias Inventario', 'días'), delta_color="inverse")
        col_r3.metric("📊 Plazo Medio Pago", f"{datos_año['Dias Pago']:.0f} días", delta=get_delta('Dias Pago', 'días'))
        
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

        st.write("")
        insertar_boton_impresion()
        st.info("**💡 Guía de Interpretación:** Si la suma de *Cobro + Stock* supera con holgura los *Días de Pago*, la firma padece un déficit estructural de giro que consume liquidez genuina.")

    elif solapa_seleccionada == "📈 Rentabilidad y Margenes":
        col_m7, col_m8, col_m9, col_m10 = st.columns(4)
        col_m7.metric("📊 Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M", delta=get_delta('Ventas', 'M'))
        col_m8.metric("📊 Margen EBITDA", f"{datos_año['Margen EBITDA (%)']:.2f}%", delta=get_delta('Margen EBITDA (%)', '%'))
        col_m9.metric(f"{semaforo(datos_año['Margen Neto (%)'], 'Margen Neto')} Margen Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=get_delta('Margen Neto (%)', '%'))
        col_m10.metric(f"{semaforo(datos_año['ROE (%)'], 'ROE')} ROE Final", f"{datos_año['ROE (%)']:.2f}%", delta=get_delta('ROE (%)', '%'))
        
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
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='EBITDA', marker_color=COLOR_VENTAS))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto', marker_color=COLOR_ACT_NOCORR))
            fig_rent.update_layout(title="EBITDA vs Resultado Neto Real", barmode='group', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rent, use_container_width=True)

        st.write("")
        st.markdown("---")
        fig_dupont_rent = go.Figure()
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], mode='lines+markers', name='ROE (%) [Eje Izq]', line=dict(color=COLOR_PN, width=4)))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%) [Eje Izq]', line=dict(color=COLOR_ACT_CORR, width=2, dash='dash')))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activos'], mode='lines+markers', name='Rotación Activos [Eje Der]', yaxis='y2', line=dict(color=COLOR_PAS_CORR, width=2)))
        fig_dupont_rent.update_layout(title="🎯 Descomposición DuPont", yaxis2=dict(overlaying='y', side='right', showgrid=False), hovermode="x unified", height=450, legend=config_leyenda_abajo)
        st.plotly_chart(fig_dupont_rent, use_container_width=True)
        
        st.write("")
        insertar_boton_impresion()
        st.info("**💡 Guía de Interpretación DuPont:** Desarma el ROE para revelar la verdadera palanca de la rentabilidad: Eficiencia en Costos (Margen), Eficacia Operativa (Rotación) o Apalancamiento Financiero (Estructura de Fondeo).")

else:
    st.info("👆 Por favor, abrí el panel de la barra lateral izquierda y subí el archivo Excel (.xlsx) para comenzar el análisis.")on: sticky;
        top: 2.875rem;
        background-color: #1E293B;
        z-index: 999;
        padding: 15px 25px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border-radius: 0 0 12px 12px;
    }
    
    /* Cards para métricas */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    </style>
    """, unsafe_allow_html=True
)

# 3. PALETA DE COLORES
C_AZUL = '#336699'      # Patrimonio Neto
C_VERDE_D = '#2E7D32'   # Activo Corriente
C_VERDE_L = '#A5D6A7'   # Activo No Corriente
C_NARANJA = '#EF6C00'   # Pasivo Corriente
C_ROJO = '#C62828'      # Pasivo No Corriente
C_CELESTE = '#0288D1'   # Ventas / EBITDA
C_VIOLETA = '#7E57C2'   # Margen / ROE

# 4. FUNCIONES DE APOYO
def semaforo(valor, metrica):
    if pd.isna(valor): return "📊"
    if metrica == 'Liquidez Corriente': return "🟢" if valor >= 1.5 else "🟡" if valor >= 1.0 else "🔴"
    elif metrica == 'Prueba Acida': return "🟢" if valor >= 1.0 else "🟡" if valor >= 0.8 else "🔴"
    elif metrica == 'Endeudamiento': return "🟢" if valor <= 1.5 else "🟡" if valor <= 2.5 else "🔴"
    elif metrica == 'Margen Neto': return "🟢" if valor >= 10 else "🟡" if valor >= 5 else "🔴"
    elif metrica == 'ROE': return "🟢" if valor >= 15 else "🟡" if valor > 0 else "🔴"
    elif metrica == 'Solvencia': return "🟢" if valor >= 2.0 else "🟡" if valor >= 1.5 else "🔴"
    return "📊"

def calc_delta(val_actual, val_ant, unidad=""):
    if val_ant is None or pd.isna(val_ant) or pd.isna(val_actual) or val_ant == 0: return None
    diff = val_actual - val_ant
    return f"{diff:+.2f} {unidad}".strip()

@st.dialog("🔍 Detalle del Análisis", width="large")
def mostrar_grafico_ampliado(figura):
    f = go.Figure(figura)
    f.update_layout(height=700, paper_bgcolor='white')
    st.plotly_chart(f, use_container_width=True)

def boton_imprimir():
    st.write("")
    st.markdown("""
        <style>
        @media print {
            @page { size: A4 landscape; margin: 10mm; }
            [data-testid="stSidebar"], [data-testid="stHeader"], button { display: none !important; }
            .main, .block-container { padding: 0 !important; background-color: white !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    components.html("""
        <button onclick="window.parent.print()" style="background-color: #336699; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        🖨️ Generar Reporte PDF para el Cliente
        </button>""", height=50)

# 5. BARRA LATERAL Y CARGA
with st.sidebar:
    archivo = st.file_uploader("Cargar Balances (.xlsx)", type=["xlsx"])
    nombre_e, dia_c, mes_c, leyenda_i = "Empresa", 31, 12, ""

    if archivo:
        try:
            df_e = pd.read_excel(archivo, sheet_name="Datos Empresa", header=None)
            dic_e = dict(zip(df_e[0].astype(str).str.strip(), df_e[1]))
            nombre_e = dic_e.get("Empresa", "Empresa")
            raw_c = dic_e.get("Cierre Ejercicio", "31/12")
            if "/" in str(raw_c):
                dia_c, mes_c = map(int, str(raw_c).split("/")[:2])
            else:
                f_obj = pd.to_datetime(raw_c)
                dia_c, mes_c = f_obj.day, f_obj.month
        except: pass

        try:
            df_ipc = pd.read_excel(archivo, sheet_name="IPC")
            df_ipc['MES'] = pd.to_datetime(df_ipc['MES'])
            u_f = df_ipc.dropna(subset=['IPC NACIONAL EMPALME IPIM'])['MES'].max()
            meses = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
            leyenda_i = f"Datos ajustados al {meses[u_f.month]} de {u_f.year}"
        except: pass

        df_h = pd.read_excel(archivo, sheet_name="Balances Historicos")
        df_p = df_h.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
        lista_a = sorted(df_p.index.tolist())
        u_a = int(max(lista_a))
        
        st.markdown("---")
        selec_a = st.selectbox("Ejercicio:", sorted(lista_a, reverse=True))
        rango_a = st.slider("Histórico:", min(lista_a), max(lista_a), (min(lista_a), max(lista_a)))
        st.markdown("---")
        solapa = st.radio("Secciones:", ["🏠 Resumen Ejecutivo", "🏛️ Estructura Patrimonial", "💧 Liquidez y Solvencia", "🔄 Ciclo Operativo", "📈 Rentabilidad y Margenes"])
        st.markdown("---")
        st.caption(f"ℹ️ {leyenda_i}")
        st.caption(f"📅 **Cierre:** {dia_c:02d}/{mes_c:02d}/{selec_a}")

# 6. MOTOR DE CÁLCULO
if archivo:
    df_rub = pd.read_excel(archivo, sheet_name="Rubros Grales", header=None)
    f_i = df_rub[df_rub[0] == 'Sub Rubro'].index[0]
    map_r = df_rub.iloc[f_i+1:].dropna(subset=[0, 1]).copy()
    map_r.columns = ['Sub Rubro', 'Cuenta']
    
    def totalizar(nombre):
        cts = map_r[map_r['Sub Rubro'].str.lower() == nombre.lower()]['Cuenta'].tolist()
        ex = [c for c in cts if c in df_p.columns]
        return df_p[ex].sum(axis=1) if ex else pd.Series(0, index=df_p.index)

    # Variables Base
    ac, anc = totalizar('Activo Corriente'), totalizar('Activo No Corriente')
    pc, pnc = totalizar('Pasivo Corriente'), totalizar('Pasivo no Corriente')
    pn = totalizar('Patrimonio Neto')
    vts = df_p.get('ventas', pd.Series(0, index=df_p.index))
    rn = df_p.get('Resultado Neto', pd.Series(0, index=df_p.index))
    eb = rn + df_p.get('Amortizacion', 0) + df_p.get('Intereses Financieros', 0) + df_p.get('impuesto a las gs', 0)
    cmv = np.where(df_p.get('Costo Mercaderia Vendida', 0) == 0, vts, df_p.get('Costo Mercaderia Vendida', 0))

    df_k = pd.DataFrame({
        'AC': ac/1e6, 'ANC': anc/1e6, 'AT': (ac+anc)/1e6, 'PC': pc/1e6, 'PNC': pnc/1e6, 'PT': (pc+pnc)/1e6, 'PN': pn/1e6,
        'Liq': ac/pc.replace(0,np.nan), 'Acid': (df_p.get('activo liquido',0)+df_p.get('creditos comerciales',0))/pc.replace(0,np.nan),
        'Solv': (ac+anc)/(pc+pnc).replace(0,np.nan), 'Gar': pn/(pc+pnc).replace(0,np.nan),
        'End': (pc+pnc)/pn.replace(0,np.nan), 'Vts': vts/1e6, 'RN': rn/1e6, 'EB': eb/1e6,
        'Marg': (rn/vts.replace(0,np.nan))*100, 'ROE': (rn/pn.replace(0,np.nan))*100,
        'RotT': vts/(ac+anc).replace(0,np.nan), 'RotC': vts/ac.replace(0,np.nan),
        'DC': (df_p.get('creditos comerciales',0)/vts.replace(0,np.nan))*365,
        'DS': (df_p.get('Bienes de cambio',0)/pd.Series(cmv,index=df_p.index).replace(0,np.nan))*365,
        'DP': (df_p.get('Deudas comerciales',0)/pd.Series(cmv,index=df_p.index).replace(0,np.nan))*365,
        'GAF': (rn/pn.replace(0,np.nan))/((rn+df_p.get('Intereses Financieros',0))/(pn+pnc).replace(0,np.nan))
    }).round(2)

    dat_a = df_k.loc[selec_a]
    df_f = df_k.loc[rango_a[0]:rango_a[1]]
    lista_d = sorted(lista_a, reverse=True)
    idx_a = lista_d.index(selec_a)
    dat_ant = df_k.loc[lista_d[idx_a+1]] if idx_a < len(lista_d)-1 else None
    
    def get_d(col, u=""): return calc_delta(dat_a[col], dat_ant[col], u) if dat_ant is not None else None

    # STICKY HEADER
    st.markdown(f'<div class="sticky-header" style="text-align:center;"><h2 style="margin:0; color:white;">🏢 {nombre_e} | Tablero de Control</h2><p style="margin:0; color:#94A3B8;">{solapa} | Período: {selec_a}</p></div>', unsafe_allow_html=True)

    # ------------------ SOLAPAS ------------------
    if solapa == "🏠 Resumen Ejecutivo":
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Ventas Totales", f"$ {dat_a['Vts']:,.2f} M", get_d('Vts','M'))
        c2.metric(f"{semaforo(dat_a['RN'],'RN')} Resultado Neto", f"$ {dat_a['RN']:,.2f} M", get_d('RN','M'))
        c3.metric("📊 Caja (EBITDA)", f"$ {dat_a['EB']:,.2f} M", get_d('EB','M'))
        
        st.write("")
        c4, c5, c6 = st.columns(3)
        c4.metric(f"{semaforo(dat_a['ROE'],'ROE')} ROE", f"{dat_a['ROE']}%", get_d('ROE','%'))
        c5.metric(f"{semaforo(dat_a['Marg'],'Marg')} Margen Neto", f"{dat_a['Marg']}%", get_d('Marg','%'))
        c6.metric(f"{semaforo(dat_a['Liq'],'Liq')} Liquidez", dat_a['Liq'], get_d('Liq','x'))

        st.markdown("---")
        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.markdown("<p style='text-align:center; font-weight:bold; font-size:18px;'>🎯 Radar de Salud Financiera</p>", unsafe_allow_html=True)
            cat = ['Liquidez', 'Solvencia', 'Margen', 'ROE', 'Endeudamiento']
            val = [min(dat_a['Liq']*20,100), min(dat_a['Solv']*20,100), max(min(dat_a['Marg']*3,100),0), max(min(dat_a['ROE']*2,100),0), max(min((2/(dat_a['End']+0.1))*50,100),0)]
            fig_r = go.Figure(go.Scatterpolar(r=val+[val[0]], theta=cat+[cat[0]], fill='toself', fillcolor='rgba(51, 102, 153, 0.3)', line=dict(color=C_AZUL, width=3)))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)), showlegend=False, height=450, margin=dict(t=40,b=40))
            st.plotly_chart(fig_r, use_container_width=True)
            if st.button("🔍 Ampliar Radar"): mostrar_grafico_ampliado(fig_r)

        boton_imprimí = boton_imprimir()
        st.info("**💡 Guía Portada:** El radar resume el equilibrio. Un polígono amplio indica una empresa sana en liquidez, rentabilidad y estructura.")

    elif solapa == "🏛️ Estructura Patrimonial":
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Activo Total", f"$ {dat_a['AT']:,.2f} M", get_d('AT','M'))
        c2.metric("🔵 Patrimonio Neto", f"$ {dat_a['PN']:,.2f} M", get_d('PN','M'))
        c3.metric(f"{semaforo(dat_a['End'],'End')} Endeudamiento", dat_a['End'], get_d('End','x'), delta_color="inverse")
        
        st.write("")
        col_p1, col_p2, col_p3 = st.columns([0.5, 9, 0.5])
        with col_p2:
            st.markdown("<p style='text-align:center; font-weight:bold; font-size:18px;'>📊 Situación Patrimonial</p>", unsafe_allow_html=True)
            fig_eq = go.Figure()
            # Bloque Izquierdo (Activo)
            fig_eq.add_trace(go.Bar(x=['Inversión'], y=[dat_a['ANC']], name='Activo No Corr.', marker_color=C_VERDE_L, text=[f"<b>Activo No Corriente</b><br>$ {dat_a['ANC']:.2f} M"], textposition='inside'))
            fig_eq.add_trace(go.Bar(x=['Inversión'], y=[dat_a['AC']], name='Activo Corr.', marker_color=C_VERDE_D, text=[f"<b>Activo Corriente</b><br>$ {dat_a['AC']:.2f} M"], textposition='inside'))
            # Bloque Derecho (Fondeo)
            fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[dat_a['PN']], name='Patr. Neto', marker_color=C_AZUL, text=[f"<b>Patrimonio Neto</b><br>$ {dat_a['PN']:.2f} M"], textposition='inside'))
            fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[dat_a['PNC']], name='Pasivo No Corr.', marker_color=C_ROJO, text=[f"<b>Pasivo No Corriente</b><br>$ {dat_a['PNC']:.2f} M"], textposition='inside'))
            fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[dat_a['PC']], name='Pasivo Corr.', marker_color=C_NARANJA, text=[f"<b>Pasivo Corriente</b><br>$ {dat_a['PC']:.2f} M"], textposition='inside'))
            
            fig_eq.update_layout(barmode='stack', bargap=0.05, height=500, showlegend=False, margin=dict(t=10,b=10),
                                xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False, showticklabels=False))
            st.plotly_chart(fig_eq, use_container_width=True)
            if st.button("🔍 Ampliar Estructura"): mostrar_grafico_ampliado(fig_eq)

        st.write("---")
        g1, g2 = st.columns(2)
        with g1:
            fig1 = go.Figure([go.Bar(x=df_f.index, y=df_f['PC'], name='Pas. Corr', marker_color=C_NARANJA), go.Bar(x=df_f.index, y=df_f['PNC'], name='Pas. No Corr', marker_color=C_ROJO), go.Bar(x=df_f.index, y=df_f['PN'], name='PN', marker_color=C_AZUL)])
            fig1.update_layout(title="Evolución del Pasivo + PN", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = go.Figure([go.Bar(x=df_f.index, y=df_f['AC'], name='Act. Corr', marker_color=C_VERDE_D), go.Bar(x=df_f.index, y=df_f['ANC'], name='Act. No Corr', marker_color=C_VERDE_L)])
            fig2.update_layout(title="Evolución de los Activos", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig2, use_container_width=True)
        
        boton_imprimí = boton_imprimir()
        st.info("**💡 Interpretación Patrimonial:** Evalúa si las inversiones de largo plazo (Bienes de Uso) están calzadas con fondeo genuino (PN) para evitar descalces financieros.")

    elif solapa == "💧 Liquidez y Solvencia":
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{semaforo(dat_a['Liq'],'Liq')} Liquidez Corriente", dat_a['Liq'], get_d('Liq','x'))
        c2.metric(f"{semaforo(dat_a['Acid'],'Acid')} Prueba Ácida", dat_a['Acid'], get_d('Acid','x'))
        c3.metric(f"{semaforo(dat_a['Solv'],'Solv')} Solvencia", dat_a['Solv'], get_d('Solv','x'))

        st.write("")
        g1, g2 = st.columns(2)
        with g1:
            fig1 = go.Figure([go.Scatter(x=df_f.index, y=df_f['Liq'], name='Liquidez', line=dict(color=C_VERDE_D, width=3)), go.Scatter(x=df_f.index, y=df_f['Acid'], name='Ácida', line=dict(color=C_AZUL, dash='dot'))])
            fig1.add_hline(y=1.0, line_dash="dash", line_color=C_ROJO)
            fig1.update_layout(title="Evolución de Liquidez", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = go.Figure([go.Scatter(x=df_f.index, y=df_f['Solv'], name='Solvencia', line=dict(color=C_AZUL, width=3)), go.Scatter(x=df_f.index, y=df_f['Gar'], name='Garantía', line=dict(color=C_VERDE_L, dash='dash'))])
            fig2.update_layout(title="Evolución de Solvencia", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig2, use_container_width=True)
            
        boton_imprimí = boton_imprimir()
        st.info("**💡 Guía de Liquidez:** Un índice mayor a 1.0 es el mínimo de seguridad. La solvencia mide la capacidad de responder a deudas con todos los activos de la firma.")

    elif solapa == "🔄 Ciclo Operativo":
        c1, c2, c3 = st.columns(3)
        c1.metric("⏱️ Cobro", f"{dat_a['DC']:.0f} días", get_d('DC','d'), delta_color="inverse")
        c2.metric("⏱️ Stock", f"{dat_a['DS']:.0f} días", get_d('DS','d'), delta_color="inverse")
        c3.metric("⏱️ Pago", f"{dat_a['DP']:.0f} días", get_d('DP','d'))

        st.write("")
        g1, g2 = st.columns(2)
        with g1:
            fig1 = go.Figure([go.Scatter(x=df_f.index, y=df_f['DC'], name='Cobro', line=dict(color=C_AZUL)), go.Scatter(x=df_f.index, y=df_f['DS'], name='Stock', line=dict(color=C_VERDE_D)), go.Scatter(x=df_f.index, y=df_f['DP'], name='Pago', line=dict(color=C_NARANJA, dash='dash'))])
            fig1.update_layout(title="Ciclo Operativo (Días)", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_f.index, y=df_f['RotT'], mode='lines+markers', name='Rot. Total', line=dict(color=C_AZUL, width=3)))
            fig2.add_trace(go.Scatter(x=df_f.index, y=df_f['RotC'], mode='lines+markers', name='Rot. Corriente', line=dict(color=C_VERDE_D, dash='dash')))
            fig2.update_layout(title="Intensidad de Rotación (Veces)", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig2, use_container_width=True)
            
        boton_imprimí = boton_imprimir()
        st.info("**💡 Guía Ciclos:** Si el *Cobro + Stock* supera con creces el *Pago*, la empresa tiene un 'Déficit Estructural de Giro' que requiere fondeo propio constante.")

    elif solapa == "📈 Rentabilidad y Margenes":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Ventas", f"$ {dat_a['Vts']:,.2f} M", get_d('Vts','M'))
        c2.metric(f"{semaforo(dat_a['Marg'],'Marg')} Margen Neto", f"{dat_a['Marg']}%", get_d('Marg','%'))
        c3.metric(f"{semaforo(dat_a['ROE'],'ROE')} ROE", f"{dat_a['ROE']}%", get_d('ROE','%'))
        c4.metric("📊 GAF (Palanca)", f"{dat_a['GAF']}x", get_d('GAF','x'))

        st.write("")
        g1, g2 = st.columns(2)
        with g1:
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=df_f.index, y=df_f['Vts'], name='Ventas', marker_color=C_CELESTE, yaxis='y'))
            fig1.add_trace(go.Scatter(x=df_f.index, y=df_f['Marg'], name='Margen %', line=dict(color=C_VIOLETA, width=3), yaxis='y2'))
            fig1.update_layout(title="Ventas vs Margen Neto Final", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            fig2 = go.Figure([go.Bar(x=df_f.index, y=df_f['EB'], name='EBITDA', marker_color=C_AZUL), go.Bar(x=df_f.index, y=df_f['RN'], name='Res. Neto', marker_color=C_VERDE_D)])
            fig2.update_layout(title="EBITDA vs Resultado Neto Real", barmode='group', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig2, use_container_width=True)
            
        st.write("---")
        fig_d = go.Figure()
        fig_d.add_trace(go.Scatter(x=df_f.index, y=df_f['ROE'], name='ROE %', line=dict(color=C_VIOLETA, width=4)))
        fig_d.add_trace(go.Scatter(x=df_f.index, y=df_f['Marg'], name='Margen %', line=dict(color=C_AZUL, dash='dash')))
        fig_d.add_trace(go.Scatter(x=df_f.index, y=df_f['RotT'], name='Rotación (Der)', yaxis='y2', line=dict(color=C_VERDE_D)))
        fig_d.update_layout(title="🎯 Descomposición DuPont", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=450, legend=config_leyenda_abajo)
        st.plotly_chart(fig_d, use_container_width=True)

        boton_imprimí = boton_imprimir()
        st.info("**💡 Guía DuPont:** Este modelo indica si la rentabilidad del socio viene por eficiencia en costos (Margen), por eficiencia operativa (Rotación) o por uso de deuda.")
else:
    st.info("👆 Cargá el archivo Excel para iniciar el análisis dinámico.")
