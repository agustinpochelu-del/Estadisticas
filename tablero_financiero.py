import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(page_title="Tablero de Control", layout="wide")

# --- ESTÉTICA GENERAL: FONDO Y CONTENEDORES ---
st.markdown(
    """
    <style>
    /* Fondo de la aplicación */
    .stApp {
        background-color: #F1F5F9;
    }
    
    /* Cabecera Fija (Sticky Header) */
    div[data-testid="stVerticalBlock"] > div:has(div.sticky-header) {
        position: sticky;
        top: 2.875rem;
        background-color: white;
        z-index: 999;
        border-bottom: 1px solid #E2E8F0;
        padding: 15px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-radius: 0 0 10px 10px;
    }

    /* Estilo para los botones de imprimir y ampliar */
    .stButton > button {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- FUNCIONES AUXILIARES (SEMAFOROS Y DELTAS) ---
def semaforo(valor, metrica):
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
    if val_ant is None or pd.isna(val_ant) or pd.isna(val_actual):
        return None
    diff = val_actual - val_ant
    return f"{diff:+.2f} {unidad}".strip()

# --- FUNCIÓN DE PANTALLA COMPLETA (POP-UP) ---
@st.dialog("🔍 Vista Ampliada del Análisis", width="large")
def mostrar_grafico_ampliado(figura):
    fig_xl = go.Figure(figura)
    fig_xl.update_layout(height=650, paper_bgcolor='white', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_xl, use_container_width=True)

# --- FUNCIÓN DE IMPRESIÓN ---
def insertar_boton_impresion():
    st.markdown("""
        <style>
        @media print {
            @page { size: A4 landscape; margin: 15mm 12mm 15mm 12mm; }
            [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"], footer, button, .stButton { display: none !important; }
            .main, .block-container, div { overflow: visible !important; height: auto !important; width: 100% !important; max-width: 100% !important; padding: 0 !important; background-color: white !important; }
            .js-plotly-plot, .plotly { width: 100% !important; page-break-inside: avoid !important; }
        }
        </style>
    """, unsafe_allow_html=True)
    
    components.html(f"""
        <button onclick="window.parent.print()" style="
            background-color: #6482A1; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: 600; font-size: 14px; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
        ">🖨️ Generar Reporte de Impresión / Guardar PDF Ejecutivo</button>
    """, height=45)

# PALETA CORPORATIVA SUAVE (MUTED PASTELS)
COLOR_PN = '#6482A1'         # Azul Pizarra
COLOR_VENTAS = '#7A96B1'     # Azul Claro
COLOR_ACT_CORR = '#7D9B8B'   # Verde Salvia
COLOR_PAS_CORR = '#C4A67A'   # Mostaza/Arena
COLOR_PAS_NOCORR = '#B67E79' # Rosa Viejo/Terracota
COLOR_ACT_NOCORR = '#A3A09E' # Gris Cálido
config_leyenda_abajo = dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5)

# --- BARRA LATERAL ---
with st.sidebar:
    archivo_subido = st.file_uploader("Subí el archivo Excel (.xlsx)", type=["xlsx"])
    nombre_empresa, dia_cierre, mes_cierre, leyenda_ipc = "Empresa no identificada", 31, 12, ""

    if archivo_subido is not None:
        try:
            df_empresa_raw = pd.read_excel(archivo_subido, sheet_name="Datos Empresa", header=None)
            dict_empresa = dict(zip(df_empresa_raw[0].astype(str).str.strip(), df_empresa_raw[1]))
            nombre_empresa = dict_empresa.get("Empresa", "Empresa Registrada")
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
        ultimo_año_base = int(max(lista_años))
        fecha_ultimo_balance = f"{dia_cierre:02d}/{mes_cierre:02d}/{ultimo_año_base}"
        fecha_proximo_cierre = f"{dia_cierre:02d}/{mes_cierre:02d}/{ultimo_año_base + 1}"

        st.markdown("---")
        año_seleccionado = st.selectbox("Ejercicio Económico:", options=sorted(lista_años, reverse=True), index=0)
        rango_años = st.slider("Tendencia Histórica:", min_value=int(min(lista_años)), max_value=int(max(lista_años)), value=(int(min(lista_años)), int(max(lista_años))))
        
        st.markdown("---")
        solapa_seleccionada = st.radio("Seleccioná el Reporte:", options=["🏠 Resumen Ejecutivo", "🏛️ Estructura Patrimonial", "💧 Liquidez y Solvencia", "🔄 Ciclo Operativo", "📈 Rentabilidad y Margenes"])
        st.markdown("---")
        if leyenda_ipc: st.caption(f"ℹ️ {leyenda_ipc}")
        st.caption(f"📅 **Último balance:** {fecha_ultimo_balance}")
        st.caption(f"⏳ **Próximo cierre:** {fecha_proximo_cierre}")

# --- PROCESAMIENTO Y CUERPO ---
if archivo_subido is not None:
    df_rubros_raw = pd.read_excel(archivo_subido, sheet_name="Rubros Grales", header=None)
    fila_inicio = df_rubros_raw[df_rubros_raw[0] == 'Sub Rubro'].index[0]
    df_mapeo = df_rubros_raw.iloc[fila_inicio+1:].dropna(subset=[0, 1]).copy()
    df_mapeo.columns = ['Sub Rubro', 'Cuenta']
    
    def sumar_sub_rubro(df_datos, df_map, sub_rubro_nombre):
        cuentas = df_map[df_map['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
        cuentas_existing = [c for c in cuentas if c in df_datos.columns]
        return df_datos[cuentas_existing].sum(axis=1) if cuentas_existing else pd.Series(0, index=df_datos.index)

    # Motor de Cálculos
    act_corr = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo Corriente')
    act_ncorr = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo No Corriente')
    pas_corr = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo Corriente')
    pas_ncorr = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo no Corriente')
    pn = sumar_sub_rubro(df_pivot, df_mapeo, 'Patrimonio Neto')
    ventas = df_pivot.get('ventas', pd.Series(0, index=df_pivot.index))
    res_neto = df_pivot.get('Resultado Neto', pd.Series(0, index=df_pivot.index))
    ebitda = res_neto + df_pivot.get('Amortizacion', 0) + df_pivot.get('Intereses Financieros', 0) + df_pivot.get('impuesto a las gs', 0)
    
    # Ratios
    df_kpis = pd.DataFrame({
        'Activo Corriente': act_corr / 1e6, 'Activo No Corriente': act_ncorr / 1e6, 'Activo Total': (act_corr + act_ncorr) / 1e6,
        'Pasivo Corriente': pas_corr / 1e6, 'Pasivo No Corriente': pas_ncorr / 1e6, 'Pasivo Total': (pas_corr + pas_ncorr) / 1e6,
        'Patrimonio Neto': pn / 1e6, 'Endeudamiento': (pas_corr + pas_ncorr) / pn.replace(0, pd.NA),
        'Liquidez Corriente': act_corr / pas_corr.replace(0, pd.NA), 
        'Prueba Acida': (df_pivot.get('activo liquido', 0) + df_pivot.get('creditos comerciales', 0)) / pas_corr.replace(0, pd.NA),
        'Capital de Trabajo': (act_corr - pas_corr) / 1e6,
        'Solvencia': (act_corr + act_ncorr) / (pas_corr + pas_ncorr).replace(0, pd.NA),
        'Garantia': pn / (pas_corr + pas_ncorr).replace(0, pd.NA),
        'Ventas': ventas / 1e6, 'Resultado Neto': res_neto / 1e6, 'EBITDA Proxy': ebitda / 1e6,
        'Margen Neto (%)': (res_neto / ventas.replace(0, pd.NA)) * 100,
        'ROE (%)': (res_neto / pn.replace(0, pd.NA)) * 100,
        'Rotacion Activos': ventas / (act_corr + act_ncorr).replace(0, pd.NA),
        'Dias Cobro': (df_pivot.get('creditos comerciales', 0) / ventas.replace(0, pd.NA)) * 365,
        'Dias Inventario': (df_pivot.get('Bienes de cambio', 0) / pd.Series(np.where(df_pivot.get('Costo Mercaderia Vendida', 0)==0, ventas, df_pivot.get('Costo Mercaderia Vendida', 0)), index=df_pivot.index).replace(0, pd.NA)) * 365,
        'Dias Pago': (df_pivot.get('Deudas comerciales', 0) / pd.Series(np.where(df_pivot.get('Costo Mercaderia Vendida', 0)==0, ventas, df_pivot.get('Costo Mercaderia Vendida', 0)), index=df_pivot.index).replace(0, pd.NA)) * 365,
        'Efecto Palanca': (res_neto/pn.replace(0,pd.NA)) / ((res_neto + df_pivot.get('Intereses Financieros', 0))/(pn + pas_ncorr).replace(0,pd.NA)).replace(0,pd.NA)
    }).round(2)

    datos_año = df_kpis.loc[año_seleccionado]
    df_filtrado = df_kpis.loc[rango_años[0]:rango_años[1]]
    lista_desc = sorted(lista_años, reverse=True)
    idx_desc = lista_desc.index(año_seleccionado)
    datos_año_ant = df_kpis.loc[lista_desc[idx_desc + 1]] if idx_desc < len(lista_desc) - 1 else None

    def get_delta(col, unidad=""):
        return calc_delta(datos_año[col], datos_año_ant[col], unidad) if datos_año_ant is not None else None

    # --- STICKY HEADER ---
    st.markdown(f'<div class="sticky-header" style="text-align: center;"><h2 style="margin:0; color:{COLOR_PN};">🏢 {nombre_empresa} | Tablero de Control</h2><p style="margin:0; color:#64748B;">{solapa_seleccionada} | Ejercicio: {año_seleccionado}</p></div>', unsafe_allow_html=True)

    # --- ENRUTADOR DE CONTENIDO ---
    if solapa_seleccionada == "🏠 Resumen Ejecutivo":
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M", delta=get_delta('Ventas', 'M'))
        c2.metric(f"{semaforo(datos_año['Resultado Neto'], 'Resultado')} Resultado Neto", f"$ {datos_año['Resultado Neto']:,.2f} M", delta=get_delta('Resultado Neto', 'M'))
        c3.metric("📊 EBITDA Proxy", f"$ {datos_año['EBITDA Proxy']:,.2f} M", delta=get_delta('EBITDA Proxy', 'M'))
        
        c4, c5, c6 = st.columns(3)
        c4.metric(f"{semaforo(datos_año['ROE (%)'], 'ROE')} ROE", f"{datos_año['ROE (%)']:.2f}%", delta=get_delta('ROE (%)', '%'))
        c5.metric(f"{semaforo(datos_año['Margen Neto (%)'], 'Margen Neto')} Margen Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=get_delta('Margen Neto (%)', '%'))
        c6.metric(f"{semaforo(datos_año['Liquidez Corriente'], 'Liquidez Corriente')} Liquidez", f"{datos_año['Liquidez Corriente']:.2f}", delta=get_delta('Liquidez Corriente', 'x'))

        col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
        with col_r2:
            st.markdown("<p style='text-align:center; font-weight:bold; margin-top:20px;'>🎯 Radar de Desempeño (Dimensiones Normalizadas)</p>", unsafe_allow_html=True)
            cat = ['Liquidez', 'Solvencia', 'Margen', 'ROE', 'Endeudamiento']
            val_radar = [min(datos_año['Liquidez Corriente']*20,100), min(datos_año['Solvencia']*20,100), max(min(datos_año['Margen Neto (%)']*3,100),0), max(min(datos_año['ROE (%)']*2,100),0), max(min((2/(datos_año['Endeudamiento']+0.1))*50,100),0)]
            fig_radar = go.Figure(go.Scatterpolar(r=val_radar + [val_radar[0]], theta=cat + [cat[0]], fill='toself', fillcolor='rgba(100, 130, 161, 0.2)', line=dict(color=COLOR_PN, width=2)))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)), showlegend=False, height=400, margin=dict(t=40, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_radar, use_container_width=True)
            if st.button("🔍 Ampliar Radar de Diagnóstico", key="btn_radar_exec", use_container_width=True): mostrar_grafico_ampliado(fig_radar)
        
        insertar_boton_impresion()
        st.info("**💡 Interpretación:** El radar muestra el equilibrio de la firma. Un polígono amplio y simétrico indica una gestión saludable en todas las áreas core.")

    elif solapa_seleccionada == "🏛️ Estructura Patrimonial":
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("📊 Activo Total", f"$ {datos_año['Activo Total']:,.2f} M", delta=get_delta('Activo Total', 'M'))
        col_a2.metric("🟢 Activo Corriente", f"$ {datos_año['Activo Corriente']:,.2f} M", delta=get_delta('Activo Corriente', 'M'))
        col_a3.metric("🟢 Activo No Corriente", f"$ {datos_año['Activo No Corriente']:,.2f} M", delta=get_delta('Activo No Corriente', 'M'))
        
        st.write("")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("🔵 Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M", delta=get_delta('Patrimonio Neto', 'M'))
        col_m2.metric("🟠 Pasivo Total", f"$ {datos_año['Pasivo Total']:,.2f} M", delta=get_delta('Pasivo Total', 'M'), delta_color="inverse")
        col_m3.metric(f"{semaforo(datos_año['Endeudamiento'], 'Endeudamiento')} Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}", delta=get_delta('Endeudamiento', 'x'), delta_color="inverse")
        
        st.write("")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Bar(x=['Inversión'], y=[datos_año['Activo No Corriente']], name='Act. No Corr.', marker_color=COLOR_ACT_NOCORR, texttemplate="$ %{y:.2f}M", textposition='inside'))
        fig_eq.add_trace(go.Bar(x=['Inversión'], y=[datos_año['Activo Corriente']], name='Act. Corr.', marker_color=COLOR_ACT_CORR, texttemplate="$ %{y:.2f}M", textposition='inside'))
        fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[datos_año['Patrimonio Neto']], name='PN', marker_color=COLOR_PN, texttemplate="$ %{y:.2f}M", textposition='inside'))
        fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[datos_año['Pasivo No Corriente']], name='Pas. No Corr.', marker_color=COLOR_PAS_NOCORR, texttemplate="$ %{y:.2f}M", textposition='inside'))
        fig_eq.add_trace(go.Bar(x=['Fondeo'], y=[datos_año['Pasivo Corriente']], name='Pas. Corr.', marker_color=COLOR_PAS_CORR, texttemplate="$ %{y:.2f}M", textposition='inside'))
        
        # RESTAURADO: Se quitan los ejes y grillas laterales por completo
        fig_eq.update_layout(
            barmode='stack', bargap=0.1, showlegend=False, height=450, 
            margin=dict(t=20, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, showline=False),
            yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False)
        )
        
        col_eq_izq, col_eq_centro, col_eq_der = st.columns([1, 2, 1])
        with col_eq_centro:
            st.markdown("<p style='text-align: center; font-weight: bold;'>📋 Estructura Patrimonial</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_eq, use_container_width=True)
            if st.button("🔍 Ampliar Estructura Patrimonial", key="btn_amp_patr", use_container_width=True): mostrar_grafico_ampliado(fig_eq)

        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            fig1 = go.Figure([go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo Corriente'], name='Pas. Corr.', marker_color=COLOR_PAS_CORR), go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo No Corriente'], name='Pas. No Corr.', marker_color=COLOR_PAS_NOCORR), go.Bar(x=df_filtrado.index, y=df_filtrado['Patrimonio Neto'], name='PN', marker_color=COLOR_PN)])
            fig1.update_layout(title="Evolución Pasivo + PN", barmode='stack', height=350, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
            if st.button("🔍 Ampliar Evolución Fondeo", key="btn_amp_fond"): mostrar_grafico_ampliado(fig1)
        with c2:
            fig2 = go.Figure([go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Act. Corr.', marker_color=COLOR_ACT_CORR), go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Act. No Corr.', marker_color=COLOR_ACT_NOCORR)])
            fig2.update_layout(title="Evolución de los Activos", barmode='stack', height=350, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)
            if st.button("🔍 Ampliar Evolución Activos", key="btn_amp_act"): mostrar_grafico_ampliado(fig2)
        
        insertar_boton_impresion()
        st.info("**💡 Guía:** El bloque de Inversión debe estar calzado por Fondeo genuino. El endeudamiento mide la dependencia de terceros.")

    elif solapa_seleccionada == "💧 Liquidez y Solvencia":
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("💧 Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}", delta=get_delta('Liquidez Corriente', 'x'))
        col_m5.metric("💧 Prueba Ácida", f"{datos_año['Prueba Acida']:.2f}", delta=get_delta('Prueba Acida', 'x'))
        col_m6.metric("📊 Cap. de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M", delta=get_delta('Capital de Trabajo', 'M'))

        c1, c2 = st.columns(2)
        with c1:
            fig_l = go.Figure([go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], name='Liquidez', line=dict(color=COLOR_ACT_CORR, width=3)), go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], name='Ácida', line=dict(color=COLOR_PN, dash='dot'))])
            fig_l.add_hline(y=1.0, line_dash="dash", line_color=COLOR_PAS_NOCORR)
            fig_l.update_layout(title="Tendencia de Liquidez", height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_l, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico Liquidez", key="btn_amp_liq"): mostrar_grafico_ampliado(fig_l)
        with c2:
            fig_s = go.Figure([go.Scatter(x=df_filtrado.index, y=df_filtrado['Solvencia'], name='Solvencia', line=dict(color=COLOR_PN, width=3)), go.Scatter(x=df_filtrado.index, y=df_filtrado['Garantia'], name='Garantía', line=dict(color=COLOR_ACT_NOCORR, dash='dash'))])
            fig_s.update_layout(title="Respaldo y Solvencia", height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_s, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico Solvencia", key="btn_amp_solv"): mostrar_grafico_ampliado(fig_s)
        
        insertar_boton_impresion()

    elif solapa_seleccionada == "🔄 Ciclo Operativo":
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("⏱️ Cobranza", f"{datos_año['Dias Cobro']:.0f} días", delta=get_delta('Dias Cobro', 'días'), delta_color="inverse")
        col_r2.metric("⏱️ Stock", f"{datos_año['Dias Inventario']:.0f} días", delta=get_delta('Dias Inventario', 'días'), delta_color="inverse")
        col_r3.metric("⏱️ Pago", f"{datos_año['Dias Pago']:.0f} días", delta=get_delta('Dias Pago', 'días'))

        c1, c2 = st.columns(2)
        with c1:
            fig_c = go.Figure([go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Cobro'], name='Cobro', line=dict(color=COLOR_PN)), go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Inventario'], name='Stock', line=dict(color=COLOR_ACT_CORR)), go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Pago'], name='Pago', line=dict(color=COLOR_PAS_CORR, dash='dash'))])
            fig_c.update_layout(title="Ciclo Operativo (Días)", yaxis=dict(range=[0, 365]), height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_c, use_container_width=True)
            if st.button("🔍 Ampliar Ciclos", key="btn_amp_ciclo"): mostrar_grafico_ampliado(fig_c)
        with c2:
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Total'], mode='lines+markers', name='Rot. Activo Total', line=dict(color=COLOR_ACT_NOCORR, width=3)))
            fig_r.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Corriente'], mode='lines+markers', name='Rot. Activo Corriente', line=dict(color=COLOR_ACT_CORR, width=2, dash='dash')))
            fig_r.update_layout(title="Intensidad de Rotación (Veces)", hovermode="x unified", height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_r, use_container_width=True)
            if st.button("🔍 Ampliar Rotación", key="btn_amp_rot"): mostrar_grafico_ampliado(fig_r)
        
        insertar_boton_impresion()

    elif solapa_seleccionada == "📈 Rentabilidad y Margenes":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📊 Ventas", f"$ {datos_año['Ventas']:,.2f} M", delta=get_delta('Ventas', 'M'))
        c2.metric("📊 Margen Neto", f"{datos_año['Margen Neto (%)']:.2f}%", delta=get_delta('Margen Neto (%)', '%'))
        c3.metric("📊 ROE", f"{datos_año['ROE (%)']:.2f}%", delta=get_delta('ROE (%)', '%'))
        c4.metric("📊 Palanca", f"{datos_año['Efecto Palanca']:.2f}x", delta=get_delta('Efecto Palanca', 'x'))

        # RESTAURADO: Se inyectan las dos gráficas de evolución de ventas y EBITDA perdidas
        st.write("")
        col_t3a, col_t3b = st.columns(2)
        with col_t3a:
            fig_ventas = go.Figure()
            fig_ventas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Ventas'], name='Ventas', marker_color=COLOR_VENTAS, yaxis='y'))
            fig_ventas.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%)', yaxis='y2', line=dict(color=COLOR_ACT_CORR, width=3)))
            fig_ventas.update_layout(title="Ventas vs Margen Neto Final", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ventas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Ventas", key="btn_amp_vts_rent", use_container_width=True): mostrar_grafico_ampliado(fig_ventas)
            
        with col_t3b:
            fig_rent = go.Figure()
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='EBITDA', marker_color=COLOR_PN))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto', marker_color=COLOR_ACT_NOCORR))
            fig_rent.update_layout(title="EBITDA vs Resultado Neto Real", barmode='group', height=400, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_rent, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Caja", key="btn_amp_caja_rent", use_container_width=True): mostrar_grafico_ampliado(fig_rent)
            
        st.write("---")

        # Gráfico DuPont (Con su respectivo botón de ampliación conectado)
        fig_d = go.Figure()
        fig_d.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], name='ROE %', line=dict(color=COLOR_PN, width=4)))
        fig_d.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], name='Margen %', line=dict(color=COLOR_ACT_CORR, dash='dash')))
        fig_d.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activos'], name='Rotación (Der)', yaxis='y2', line=dict(color=COLOR_PAS_CORR)))
        fig_d.update_layout(title="🎯 Descomposición DuPont", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=450, legend=config_leyenda_abajo, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_d, use_container_width=True)
        if st.button("🔍 Ampliar Análisis DuPont", key="btn_amp_dupont", use_container_width=True): mostrar_grafico_ampliado(fig_d)
        
        insertar_boton_impresion()
        st.info("**💡 Guía de Interpretación DuPont:** Desarma el ROE para revelar la verdadera palanca de la rentabilidad: Eficiencia en Costos (Margen), Eficacia Operativa (Rotación) o Apalancamiento Financiero (Estructura de Fondeo).")
else:
    st.info("👆 Por favor, abrí el panel de la barra lateral izquierda y subí el archivo Excel (.xlsx) para comenzar el análisis.")
