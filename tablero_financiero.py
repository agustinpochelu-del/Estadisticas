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
    
    # --- LECTURA DINÁMICA DE LA HOJA DE RUBROS GRALES ---
    df_rubros_raw = pd.read_excel(archivo_subido, sheet_name="Rubros Grales", header=None)
    
    try:
        fila_inicio = df_rubros_raw[df_rubros_raw[0] == 'Sub Rubro'].index[0]
        df_mapeo = df_rubros_raw.iloc[fila_inicio+1:].dropna(subset=[0, 1]).copy()
        df_mapeo.columns = ['Sub Rubro', 'Cuenta']
        df_mapeo['Sub Rubro'] = df_mapeo['Sub Rubro'].astype(str).str.strip()
        df_mapeo['Cuenta'] = df_mapeo['Cuenta'].astype(str).str.strip()
    except Exception as e:
        st.error("⚠️ No se encontró la tabla de mapeo ('Sub Rubro' y 'Cuenta') en la hoja 'Rubros Grales'.")
        st.stop()

    # Función motor para sumar dinámicamente las cuentas basándose en el mapeo de Excel
    def sumar_sub_rubro(df_datos, df_map, sub_rubro_nombre):
        cuentas = df_map[df_map['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
        cuentas_existing = [c for c in cuentas if c in df_datos.columns]
        if not cuentas_existing:
            return pd.Series(0, index=df_datos.index)
        return df_datos[cuentas_existing].sum(axis=1)

    # --- 2. MOTOR DE CÁLCULOS PRINCIPALES ---
    activo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo Corriente')
    activo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo No Corriente')
    activo_total = activo_corriente + activo_no_corriente
    
    pasivo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo Corriente')
    pasivo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo no Corriente')
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    
    patrimonio_neto = sumar_sub_rubro(df_pivot, df_mapeo, 'Patrimonio Neto')
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    # Prueba Ácida Estricta Acordada (Caja/Bancos + Clientes netos, sin créditos fiscales ni otros créditos)
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
    
    # Efecto Palanca Avanzado Acordada (GAF - Grado de Apalancamiento Financiero)
    num_palanca = resultado_neto / patrimonio_neto.replace(0, pd.NA)
    den_palanca = (resultado_neto + df_pivot.get('Intereses Financieros', 0)) / (patrimonio_neto + pasivo_no_corriente).replace(0, pd.NA)
    efecto_palanca = num_palanca / den_palanca.replace(0, pd.NA)
        
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

    # --- MOTOR DE CÁLCULOS: ROTACIONES Y CICLOS PROFESIONALES ---
    # 1. Extracción de Rubros del df_pivot (con salvavidas de ceros)
    activo_corriente = df_pivot.get('Activo Corriente', pd.Series(0, index=df_pivot.index))
    bienes_de_uso = df_pivot.get('Bienes de Uso', pd.Series(0, index=df_pivot.index))
    bienes_de_cambio = df_pivot.get('Bienes de cambio', pd.Series(0, index=df_pivot.index))
    deudas_comerciales = df_pivot.get('Deudas comerciales', pd.Series(0, index=df_pivot.index))
    
    # Cuenta de Resultados incorporada de tu Excel
    cmv = df_pivot.get('Costo Mercaderia Vendida', pd.Series(0, index=df_pivot.index))
    # Si en algún año viejo el CMV es cero, usamos Ventas temporalmente para ese año aislado
    cmv_seguro = np.where(cmv == 0, ventas, cmv)

    # 2. Ratios de Rotación (Veces al año)
    rot_activo_total = ventas / activo.replace(0, pd.NA)
    rot_activo_corriente = ventas / activo_corriente.replace(0, pd.NA)
    rot_bienes_uso = ventas / bienes_uso.replace(0, pd.NA) if 'bienes_uso' in locals() else (ventas / bienes_de_uso.replace(0, pd.NA))
    rot_inventarios = cmv_seguro / bienes_de_cambio.replace(0, pd.NA)

    # 3. Plazos Medios (Expresados en Días de calendario)
    dias_cobro = (creditos_comerciales_puros / ventas.replace(0, pd.NA)) * 365
    dias_inventario = (bienes_de_cambio / cmv_seguro.replace(0, pd.NA)) * 365
    dias_pago = (deudas_comerciales / cmv_seguro.replace(0, pd.NA)) * 365

    # Consolidación en DataFrame (Expresando valores monetarios en Millones)
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
        'Solvencia': solvencia,
        'Garantia': indice_garantia,
        'Efecto Palanca': efecto_palanca,
        'Ventas': ventas / 1e6, 
        'Resultado Neto': resultado_neto / 1e6, 
        'EBITDA Proxy': ebitda_proxy / 1e6,
        'Margen Neto (%)': margen_neto, 
        'Margen EBITDA (%)': margen_ebitda,
        'ROE (%)': roe, 
        'Rotacion Activos': rotacion_activos,
        'Rotacion Activo Total': rot_activo_total,
        'Rotacion Activo Corriente': rot_activo_corriente,
        'Rotacion Bienes Uso': rot_bienes_uso,
        'Rotacion Inventarios': rot_inventarios,
        'Dias Cobro': dias_cobro,
        'Dias Inventario': dias_inventario,
        'Dias Pago': dias_pago
        'Multiplicador Capital': multiplicador_capital
    }).dropna(how='all').round(2)

    # --- CONTROLES EN LA BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("🔍 Filtros del Tablero")
    
    lista_años = sorted(df_kpis.index.tolist())
    rango_años = st.sidebar.slider(
        "Seleccionar Período de Análisis:",
        min_value=int(min(lista_años)),
        max_value=int(max(lista_años)),
        value=(int(min(lista_años)), int(max(lista_años)))
    )
    
    df_filtrado = df_kpis.loc[rango_años[0]:rango_años[1]]
    
    año_seleccionado = st.sidebar.selectbox("📅 Ejercicio para análisis puntual:", df_filtrado.index.sort_values(ascending=False).tolist())
    datos_año = df_filtrado.loc[año_seleccionado]
    
    st.divider()
    
    # ESTRUCTURA REUTILIZABLE PARA LEYENDAS INFERIORES CENTRADAS (DA MÁS ESPACIO LATERAL)
    config_leyenda_abajo = dict(
        orientation="h",
        yanchor="top",
        y=-0.22,
        xanchor="center",
        x=0.5
    )
    
  # --- 3. ESTRUCTURA DE SOLAPAS ---
    tab1, tab2, tab_rotaciones, tab3 = st.tabs([
        "🏛️ Estructura Patrimonial", 
        "💧 Liquidez y Corto Plazo", 
        "🔄 Rotaciones y Ciclos",
        "📈 Rentabilidad Económica"
    ])
    
    # --- SOLAPA 1: PATRIMONIO (FOTO DEL BALANCE) ---
    with tab1:
        st.subheader(f"Análisis Patrimonial - Ejercicio {año_seleccionado}")
        
        # Auxiliar de herramientas dinámicas para los bloques del gráfico (HTML)
        def armar_texto_hover(sub_rubro_nombre):
            cuentas = df_mapeo[df_mapeo['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
            lineas = f"<b>{sub_rubro_nombre.upper()}</b><br>"
            for c in cuentas:
                if c in df_pivot.columns:
                    val = df_pivot[c].loc[año_seleccionado] / 1e6
                    if val != 0:
                        lineas += f"• {c}: $ {val:,.2f} M<br>"
            return lineas + "<extra></extra>"

        st.markdown("##### 🧩 Componentes del Activo")
        col_a1, col_a2, col_a3 = st.columns(3)
        
        def generar_texto_help(sub_rubro_nombre):
            cuentas = df_mapeo[df_mapeo['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
            texto = "Subcuentas integrantes:\n"
            for c in cuentas:
                if c in df_pivot.columns:
                    val = df_pivot[c].loc[año_seleccionado] / 1e6
                    if val != 0:
                        texto += f"- {c}: $ {val:,.2f} M\n"
            return texto

        col_a1.metric("Activo Total", f"$ {datos_año['Activo Total']:,.2f} M", help=f"Composición:\n- Corriente: $ {datos_año['Activo Corriente']:,.2f} M\n- No Corriente: $ {datos_año['Activo No Corriente']:,.2f} M")
        col_a2.metric("Activo Corriente", f"$ {datos_año['Activo Corriente']:,.2f} M", help=generar_texto_help('Activo Corriente'))
        col_a3.metric("Activo No Corriente", f"$ {datos_año['Activo No Corriente']:,.2f} M", help=generar_texto_help('Activo No Corriente'))
        
        st.write("")
        st.markdown("##### 🪙 Estructura Financiera")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M", help=generar_texto_help('Patrimonio Neto'))
        col_m2.metric("Pasivo Total (Fondeo Terceros)", f"$ {datos_año['Pasivo Total']:,.2f} M", help=f"Composición:\n- Corto Plazo: $ {datos_año['Pasivo Corriente']:,.2f} M\n- Largo Plazo: $ {datos_año['Pasivo No Corriente']:,.2f} M")
        col_m3.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}")
        
        st.write("")
        st.markdown(f"<h5 style='text-align: center;'>📋 Esquema Estructural del Balance (Ecuación Patrimonial)</h5>", unsafe_allow_html=True)
        
        fig_eq = go.Figure()
        
        # LADO IZQUIERDO: Inversión (Corriente ARRIBA, No Corriente ABAJO)
        fig_eq.add_trace(go.Bar(
            x=['INVERSIÓN (ACTIVO)'], y=[datos_año['Activo No Corriente']],
            name='Activo No Corriente', marker_color='#a1d99b',
            text=f"<b>ACTIVO NO CORRIENTE</b><br>(Bienes de Uso)<br><br>$ {datos_año['Activo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Activo No Corriente')
        ))
        fig_eq.add_trace(go.Bar(
            x=['INVERSIÓN (ACTIVO)'], y=[datos_año['Activo Corriente']],
            name='Activo Corriente', marker_color='#2ca02c',
            text=f"<b>ACTIVO CORRIENTE</b><br><br>$ {datos_año['Activo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Activo Corriente')
        ))
        
        # LADO DERECHO: Financiamiento (Pasivo Corriente ARRIBA, Pasivo No Corriente MEDIO, PN ABAJO)
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO (PASIVO + PN)'], y=[datos_año['Patrimonio Neto']],
            name='Patrimonio Neto', marker_color='#1f77b4',
            text=f"<b>PATRIMONIO NETO</b><br><br>$ {datos_año['Patrimonio Neto']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Patrimonio Neto')
        ))
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO (PASIVO + PN)'], y=[datos_año['Pasivo No Corriente']],
            name='Pasivo No Corriente', marker_color='#ffbb78',
            text=f"<b>PASIVO NO CORRIENTE</b><br><br>$ {datos_año['Pasivo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Pasivo no Corriente')
        ))
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO (PASIVO + PN)'], y=[datos_año['Pasivo Corriente']],
            name='Pasivo Corriente', marker_color='#ff7f0e',
            text=f"<b>PASIVO CORRIENTE</b><br><br>$ {datos_año['Pasivo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Pasivo Corriente')
        ))
        
        # Modificación Acordada: bargap=0 y tickvals=[] para remover textos del eje X redundantes
        fig_eq.update_layout(
            barmode='stack', bargap=0, showlegend=False, height=450, 
            margin=dict(t=30, b=20, l=20, r=20),
            xaxis=dict(showgrid=False, zeroline=False, showline=False, tickvals=[], ticktext=[]),
            yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        
        col_eq_izq, col_eq_centro, col_eq_der = st.columns([1, 2, 1])
        with col_eq_centro:
            st.plotly_chart(fig_eq, use_container_width=True)
            if st.button("🔍 Ampliar Esquema del Balance", key="btn_eq", use_container_width=True):
                mostrar_grafico_ampliado(fig_eq)
            
        st.write("")
        st.markdown("##### 📅 Evolución Histórica de Estructuras")
        col_t1a, col_t1b = st.columns(2)
        with col_t1a:
            fig_pas = go.Figure()
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo Corriente'], name='Pasivo Corto Plazo', marker_color='#ff7f0e', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Pasivo No Corriente'], name='Pasivo Largo Plazo', marker_color='#d62728', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_pas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Patrimonio Neto'], name='Patrimonio Neto', marker_color='#1f77b4', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_pas.update_layout(title="Evolución del Fondeo Histórico (Pasivo + PN)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_pas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Fondeo", key="btn_pas", use_container_width=True):
                mostrar_grafico_ampliado(fig_pas)
            
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente (Bienes Uso)', marker_color='#8c564b', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.update_layout(title="Evolución de la Inversión Histórica (Activos)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Inversión", key="btn_act", use_container_width=True):
                mostrar_grafico_ampliado(fig_act)
            
        st.info("""
        **💡 Guía de interpretación:**
        - **Estructura del Balance:** Esta gráfica muestra el balance general como un bloque unificado, respetando el principio de partida doble ($A = P + PN$). Permite evaluar rápidamente si los activos a largo plazo (Bienes de Uso) están siendo financiados correctamente con deudas a largo plazo o capital propio, para no ahogar la liquidez del negocio.
        - **Índice de Endeudamiento (Pasivo / PN):** Mide cuántos pesos de deuda tiene la empresa por cada peso de capital propio aportado por los socios.
        """)

    # --- SOLAPA 2: LIQUIDEZ Y RESPALDO (SOLVENCIA, GARANTÍA Y PALANCA) ---
    with tab2:
        st.subheader(f"Situación de Corto y Largo Plazo - Ejercicio {año_seleccionado}")
        
        st.markdown("##### 💧 Índices de Liquidez (Corto Plazo)")
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}")
        col_m5.metric("Prueba Ácida (Filtrada)", f"{datos_año['Prueba Acida']:.2f}")
        col_m6.metric("Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M")
        
        st.write("")
        st.markdown("##### ⚖️ Solvencia, Respaldo y Apalancamiento (Largo Plazo)")
        col_m11, col_m12, col_m13 = st.columns(3)
        col_m11.metric("Índice de Solvencia", f"{datos_año['Solvencia']:.2f}")
        col_m12.metric("Índice de Garantía (PN / Pasivo)", f"{datos_año['Garantia']:.2f}")
        col_m13.metric("Efecto Palanca (GAF)", f"{datos_año['Efecto Palanca']:.2f}x")
        
        st.write("")
        col_t2a, col_t2b = st.columns(2)
        
        with col_t2a:
            fig_liq = go.Figure()
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Límite Técnico (1.0)")
            fig_liq.update_layout(title="Evolución Histórica de los Índices de Liquidez", yaxis_title="Índice", hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_liq, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Liquidez", key="btn_liq", use_container_width=True):
                mostrar_grafico_ampliado(fig_liq)
                
        with col_t2b:
            fig_solv = go.Figure()
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Solvencia'], mode='lines+markers', name='Índice de Solvencia', line=dict(width=3, color='#bcbd22'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Garantia'], mode='lines+markers', name='Índice de Garantía', line=dict(width=3, color='#1f77b4', dash='dash'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Efecto Palanca'], mode='lines+markers', name='Efecto Palanca (GAF)', line=dict(width=3, color='#e377c2', dash='dot'), hovertemplate="%{y:.2f}x<extra></extra>"))
            fig_solv.update_layout(title="Evolución de Solvencia, Respaldo y Palanca", yaxis_title="Ratio / Multiplicador", hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_solv, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Solvencia y Palanca", key="btn_solv", use_container_width=True):
                mostrar_grafico_ampliado(fig_solv)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **Liquidez Corriente (Activo Corriente / Pasivo Corriente):** Indica cuántos pesos en bienes líquidos o realizables de corto plazo se tienen para cubrir cada peso de deuda que vence dentro del año.
        - **Prueba Ácida Filtrada:** Mide la capacidad de pago inmediata más estricta. Excluye totalmente los inventarios (Bienes de cambio), los créditos fiscales y otros créditos no comerciales, computando únicamente la disponibilidad líquida real y las cuentas a cobrar de clientes de forma prolija.
        - **Índice de Solvencia (Activo Total / Pasivo Total):** Mide la garantía a largo plazo de la empresa. Evalúa si el total de activos es suficiente para respaldar el total de las obligaciones contraídas con terceros.
        - **Índice de Garantía (PN / Pasivo Total):** Es la contrapartida del endeudamiento. Mide el respaldo o "espalda propia" que ofrecen los socios ante las deudas totales. Indica cuántos pesos de capital propio respaldan cada peso de deuda externa.
        - **Efecto Palanca Financiera (GAF):** Utiliza la fórmula avanzada de rentabilidad. Mide la relación entre el ROE y el rendimiento del capital permanente. Un valor superior a 1.0 demuestra un apalancamiento positivo: la deuda externa se tomó a un costo menor que el rendimiento del negocio, multiplicando la utilidad final para el socio.
        """)

    # --- SOLAPA 3: RENTABILIDAD ECONÓMICA (LA PELÍCULA DE LOS RESULTADOS) ---
    with tab3:
        st.subheader(f"Rendimiento Económico - Ejercicio {año_seleccionado}")
        
        col_m7, col_m8, col_m9, col_m10 = st.columns(4)
        col_m7.metric("Ventas Netas", f"$ {datos_año['Ventas']:,.2f} M")
        col_m8.metric("Margen EBITDA", f"{datos_año['Margen EBITDA (%)']:.2f}%")
        col_m9.metric("Rentabilidad s/ Ventas (Neto)", f"{datos_año['Margen Neto (%)']:.2f}%")
        col_m10.metric("Rentabilidad s/ PN (ROE)", f"{datos_año['ROE (%)']:.2f}%")
        
        st.write("")
        col_t3a, col_t3b = st.columns(2)
        
        with col_t3a:
            st.markdown("##### 🛒 Volumen de Ventas vs Eficiencia (ROS)")
            fig_ventas = go.Figure()
            fig_ventas.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Ventas'], name='Ventas Netas', marker_color='#17becf', yaxis='y', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_ventas.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], mode='lines+markers', name='Margen Neto (%)', yaxis='y2', line=dict(color='#ff7f0e', width=3), hovertemplate="%{y:.2f}%<extra></extra>"))
            fig_ventas.update_layout(
                title="Evolución de Ventas vs Margen Neto Final",
                yaxis=dict(title="Millones de Pesos"),
                yaxis2=dict(title="Margen Neto (%)", overlaying='y', side='right', showgrid=False),
                barmode='group', hovermode="x unified", height=450, legend=config_leyenda_abajo
            )
            st.plotly_chart(fig_ventas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Ventas", key="btn_ventas", use_container_width=True):
                mostrar_grafico_ampliado(fig_ventas)
            
        with col_t3b:
            st.markdown("##### 💰 Generación de Caja Operativa")
            fig_rent = go.Figure()
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['EBITDA Proxy'], name='Caja Operativa (EBITDA)', marker_color='#bcbd22', yaxis='y', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_rent.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Resultado Neto'], name='Resultado Neto Final', marker_color='#2ca02c', yaxis='y', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_rent.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Margen EBITDA (%)'], mode='lines+markers', name='Margen EBITDA (%)', yaxis='y2', line=dict(color='black', width=2), hovertemplate="%{y:.2f}%<extra></extra>"))
            fig_rent.update_layout(
                title="EBITDA vs Resultado Neto Real",
                yaxis=dict(title="Millones de Pesos"),
                yaxis2=dict(title="Margen EBITDA (%)", overlaying='y', side='right', showgrid=False),
                barmode='group', hovermode="x unified", height=450, legend=config_leyenda_abajo
            )
            st.plotly_chart(fig_rent, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Caja", key="btn_caja", use_container_width=True):
                mostrar_grafico_ampliado(fig_rent)

        # --- INTEGRACIÓN PUNTO 2: MODELO DUPONT DENTRO DE RENTABILIDAD ---
        st.write("")
        st.markdown("---")
        st.subheader(f"🎯 Descomposición del ROE (Esquema DuPont) - Ejercicio {año_seleccionado}")
        
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        col_d1.metric("Margen Neto (Eficiencia)", f"{datos_año['Margen Neto (%)']:.2f}%")
        col_d2.metric("Rotación Activos (Eficacia)", f"{datos_año['Rotacion Activos']:.2f}x")
        col_d3.metric("Multiplicador (Apalancamiento)", f"{datos_año['Multiplicador Capital']:.2f}x")
        col_d4.metric("ROE Final (Rendimiento PN)", f"{datos_año['ROE (%)']:.2f}%")
        
       # --- REEMPLAZO SEGURO: VARIABLE ÚNICA PARA EVITAR DUPLICADOS ---
        st.write("")
        fig_dupont_rent = go.Figure() # <--- Cambiamos el nombre de la variable acá
        
        # Eje Y Principal: Tasas en Porcentaje (%)
        fig_dupont_rent.add_trace(go.Scatter(
            x=df_filtrado.index, y=df_filtrado['ROE (%)'], 
            name='ROE (%) [Eje Izq]', 
            line=dict(color='#e377c2', width=4), 
            hovertemplate="ROE: %{y:.2f}%<extra></extra>"
        ))
        fig_dupont_rent.add_trace(go.Scatter(
            x=df_filtrado.index, y=df_filtrado['Margen Neto (%)'], 
            name='Margen Neto (%) [Eje Izq]', 
            line=dict(color='#ff7f0e', width=2, dash='dash'), 
            hovertemplate="Margen Neto: %{y:.2f}%<extra></extra>"
        ))
        
        # Eje Y Secundario: Ratios en Veces (x)
        fig_dupont_rent.add_trace(go.Scatter(
            x=df_filtrado.index, y=df_filtrado['Rotacion Activos'], 
            name='Rotación Activos (x) [Eje Der]', 
            yaxis='y2', line=dict(color='#2ca02c', width=2), 
            hovertemplate="Rotación: %{y:.2f}x<extra></extra>"
        ))
        fig_dupont_rent.add_trace(go.Scatter(
            x=df_filtrado.index, y=df_filtrado['Multiplicador Capital'], 
            name='Multiplicador Cap. (x) [Eje Der]', 
            yaxis='y2', line=dict(color='#1f77b4', width=2, dash='dot'), 
            hovertemplate="Multiplicador: %{y:.2f}x<extra></extra>"
        ))
        
        # Configuración de Layout con Eje Y Doble
        fig_dupont_rent.update_layout(
            title="Análisis de Tendencias DuPont: Drivers del ROE", 
            xaxis=dict(title="Período"),
            yaxis=dict(title="Porcentaje (%)", side="left"),
            yaxis2=dict(title="Ratio / Veces (x)", overlaying='y', side='right', showgrid=False),
            hovermode="x unified", height=500, legend=config_leyenda_abajo
        )
        
        # Renderizado con variables específicas únicas
        st.plotly_chart(fig_dupont_rent, use_container_width=True)
        
        if st.button("🔍 Ampliar Gráfico DuPont", key="btn_dupont_rentabilidad", use_container_width=True):
            mostrar_grafico_ampliado(fig_dupont_rent)
            
        st.info("""
        **💡 Guía de interpretación:**
        - **Rentabilidad sobre Ventas (ROS / Margen Neto):** Mide la eficiencia comercial. Nos indica qué porcentaje de cada peso facturado por la empresa queda limpio como ganancia neta para los socios después de absorber todos los costos, amortizaciones, gastos financieros e impuestos.
        - **Rentabilidad sobre el Patrimonio Neto (ROE):** Mide el rendimiento del capital propio. Indica cuánta ganancia genera la empresa por cada peso que los socios dejaron invertido en el negocio. Es la métrica definitiva de éxito financiero para el accionista.
        - **Caja Operativa (EBITDA Proxy):** Muestra el verdadero potencial del negocio para generar fondos genuinos por su actividad core, aislando amortizaciones, costos financieros e impuestos.
        
        **💡 Guía de interpretación del Modelo DuPont:**
        Este esquema desarma estratégicamente el ROE para revelar cuál es la verdadera palanca que está empujando la rentabilidad del accionista, multiplicando tres frentes del negocio:
        - **Eficiencia en Costos (Margen Neto):** Cuánto rinde cada peso de venta.
        - **Eficacia Operativa (Rotación de Activos):** Cuántas veces se hace girar la estructura de inversión para generar esas ventas.
        - **Apalancamiento (Multiplicador del Capital):** Cómo impacta el uso de fondos de terceros sobre el capital propio aportado.
        """)
       
    # --- SOLAPA: ROTACIONES Y CICLOS OPERATIVOS ---
    with tab_rotaciones:
        st.subheader(f"📊 Análisis de Ciclos Operativos y Eficiencia - Ejercicio {año_seleccionado}")
        
        # Fila de KPIs de Plazos Medios
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Plazo Medio de Cobranza", f"{datos_año['Dias Cobro']:.0f} días", 
                      help="Promedio de días que transcurren desde que se factura un servicio o venta hasta que se cobra efectivamente.")
        col_r2.metric("Días de Stock en Inmovilización", f"{datos_año['Dias Inventario']:.0f} días", 
                      help="Días promedio que la mercadería/materiales permanecen en el activo antes de ser vendidos. Calculado sobre CMV.")
        col_r3.metric("Plazo Medio de Pago a Proveedores", f"{datos_año['Dias Pago']:.0f} días", 
                      help="Plazo promedio de financiación comercial obtenido de los proveedores de bienes y servicios.")
        
        st.write("")
        col_tr1, col_tr2 = st.columns(2)
        
        with col_tr1:
            st.markdown("##### ⏱️ Evolución Temporal del Ciclo Operativo (Días)")
            fig_ciclos = go.Figure()
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Cobro'], mode='lines+markers', name='Plazo Cobro (Clientes)', line=dict(color='#1f77b4', width=3)))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Inventario'], mode='lines+markers', name='Plazo Stock (Inventario)', line=dict(color='#ff7f0e', width=3)))
            fig_ciclos.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Dias Pago'], mode='lines+markers', name='Plazo Pago (Proveedores)', line=dict(color='#d62728', width=3, dash='dash')))
            fig_ciclos.update_layout(yaxis_title="Días Corridos", hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_ciclos, use_container_width=True)
            
        with col_tr2:
            st.markdown("##### 🔄 Intensidad de Rotación de Activos (Veces al Año)")
            fig_rot_act = go.Figure()
            fig_rot_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Total'], name='Rot. Activo Total', marker_color='#2ca02c'))
            fig_rot_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Rotacion Activo Corriente'], name='Rot. Activo Corriente', marker_color='#9467bd'))
            fig_rot_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Rotacion Bienes Uso'], name='Rot. Bienes de Uso', marker_color='#bcbd22'))
            fig_rot_act.update_layout(yaxis_title="Veces de Rotación", barmode='group', hovermode="x unified", height=450, legend=config_leyenda_abajo)
            st.plotly_chart(fig_rot_act, use_container_width=True)

        st.info("""
        **💡 Lectura Gerencial del Ciclo Operativo:**
        * **El Descalce Financiero:** Si la suma de *Plazo de Cobro + Plazo de Stock* es mayor al *Plazo de Pago*, la empresa tiene un déficit estructural de capital de trabajo que debe financiar con caja propia o bancaria.
        * **Rotación de Estructura (Bienes de Uso):** Mide cuántos pesos de ventas genera la empresa por cada peso invertido en maquinarias, instalaciones o vehículos. Un ratio decreciente alerta subutilización de la estructura.
        """)
  

else:
    st.info("👆 Por favor, subí el archivo Excel (.xlsx) para comenzar el análisis.")
