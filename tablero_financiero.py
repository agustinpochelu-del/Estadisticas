import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Tablero de Análisis Integral", layout="wide")

# --- FUNCIÓN DE PANTALLA COMPLETA (POP-UP) ---
@st.dialog("🔍 Vista Ampliada del Análisis", width="large")
def mostrar_grafico_ampliado(figura):
    fig_xl = go.Figure(figura)
    fig_xl.update_layout(height=650)
    st.plotly_chart(fig_xl, use_container_width=True)

# ESTRUCTURA REUTILIZABLE PARA LEYENDAS INFERIORES CENTRADAS
config_leyenda_abajo = dict(
    orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5
)

# --- INYECCIÓN DE CSS PARA CABECERA FLOTANTE FIJA (STICKY HEADER) ---
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlock"] > div:has(div.sticky-header) {
        position: sticky;
        top: 2.875rem;
        background-color: white;
        z-index: 999;
        border-bottom: 1px solid #f0f2f6;
        padding-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- BARRA LATERAL (SIDEBAR): CONTROL TOTAL DE LA APLICACIÓN ---
with st.sidebar:
    archivo_subido = st.file_uploader("Subí el archivo Excel (.xlsx)", type=["xlsx"])
    
    nombre_empresa = "Empresa no identificada"
    cuit_empresa = ""
    domicilio_empresa = ""
    cierre_empresa = ""
    leyenda_ipc = ""

    if archivo_subido is not None:
        # --- LECTURA AUTOMÁTICA DE DATOS DE LA EMPRESA ---
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
        except Exception:
            pass

        # --- EXTRACCIÓN DE LA ÚLTIMA FECHA DE IPC ---
        try:
            df_ipc = pd.read_excel(archivo_subido, sheet_name="IPC")
            df_ipc['MES'] = pd.to_datetime(df_ipc['MES'])
            df_ipc_valido = df_ipc.dropna(subset=['IPC NACIONAL EMPALME IPIM'])
            if not df_ipc_valido.empty:
                ultima_fecha_ipc = df_ipc_valido['MES'].max()
                meses_es = {
                    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
                }
                mes_palabra = meses_es[ultima_fecha_ipc.month]
                año_ipc = ultima_fecha_ipc.year
                leyenda_ipc = f"Los datos monetarios están actualizados al {mes_palabra} de {año_ipc}"
        except Exception:
            pass

        # --- PROCESAMIENTO BASE PARA SELECTORES ---
        df_historico = pd.read_excel(archivo_subido, sheet_name="Balances Historicos")
        df_pivot = df_historico.groupby(['Periodo', 'Cuenta'])['Saldos Ajustados'].sum().unstack(fill_value=0)
        lista_años = sorted(df_pivot.index.tolist())

        st.markdown("---")
        año_seleccionado = st.selectbox(
            "Ejercicio Económico:",
            options=sorted(lista_años, reverse=True),
            index=0
        )
        
        rango_años = st.slider(
            "Tendencia Histórica:",
            min_value=int(min(lista_años)),
            max_value=int(max(lista_años)),
            value=(int(min(lista_años)), int(max(lista_años)))
        )
        
        st.markdown("---")
        solapa_seleccionada = st.radio(
            "Seleccioná la sección:",
            options=[
                "🏛️ Estructura Patrimonial", 
                "💧 Liquidez y Corto Plazo", 
                "🔄 Rotaciones y Ciclos",
                "📈 Rentabilidad Económica"
            ]
        )
        st.markdown("---")
        if leyenda_ipc:
            st.caption(f"ℹ️ {leyenda_ipc}")
        if cierre_empresa:
            st.caption(f"📅 Cierre: {cierre_empresa}")


