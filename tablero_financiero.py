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
    
    # --- 2. MOTOR DE CÁLCULOS ---
    # Cuentas individuales para los Tooltips dinámicos (en Millones)
    act_liq = df_pivot.get('activo liquido', 0) / 1e6
    cred_com = df_pivot.get('creditos comerciales', 0) / 1e6
    b_cambio = df_pivot.get('Bienes de cambio', 0) / 1e6
    b_uso = df_pivot.get('Bienes de Uso', 0) / 1e6
    
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

    # Consolidación en DataFrame
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
        'Multiplicador Capital': multiplicador_capital,
        'Act Liquido': act_liq,
        'Cred Comerciales': cred_com,
        'Bienes Cambio': b_cambio,
        'Bienes Uso': b_uso
    }).dropna().round(2)

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
        
        st.markdown("##### 🧩 Componentes del Activo")
        col_a1, col_a2, col_a3 = st.columns(3)
        
        col_a1.metric(
            label="Activo Total", 
            value=f"$ {datos_año['Activo Total']:,.2f} M",
            help=f"Composición:\n- Corriente: $ {datos_año['Activo Corriente']:,.2f} M\n- No Corriente: $ {datos_año['Activo No Corriente']:,.2f} M"
        )
        col_a2.metric(
            label="Activo Corriente", 
            value=f"$ {datos_año['Activo Corriente']:,.2f} M",
            help=f"Subcuentas integrantes:\n- Activo Líquido: $ {datos_año['Act Liquido']:,.2f} M\n- Créditos Comerciales: $ {datos_año['Cred Comerciales']:,.2f} M\n- Bienes de Cambio: $ {datos_año['Bienes Cambio']:,.2f} M"
        )
        col_a3.metric(
            label="Activo No Corriente", 
            value=f"$ {datos_año['Activo No Corriente']:,.2f} M",
            help=f"Subcuentas integrantes:\n- Bienes de Uso: $ {datos_año['Bienes Uso']:,.2f} M"
        )
        
        st.write("")
        st.markdown("##### 🪙 Estructura Financiera")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Patrimonio Neto", f"$ {datos_año['Patrimonio Neto']:,.2f} M")
        col_m2.metric("Pasivo Total (Fondeo Terceros)", f"$ {datos_año['Pasivo Total']:,.2f} M")
        col_m3.metric("Índice de Endeudamiento", f"{datos_año['Endeudamiento']:.2f}")
        
        st.write("")
        st.markdown(f"##### 📋 Esquema Estructural del Balance (Ecuación Patrimonial)")
        
        fig_eq = go.Figure()
        
        # Bloques de la columna de la IZQUIERDA (Inversión / Activos)
        fig_eq.add_trace(go.Bar(
            x=['ESTRUCTURA DE INVERSIÓN<br>(ACTIVOS)'], y=[datos_año['Activo Corriente']],
            name='Activo Corriente', marker_color='#2ca02c',
            text=f"<b>ACTIVO CORRIENTE</b><br><br>$ {datos_año['Activo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',  # <--- ACÁ ESTÁ LA CORRECCIÓN
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate="$ %{y:.2f} M<extra></extra>"
        ))
        fig_eq.add_trace(go.Bar(
            x=['ESTRUCTURA DE INVERSIÓN<br>(ACTIVOS)'], y=[datos_año['Activo No Corriente']],
            name='Activo No Corriente', marker_color='#a1d99b',
            text=f"<b>ACTIVO NO CORRIENTE</b><br>(Bienes de Uso)<br><br>$ {datos_año['Activo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',  # <--- ACÁ ESTÁ LA CORRECCIÓN
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate="$ %{y:.2f} M<extra></extra>"
        ))
        
        # Bloques de la columna de la DERECHA (Financiamiento / Pasivo + PN)
        fig_eq.add_trace(go.Bar(
            x=['ESTRUCTURA DE FINANCIAMIENTO<br>(PASIVO + PN)'], y=[datos_año['Pasivo Corriente']],
            name='Pasivo Corriente', marker_color='#ff7f0e',
            text=f"<b>PASIVO CORRIENTE</b><br><br>$ {datos_año['Pasivo Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',  # <--- ACÁ ESTÁ LA CORRECCIÓN
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate="$ %{y:.2f} M<extra></extra>"
        ))
        fig_eq.add_trace(go.Bar(
            x=['ESTRUCTURA DE FINANCIAMIENTO<br>(PASIVO + PN)'], y=[datos_año['Pasivo No Corriente']],
            name='Pasivo No Corriente', marker_color='#ffbb78',
            text=f"<b>PASIVO NO CORRIENTE</b><br><br>$ {datos_año['Pasivo No Corriente']:,.2f} M",
            textposition='inside', insidetextanchor='middle',  # <--- ACÁ ESTÁ LA CORRECCIÓN
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate="$ %{y:.2f} M<extra></extra>"
        ))
        fig_eq.add_trace(go.Bar(
            x=['ESTRUCTURA DE FINANCIAMIENTO<br>(PASIVO + PN)'], y=[datos_año['Patrimonio Neto']],
            name='Patrimonio Neto', marker_color='#1f77b4',
            text=f"<b>PATRIMONIO NETO</b><br><br>$ {datos_año['Patrimonio Neto']:,.2f} M",
            textposition='inside', insidetextanchor='middle',  # <--- ACÁ ESTÁ LA CORRECCIÓN
            marker=dict(line=dict(color='#222', width=2)),
            hovertemplate="$ %{y:.2f} M<extra></extra>"
        ))
        
        # Eliminación absoluta de elementos cartesianos y ejes
        fig_eq.update_layout(
            barmode='stack',
            showlegend=False,
            height=550,
            margin=dict(t=30, b=50, l=60, r=60),
            xaxis=dict(
                showgrid=False, zeroline=False, showline=False,
                tickfont=dict(size=14, bold=True, color='black')
            ),
            yaxis=dict(
                showgrid=False, zeroline=False, showline=False,
                showticklabels=False
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
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
            fig_pas.update_layout(title="Evolución del Fondeo Histórico (Pasivo + PN)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=400)
            st.plotly_chart(fig_pas, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Fondeo", key="btn_pas", use_container_width=True):
                mostrar_grafico_ampliado(fig_pas)
            
        with col_t1b:
            fig_act = go.Figure()
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo Corriente'], name='Activo Corriente', marker_color='#2ca02c', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.add_trace(go.Bar(x=df_filtrado.index, y=df_filtrado['Activo No Corriente'], name='Activo No Corriente (Bienes Uso)', marker_color='#8c564b', hovertemplate="$ %{y:.2f} M<extra></extra>"))
            fig_act.update_layout(title="Evolución de la Inversión Histórica (Activos)", yaxis_title="Millones de Pesos", barmode='stack', hovermode="x unified", height=400)
            st.plotly_chart(fig_act, use_container_width=True)
            if st.button("🔍 Ampliar Gráfico de Inversión", key="btn_act", use_container_width=True):
                mostrar_grafico_ampliado(fig_act)
            
        st.info("""
        **💡 Guía de interpretación:**
        - **Estructura del Balance:** Este bloque simula la representación gráfica clásica de la situación patrimonial. Permite contrastar de manera lineal si el Activo Corriente (bienes de corto plazo) es suficiente para cubrir las exigencias del Pasivo Corriente, y verificar que los Activos Fijos estén financiados genuinamente por recursos de largo plazo o Patrimonio Neto.
        - **Índice de Endeudamiento (Pasivo / PN):** Mide cuántos pesos de deuda tiene la empresa por cada peso de capital propio aportado por los socios.
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
        fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(width=3, color='#17becf'), hovertemplate="%{y:.2f}<extra></extra>"))
        fig_liq.add_trace(go.Scatter(x=df_filtrado.index, y=df_filtrado['Prueba Acida'], mode='lines+markers', name='Prueba Ácida', line=dict(width=3, color='#9467bd', dash='dot'), hovertemplate="%{y:.2f}<extra></extra>"))
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
        - **Rentabilidad sobre Ventas (ROS / Margen Neto):** Mide la eficiencia comercial.
        - **Rentabilidad sobre el Patrimonio Neto (ROE):** Mide el rendimiento del capital propio.
        - **Caja Operativa (EBITDA Proxy):** Muestra el verdadero potencial del negocio para generar fondos genuinos.
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
