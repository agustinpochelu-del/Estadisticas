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

    # Función motor para sumar dinámicamente las cuentas
    def sumar_sub_rubro(df_datos, df_map, sub_rubro_nombre):
        cuentas = df_map[df_map['Sub Rubro'].str.lower() == sub_rubro_nombre.lower()]['Cuenta'].tolist()
        cuentas_existentes = [c for c in cuentas if c in df_datos.columns]
        if not cuentas_existentes:
            return pd.Series(0, index=df_datos.index)
        return df_datos[cuentas_existentes].sum(axis=1)

    # --- 2. CÁLCULOS ---
    activo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo Corriente')
    activo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Activo No Corriente')
    activo_total = activo_corriente + activo_no_corriente
    
    pasivo_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo Corriente')
    pasivo_no_corriente = sumar_sub_rubro(df_pivot, df_mapeo, 'Pasivo no Corriente')
    pasivo_total = pasivo_corriente + pasivo_no_corriente
    
    patrimonio_neto = sumar_sub_rubro(df_pivot, df_mapeo, 'Patrimonio Neto')
    endeudamiento = pasivo_total / patrimonio_neto.replace(0, pd.NA)
    
    liquidez_corriente = activo_corriente / pasivo_corriente.replace(0, pd.NA)
    bienes_de_cambio = df_pivot.get('Bienes de cambio', pd.Series(0, index=df_pivot.index))
    prueba_acida = (activo_corriente - bienes_de_cambio) / pasivo_corriente.replace(0, pd.NA)
    capital_trabajo = activo_corriente - pasivo_corriente
    
    # Nuevos cálculos para Solvencia y Efecto Palanca
    solvencia = activo_total / pasivo_total.replace(0, pd.NA)
    
    ventas = df_pivot.get('ventas', pd.Series(0, index=df_pivot.index))
    resultado_neto = df_pivot.get('Resultado Neto', pd.Series(0, index=df_pivot.index))
    ebitda_proxy = resultado_neto + df_pivot.get('Amortizacion', 0) + df_pivot.get('Intereses Financieros', 0) + df_pivot.get('impuesto a las gs', 0)
    margen_ebitda = (ebitda_proxy / ventas.replace(0, pd.NA)) * 100
    margen_neto = (resultado_neto / ventas.replace(0, pd.NA)) * 100
    
    roe = (resultado_neto / patrimonio_neto.replace(0, pd.NA)) * 100
    rotacion_activos = ventas / activo_total.replace(0, pd.NA)
    multiplicador_capital = activo_total / patrimonio_neto.replace(0, pd.NA)

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
        'Efecto Palanca': multiplicador_capital, # Representa el multiplicador de apalancamiento financiero
        'Ventas': ventas / 1e6, 
        'Resultado Neto': resultado_neto / 1e6, 
        'EBITDA Proxy': ebitda_proxy / 1e6,
        'Margen Neto (%)': margen_neto, 
        'Margen EBITDA (%)': margen_ebitda,
        'ROE (%)': roe, 
        'Rotacion Activos': rotacion_activos, 
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
        fig_eq.add_trace(go.Bar(
            x=['INVERSIÓN<br>(ACTIVO)'], y=[datos_año['Activo No Corriente']],
            name='Activo No Corriente', marker_color='#a1d99b',
            text=f"<b>ACTIVO NO CORRIENTE</b><br>(Bienes de Uso)<br><br>$ {datos_año['Activo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Activo No Corriente')
        ))
        fig_eq.add_trace(go.Bar(
            x=['INVERSIÓN<br>(ACTIVO)'], y=[datos_año['Activo Corriente']],
            name='Activo Corriente', marker_color='#2ca02c',
            text=f"<b>ACTIVO CORRIENTE</b><br><br>$ {datos_año['Activo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Activo Corriente')
        ))
        
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO<br>(PASIVO + P.N.)'], y=[datos_año['Patrimonio Neto']],
            name='Patrimonio Neto', marker_color='#1f77b4',
            text=f"<b>PATRIMONIO NETO</b><br><br>$ {datos_año['Patrimonio Neto']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Patrimonio Neto')
        ))
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO<br>(PASIVO + P.N.)'], y=[datos_año['Pasivo No Corriente']],
            name='Pasivo No Corriente', marker_color='#ffbb78',
            text=f"<b>PASIVO NO CORRIENTE</b><br><br>$ {datos_año['Pasivo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Pasivo no Corriente')
        ))
        fig_eq.add_trace(go.Bar(
            x=['FINANCIAMIENTO<br>(PASIVO + P.N.)'], y=[datos_año['Pasivo Corriente']],
            name='Pasivo Corriente', marker_color='#ff7f0e',
            text=f"<b>PASIVO CORRIENTE</b><br><br>$ {datos_año['Pasivo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate=armar_texto_hover('Pasivo Corriente')
        ))
        
        fig_eq.update_layout(
            barmode='stack', bargap=0, showlegend=False, height=450, 
            margin=dict(t=30, b=50, l=20, r=20),
            xaxis=dict(showgrid=False, zeroline=False, showline=False, tickfont=dict(size=14, color='black')),
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
            fig_pas.update_layout(title="Evolución del Fondeo Histórico (Pasivo + PN)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450)
            st.plotly_chart(fig_pas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Fondeo", key="btn_pas", use_container_width=True):
                mostrar_grafico_ampliado(fig_pas)
            
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente (Bienes Uso)', marker_color='#8c564b', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.update_layout(title="Evolución de la Inversión Histórica (Activos)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=450)
            st.plotly_chart(fig_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Inversión", key="btn_act", use_container_width=True):
                mostrar_grafico_ampliado(fig_act)
            
        st.info("""
        **💡 Guía de interpretación:**
        - **Estructura del Balance:** Esta gráfica muestra el balance general como un bloque unificado, respetando el principio de partida doble ($A = P + PN$). Permite evaluar rápidamente si los activos a largo plazo (Bienes de Uso) están siendo financiados correctamente con deudas a largo plazo o capital propio, para no ahogar la liquidez del negocio.
        - **Índice de Endeudamiento (Pasivo / PN):** Mide cuántos pesos de deuda tiene la empresa por cada peso de capital propio aportado por los socios.
        """)

    # --- SOLAPA 2: LIQUIDEZ Y ESTRUCTURA DE COMPROMISOS ---
    with tab2:
        st.subheader(f"Situación de Corto y Largo Plazo - Ejercicio {año_seleccionado}")
        
        # Fila 1: KPIs de Corto Plazo (Liquidez)
        st.markdown("##### 💧 Índices de Liquidez (Corto Plazo)")
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Liquidez Corriente", f"{datos_año['Liquidez Corriente']:.2f}")
        col_m5.metric("Prueba Ácida (Líquida)", f"{datos_año['Prueba Acida']:.2f}")
        col_m6.metric("Capital de Trabajo", f"$ {datos_año['Capital de Trabajo']:,.2f} M")
        
        st.write("")
        # Fila 2: Nuevos KPIs de Estructura Sólida de Largo Plazo
        st.markdown("##### ⚖️ Solvencia y Apalancamiento (Estructura de Largo Plazo)")
        col_m11, col_m12 = st.columns(2)
        col_m11.metric("Índice de Solvencia", f"{datos_año['Solvencia']:.2f}")
        col_m12.metric("Efecto Palanca Financiera", f"{datos_año['Efecto Palanca']:.2f}x")
        
        st.write("")
        # Gráficos simétricos de Tendencias enfrentados al 50% de ancho
        col_t2a, col_t2b = st.columns(2)
        
        with col_t2a:
            fig_liq = go.Figure()
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_liq.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Límite Técnico (1.0)")
            fig_liq.update_layout(title="Evolución Histórica de los Índices de Liquidez", yaxis_title="Índice", hovermode="x unified", height=450)
            st.plotly_chart(fig_liq, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Liquidez", key="btn_liq", use_container_width=True):
                mostrar_grafico_ampliado(fig_liq)
                
        with col_t2b:
            # Nuevo Gráfico de Solvencia y Efecto Palanca
            fig_solv = go.Figure()
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Solvencia'], mode='lines+markers', name='Índice de Solvencia', line=dict(width=3, color='#bcbd22'), hovertemplate="%{y:.2f}<extra></extra>"))
            fig_solv.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Efecto Palanca'], mode='lines+markers', name='Efecto Palanca', line=dict(width=3, color='#e377c2', dash='dot'), hovertemplate="%{y:.2f}x<extra></extra>"))
            fig_solv.update_layout(title="Evolución de Solvencia y Apalancamiento Histórico", yaxis_title="Ratio / Multiplicador", hovermode="x unified", height=450)
            st.plotly_chart(fig_solv, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Solvencia y Palanca", key="btn_solv", use_container_width=True):
                mostrar_grafico_ampliado(fig_solv)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **Liquidez Corriente (Activo Corriente / Pasivo Corriente):** Indica cuántos pesos en bienes líquidos o de rápido vencimiento tiene la empresa para cubrir cada peso de deuda que vence dentro del año.
        - **Prueba Ácida:** Es un filtro más exigente que resta los inventarios (Bienes de cambio), evaluando si la empresa puede responder a sus deudas inmediatas utilizando únicamente caja y cuentas a cobrar rápidas.
        - **Índice de Solvencia (Activo Total / Pasivo Total):** Evalúa la garantía global que ofrece la empresa a largo plazo. Mide si la totalidad de los bienes indexados cubre la totalidad de las obligaciones con terceros. Un ratio superior a 1.5 indica una estructura patrimonial saludable y con respaldo.
        - **Efecto Palanca Financiera (Activo / PN):** Determina el grado de ventaja que tiene la empresa al financiarse con capital de terceros. Si este indicador es superior a 1.0, significa que la rentabilidad de los fondos invertidos supera el costo de la deuda, logrando un apalancamiento positivo que incrementa el retorno final para los socios.
        """)

    # --- SOLAPA 3: RENTABILIDAD ---
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
                barmode='group', hovermode="x unified", height=450
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
                barmode='group', hovermode="x unified", height=450
            )
            st.plotly_chart(fig_rent, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Caja", key="btn_caja", use_container_width=True):
                mostrar_grafico_ampliado(fig_rent)
        
        st.info("""
        **💡 Guía de interpretación:**
        - **Rentabilidad sobre Ventas (ROS / Margen Neto):** Mide la eficiencia comercial. Nos indica qué porcentaje de cada peso facturado por la empresa queda limpio como ganancia neta para los socios después de absorber todos los costos, amortizaciones, gastos financieros e impuestos.
        - **Rentabilidad sobre el Patrimonio Neto (ROE):** Mide el rendimiento del capital propio. Indica cuánta ganancia genera la empresa por cada peso que los socios dejaron invertido en el negocio. Es la métrica definitiva de éxito financiero para el accionista.
        - **Caja Operativa (EBITDA Proxy):** Muestra el verdadero potencial del negocio para generar fondos genuinos por su actividad core, aislando amortizaciones, costos financieros e impuestos.
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
        fig_dupont.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['ROE (%)'], mode='lines+markers', name='ROE (%) Histórico', line=dict(color='#e377c2', width=4), hovertemplate="%{y:.2f}%<extra></extra>"))
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