# --- CUERPO PRINCIPAL TOTALMENTE DEDICADO AL INFORME ---
if archivo_subido is not None:
    # --- MOTOR DE CÁLCULOS PRINCIPALES ---
    df_rubros_raw = pd.read_excel(archivo_subido, sheet_name="Rubros Grales", header=None)
    try:
        fila_inicio = df_rubros_raw[df_rubros_raw[0] == 'Sub Rubro'].index[0]
        df_mapeo = df_rubros_raw.iloc[fila_inicio+1:].dropna(subset=[0, 1]).copy()
        df_mapeo.columns = ['Sub Rubro', 'Cuenta']
        df_mapeo['Sub Rubro'] = df_mapeo['Sub Rubro'].astype(str).str.strip()
        df_mapeo['Cuenta'] = df_mapeo['Cuenta'].astype(str).str.strip()
    except Exception:
        st.error("⚠️ Error en la solapa 'Rubros Grales'. Verificá la tabla de mapeo.")
        st.stop()

    def sumar_sub_rubro(df_datos, df_map, sub_rubro_nombre):
        cuentas = df_map[df_map['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
        cuentas_existing = [c for c in cuentas if c in df_datos.columns]
        if not cuentas_existing:
            return pd.Series(0, index=df_datos.index)
        return df_datos[cuentas_existing].sum(axis=1)

    # Variables y Ratios
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
    
    num_palanca = resultado_neto / patrimonio_neto.replace(0, pd.NA)
    den_palanca = (resultado_neto + df_pivot.get('Intereses Financieros', 0)) / (patrimonio_neto + pasivo_no_corriente).replace(0, pd.NA)
    efecto_palanca = num_palanca / den_palanca.replace(0, pd.NA)
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

    bienes_de_uso = df_pivot.get('Bienes de Uso', pd.Series(0, index=df_pivot.index))
    bienes_de_cambio = df_pivot.get('Bienes de cambio', pd.Series(0, index=df_pivot.index))
    deudas_comerciales = df_pivot.get('Deudas comerciales', pd.Series(0, index=df_pivot.index))
    cmv = df_pivot.get('Costo Mercaderia Vendida', pd.Series(0, index=df_pivot.index))
    cmv_seguro = np.where(cmv == 0, ventas, cmv)

    rot_activo_total = ventas / activo_total.replace(0, pd.NA)
    rot_activo_corriente = ventas / activo_corriente.replace(0, pd.NA)
    rot_bienes_uso = ventas / bienes_de_uso.replace(0, pd.NA)
    rot_inventarios = cmv_seguro / bienes_de_cambio.replace(0, pd.NA)

    dias_cobro = (creditos_comerciales_puros / ventas.replace(0, pd.NA)) * 365
    dias_inventario = (bienes_de_cambio / pd.Series(cmv_seguro, index=df_pivot.index).replace(0, pd.NA)) * 365
    dias_pago = (deudas_comerciales / pd.Series(cmv_seguro, index=df_pivot.index).replace(0, pd.NA)) * 365

    # Estructura de Datos Consolidada
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
        'Rotacion Bienes Uso': rot_bienes_uso, 'Rotacion Inventarios': rot_inventarios,
        'Dias Cobro': dias_cobro, 'Dias Inventario': dias_inventario, 'Dias Pago': dias_pago
    }).dropna(how='all').round(2)

    datos_año = df_kpis.loc[año_seleccionado]
    df_filtrado = df_kpis.loc[rango_años[0]:rango_años[1]]

    # --- CONTENEDOR DE TÍTULO FIJO / STICKY HEADER ---
    st.markdown(
        f"""
        <div class="sticky-header">
            <h2 style='margin: 0; font-size: 24px;'>🏢 {nombre_empresa} | Tablero de Control Financiero</h2>
            <p style='margin: 0; color: #666; font-size: 14px;'>{solapa_seleccionada} | Ejercicio Seleccionado: {año_seleccionado}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.write("")

    # --- ENRUTADOR DE CONTENIDO ---
    if solapa_seleccionada == "🏛️ Estructura Patrimonial":
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("Activo Total", f"$ {datos_año['Activo Total']:,.2f} M")
        col_a2.metric("Activo Corriente", f"$ {datos_año['Activo Corriente']:,.2f} M")
        col_a3.metric("Activo No Corriente", f"$ {datos_año['Activo No Corriente']:,.2f} M")
        
        st.write("")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M")
        col_m2.metric("Pasivo Total", f"$ {datos_año['Pasivo Total']:,.2f} M")
        col_m3.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}")
        
        st.write("")
        fig_eq = go.Figure()
        
        # Gráfico corregido sin leyendas extensas en el eje X
        fig_eq.add_trace(go.Bar(
            x=['Activo'], y=[datos_año['Activo No Corriente']], 
            name='Activo No Corriente', marker_color='#a1d99b', 
            text=[datos_año['Activo No Corriente']], texttemplate="<b>Activo No Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2))
        ))
        fig_eq.add_trace(go.Bar(
            x=['Activo'], y=[datos_año['Activo Corriente']], 
            name='Activo Corriente', marker_color='#2ca02c', 
            text=[datos_año['Activo Corriente']], texttemplate="<b>Activo Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2))
        ))
        fig_eq.add_trace(go.Bar(
            x=['Pasivo + PN'], y=[datos_año['Patrimonio Neto']], 
            name='Patrimonio Neto', marker_color='#1f77b4', 
            text=[datos_año['Patrimonio Neto']], texttemplate="<b>Patrimonio Neto</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2))
        ))
        fig_eq.add_trace(go.Bar(
            x=['Pasivo + PN'], y=[datos_año['Pasivo No Corriente']], 
            name='Pasivo No Corriente', marker_color='#ffbb78', 
            text=[datos_año['Pasivo No Corriente']], texttemplate="<b>Pasivo No Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2))
        ))
        fig_eq.add_trace(go.Bar(
            x=['Pasivo + PN'], y=[datos_año['Pasivo Corriente']], 
            name='Pasivo Corriente', marker_color='#ff7f0e', 
            text=[datos_año['Pasivo Corriente']], texttemplate="<b>Pasivo Corriente</b><br>$ %{text:.2f} M", textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2))
        ))
        
        fig_eq.update_layout(barmode='stack', bargap=0, showlegend=False, height=420, margin=dict(t=10, b=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        
        col_eq_izq, col_eq_centro, col_eq_der = st.columns([1, 2, 1])
        with col_eq_centro:
            st.markdown("<p style='text-align: center; font-weight: bold;'>📋 Esquema del Balance</p>", unsafe_allow_html=True)
            st.plotly_chart(fig_eq, use_container_width=True)
            if st.button("🔍 Ampliar Esquema del Balance", key="btn_eq", use_container_width=True):
                mostrar_grafico_ampliado(fig_eq)

        st.write("")
        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            fig_pas = go.Figure()
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo Corriente'], name='Pasivo Corto Plazo', marker_color='#ff7f0e'))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo No Corriente'], name='Pasivo Largo Plazo', marker_color='#d62728'))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Patrimonio Neto'], name='Patrimonio Neto', marker_color='#1f77b4'))
            fig_pas.update_layout(title="Evolución del Fondeo Histórico (Pasivo + PN)", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_pas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Fondeo", key="btn_pas", use_container_width=True):
                mostrar_grafico_ampliado(fig_pas)
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c'))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente', marker_color='#8c564b'))
            fig_act.update_layout(title="Evolución de la Inversión Histórica (Activos)", barmode='stack', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Inversión", key="btn_act", use_container_width=True):
                mostrar_grafico_ampliado(fig_act)

        st.info("""
        **💡 Guía de Interpretación Patrimonial:**
        - **Estructura de Bloques:** Refleja la partida doble ($A = P + PN$). Permite evaluar de un vistazo si las inversiones de largo plazo (Bienes de Uso) están calzadas con fondeo genuino.
        - **Índice de Endeudamiento (Pasivo / PN):** Evalúa la dependencia financiera de terceros. Mide cuántos pesos de deuda externa tiene la firma por cada peso de capital propio de los socios.
        """)

    elif solapa_seleccionada == "💧 Liquidez y Corto Plazo":
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}")
        col_m5.metric("Prueba Ácida (Filtrada)", f"{datos_año['Prueba Acida']:.2f}")
        col_m6.metric("Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M")
        
        st.write("")
        col_m11, col_m12, col_m13 = st.columns(3)
        col_m11.metric("Índice de Solvencia", f"{datos_año['Solvencia']:.2f}")
        col_m12.metric("Índice de Garantía", f"{datos_año['Garantia']:.2f}")
        col_m13.metric("Efecto Palanca (GAF)", f"{datos_año['Efecto Palanca']:.2f}x")
        
        st.write("")
        col_t2a, col_t2b = st.columns(2)
        with col_t2a:
            fig_liq = go.Figure()
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_hline(y=1.0, line_dash="dash", line_color="red")
            fig_liq.update_layout(title="Evolución Histórica de los Índices de Liquidez", hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_liq, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Liquidez", key="btn_liq", use_container_width=True):
                mostrar_grafico_ampliado(fig_liq)
        with col_t2b:
            fig_solv = go.Figure()
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Solvencia'], mode='lines+markers', name='Solvencia', line=dict(width=3, color='#bcbd22')))
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Garantia'], mode='lines+markers', name='Garantía', line=dict(width=3, color='#1f77b4', dash='dash')))
            fig_solv.update_layout(title="Evolución de Solvencia y Respaldo", hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_solv, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Solvencia", key="btn_solv", use_container_width=True):
                mostrar_grafico_ampliado(fig_solv)

        st.info("""
        **💡 Guía de Interpretación de Liquidez y Cobertura:**
        - **Liquidez Corriente:** Capacidad de cobertura de compromisos inmediatos. Valores menores a 1.0 alertan posibles tensiones de caja en el corto plazo.
        - **Prueba Ácida Filtrada:** Excluye rigurosamente inventarios y créditos fiscales. Mide el verdadero respaldo monetario neto y los créditos de cobranza pura frente al pasivo comercial exigible.
        - **Efecto Palanca (GAF):** Un índice mayor a 1.0 indica un apalancamiento financiero positivo: el costo del capital de terceros es menor que la rentabilidad operativa del negocio.
        """)

    elif solapa_seleccionada == "🔄 Rotaciones y Ciclos":
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Plazo Medio de Cobranza", f"{datos_año['Dias Cobro']:.0f} días")
        col_r2.metric("Días de Stock (Inventario)", f"{datos_año['Dias Inventario']:.0f} días")
        col_r3.metric("Plazo Medio de Pago", f"{datos_año['Dias Pago']:.0f} días")
        
        st.write("")
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            st.markdown("##### ⏱️ Evolución Temporal del Ciclo Operativo (Días)")
            fig_ciclos = go.Figure()
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Cobro'], mode='lines+markers', name='Plazo Cobro', line=dict(color='#1f77b4', width=3), hovertemplate="%{y:.2f} días<extra></extra>"))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Inventario'], mode='lines+markers', name='Plazo Stock', line=dict(color='#ff7f0e', width=3), hovertemplate="%{y:.2f} días<extra></extra>"))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Pago'], mode='lines+markers', name='Plazo Pago', line=dict(color='#d62728', width=3, dash='dash'), hovertemplate="%{y:.2f} días<extra></extra>"))
            fig_ciclos.update_layout(yaxis=dict(range=[0, 365], showgrid=True), hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_ciclos, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Ciclos", key="btn_ciclos_ampliar", use_container_width=True):
                mostrar_grafico_ampliado(fig_ciclos)
        with col_tr2:
            st.markdown("##### 🔄 Intensidad de Rotación de Activos (Veces)")
            fig_rot_act = go.Figure()
            fig_rot_act.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Total'], mode='lines+markers', name='Rot. Activo Total', line=dict(color='#2ca02c', width=3), hovertemplate="%{y:.2f}x<extra></extra>"))
            fig_rot_act.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Corriente'], mode='lines+markers', name='Rot. Activo Corriente', line=dict(color='#9467bd', width=2, dash='dash'), hovertemplate="%{y:.2f}x<extra></extra>"))
            fig_rot_act.update_layout(hovermode="x unified", height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rot_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Rotaciones", key="btn_rot_ampliar", use_container_width=True):
                mostrar_grafico_ampliado(fig_rot_act)

        st.info("""
        **💡 Guía de Interpretación de Ciclos Operativos y Rotación:**
        - **Déficit Estructural de Giro:** Si la suma de *Plazo de Cobro + Días de Stock* excede con holgura los *Días de Pago*, la empresa genera un descalce financiero que consume recursos líquidos propios.
        - **Rotación de Activo Corriente:** Determina la cantidad de veces que el capital operativo "da la vuelta" en el año fiscal para materializar las ventas registradas.
        """)

    elif solapa_seleccionada == "📈 Rentabilidad Económica":
        col_m7, col_m8, col_m9, col_m10 = st.columns(4)
        col_m7.metric("Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M")
        col_m8.metric("Margen EBITDA", f"{datos_año['Margen EBITDA (%)']:.2f}%")
        col_m9.metric("Rentabilidad s/ Ventas", f"{datos_año['Margen Neto (%)']:.2f}%")
        col_m10.metric("ROE Final", f"{datos_año['ROE (%)']:.2f}%")
        
        st.write("")
        col_t3a, col_t3b = st.columns(2)
        with col_t3a:
            fig_ventas = go.Figure()
            fig_ventas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Ventas'], name='Ventas', marker_color='#17becf', yaxis='y'))
            fig_ventas.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%)', yaxis='y2', line=dict(color='#ff7f0e', width=3)))
            fig_ventas.update_layout(title="Ventas vs Margen Neto Final", yaxis2=dict(overlaying='y', side='right', showgrid=False), height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_ventas, use_container_width=True)
        with col_t3b:
            fig_rent = go.Figure()
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='EBITDA', marker_color='#bcbd22'))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto', marker_color='#2ca02c'))
            fig_rent.update_layout(title="EBITDA vs Resultado Neto Real", barmode='group', height=400, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rent, use_container_width=True)

        st.write("")
        st.markdown("---")
        st.subheader(f"🎯 Drivers del Rendimiento (Esquema DuPont)")
        fig_dupont_rent = go.Figure()
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], mode='lines+markers', name='ROE (%) [Eje Izq]', line=dict(color='#e377c2', width=4), hovertemplate="%{y:.2f}%<extra></extra>"))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%) [Eje Izq]', line=dict(color='#ff7f0e', width=2, dash='dash'), hovertemplate="%{y:.2f}%<extra></extra>"))
        fig_dupont_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Rotacion Activos'], mode='lines+markers', name='Rotación Activos [Eje Der]', yaxis='y2', line=dict(color='#2ca02c', width=2), hovertemplate="%{y:.2f}x<extra></extra>"))
        fig_dupont_rent.update_layout(title="Evolución Histórica de Componentes DuPont", yaxis2=dict(overlaying='y', side='right', showgrid=False), hovermode="x unified", height=450, legend=config_leyenda_abajo)
        st.plotly_chart(fig_dupont_rent, use_container_width=True)
        if st.button("🔍 Ampliar Gráfico DuPont", key="btn_dupont_rentabilidad", use_container_width=True):
            mostrar_grafico_ampliado(fig_dupont_rent)

        st.info("""
        **💡 Guía de Interpretación del Modelo DuPont:**
        Este esquema desarma estratégicamente el ROE para revelar cuál es la verdadera palanca que está empujando la rentabilidad del accionista, multiplicando tres frentes del negocio:
        1. **Eficiencia en Costos (Margen Neto):** Cuánto rinde cada peso de venta.
        2. **Eficacia Operativa (Rotación de Activos):** Cuántas veces se hace girar la estructura de inversión para generar esas ventas.
        3. **Apalancamiento (Multiplicador del Capital):** Cómo impacta el uso de deudas sobre el capital aportado.
        """)
else:
    st.info("👆 Por favor, abrí el panel de la barra lateral izquierda y subí el archivo Excel (.xlsx) para comenzar el análisis.")
