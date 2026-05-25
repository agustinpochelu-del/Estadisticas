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
        position: sticky;
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
