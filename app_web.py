import streamlit as st
import pandas as pd
import plotly.express as px
import os
import calendar

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# --- ESTILO CSS RESPONSIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; font-weight: bold; font-size: 1.8rem !important; }
    
    /* Ajustes para telas pequenas (Celulares) */
    @media (max-width: 768px) {
        .dizimo-valor { font-size: 28px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 0px; }
        .stTabs [data-baseweb="tab"] { padding: 10px 5px; font-size: 12px; }
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    }

    .publico-total-box {
        background-color: #162a3e; border-radius: 10px; padding: 15px;
        color: #00D4FF; font-weight: bold; font-size: 18px; border-left: 5px solid #00D4FF;
        margin-top: 10px; text-align: center;
    }
    .dizimo-destaque {
        padding: 20px; background-color: #1a1c24; border-radius: 15px;
        border: 1px solid #31333F; margin-bottom: 25px; text-align: center;
    }
    .dizimo-titulo { color: #bdc3c7; font-size: 14px; margin-bottom: 5px; }
    .dizimo-valor { color: #ffffff; font-size: 42px; font-weight: 800; margin: 0; }
    
    /* Forçar tabelas a terem scroll lateral no mobile */
    .stDataFrame { overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CONFIGURAÇÕES E DADOS ---
ARQUIVO_DIZIMOS = "dados_dizimos.csv"
ARQUIVO_FREQ = "frequencia_celula_2026.csv"
MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
CASAIS = ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"]
TIPOS = ["Célula", "Culto de Jovens"]
CORES_AZYK = {"ME": "#00D4FF", "FA": "#0072FF", "VI": "#00C6FF"}

meses_map = {m: list(calendar.month_name)[i+1] for i, m in enumerate(MESES_ORDEM)}

@st.cache_data
def carregar_dizimos():
    if os.path.exists(ARQUIVO_DIZIMOS): return pd.read_csv(ARQUIVO_DIZIMOS)
    return pd.DataFrame({"Mês": [m for m in MESES_ORDEM[:7] for _ in range(25)], "Líder": [f"Líder {i:02d}" for i in range(1, 26)] * 7, "Valor": 0.0, "Pago": "Não"})

def inicializar_frequencia():
    if os.path.exists(ARQUIVO_FREQ): return pd.read_csv(ARQUIVO_FREQ)
    data = []
    for mes in MESES_ORDEM:
        for casal in CASAIS:
            for tipo in TIPOS:
                row = {"Mês": mes, "Casal": casal, "Tipo": tipo}
                for i in range(1, 6): row[f"S{i}_ME"] = 0; row[f"S{i}_FA"] = 0; row[f"S{i}_VI"] = 0
                data.append(row)
    df = pd.DataFrame(data); df.to_csv(ARQUIVO_FREQ, index=False); return df

def obter_sabados_do_mes(mes_nome, ano=2026):
    mes_num = list(calendar.month_name).index(meses_map[mes_nome])
    cal = calendar.monthcalendar(ano, mes_num)
    return [f"{semana[calendar.SATURDAY]:02d}/{mes_num:02d}" for semana in cal if semana[calendar.SATURDAY] != 0]

if 'df' not in st.session_state: st.session_state.df = carregar_dizimos()
if 'df_freq' not in st.session_state: st.session_state.df_freq = inicializar_frequencia()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Administração")
    senha = st.text_input("Senha:", type="password")
    is_admin = (senha == "1234")

st.markdown("<h2 style='text-align: center; color: white;'>⛪ Radicais Livres 2026</h2>", unsafe_allow_html=True)

# Tabs com ícones menores para mobile
if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Freq.", "💰 Dízimos", "📝 Lançar"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Visão Dízimo"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1: mes_sel = st.selectbox("📅 Mês:", MESES_ORDEM, key="f_mes")
    with col_f2: modo_edicao = st.toggle("✏️ Editar", value=False)

    sabados = obter_sabados_do_mes(mes_sel)
    n_sab = len(sabados)
    df_mes_f = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].copy().reset_index(drop=True)

    conf_f = {"Mês": None, "Casal": st.column_config.Column("Discipulador", disabled=True), "Tipo": st.column_config.Column(disabled=True)}
    for i in range(1, 6):
        if i <= n_sab:
            dt = sabados[i-1]
            conf_f[f"S{i}_ME"] = st.column_config.NumberColumn(f"{dt}|ME", width="small")
            conf_f[f"S{i}_FA"] = st.column_config.NumberColumn(f"{dt}|FA", width="small")
            conf_f[f"S{i}_VI"] = st.column_config.NumberColumn(f"{dt}|VI", width="small")
        else:
            conf_f[f"S{i}_ME"] = conf_f[f"S{i}_FA"] = conf_f[f"S{i}_VI"] = None

    if modo_edicao:
        df_ed_f = st.data_editor(df_mes_f, column_config=conf_f, use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Frequência", use_container_width=True):
            idx_f = st.session_state.df_freq[st.session_state.df_freq["Mês"] == mes_sel].index
            st.session_state.df_freq.loc[idx_f, :] = df_ed_f.values
            st.session_state.df_freq.to_csv(ARQUIVO_FREQ, index=False); st.success("Salvo!"); st.rerun()
    else:
        sel_f = st.dataframe(df_mes_f, column_config=conf_f, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        df_p_plot = df_mes_f.iloc[sel_f.selection.rows] if sel_f.selection.rows else df_mes_f

    st.markdown("---")
    
    # Dashboards adaptados
    c1, c2 = st.columns([1, 1])
    
    l_p = []
    for _, r in df_p_plot.iterrows():
        for i in range(1, n_sab + 1):
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "ME", "Valor": r[f"S{i}_ME"]})
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "FA", "Valor": r[f"S{i}_FA"]})
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "VI", "Valor": r[f"S{i}_VI"]})
    
    if l_p:
        df_p = pd.DataFrame(l_p).groupby(["Sábado", "Tipo", "Indicador"])["Valor"].sum().reset_index()
        fig = px.bar(df_p, x="Sábado", y="Valor", color="Indicador", barmode="group", facet_col="Tipo", text="Valor", color_discrete_map=CORES_AZYK)
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

    with c1:
        me = int(df_p_plot[[f"S{i}_ME" for i in range(1, n_sab+1)]].sum().sum())
        fa = int(df_p_plot[[f"S{i}_FA" for i in range(1, n_sab+1)]].sum().sum())
        st.metric("Membros (ME)", me)
        st.metric("Freq. Ativa (FA)", fa)
    with c2:
        vi = int(df_p_plot[[f"S{i}_VI" for i in range(1, n_sab+1)]].sum().sum())
        st.metric("Visitantes (VI)", vi)
        st.markdown(f'<div class="publico-total-box">Total: {me+fa+vi}</div>', unsafe_allow_html=True)

# --- ABA 2: VISÃO GERAL DÍZIMO ---
with tab2:
    df_pago = st.session_state.df[st.session_state.df["Pago"] == "Sim"]
    st.markdown(f'<div class="dizimo-destaque"><p class="dizimo-titulo">💰 Total Acumulado</p><p class="dizimo-valor">{formatar_brl(df_pago["Valor"].sum())}</p></div>', unsafe_allow_html=True)
    
    m_v = st.selectbox("Status do Mês:", MESES_ORDEM[:7], key="v_diz")
    
    # Gráficos um abaixo do outro no mobile automaticamente pelo st.columns
    c1, c2 = st.columns(2)
    with c1:
        df_d = df_pago.groupby("Mês", sort=False)["Valor"].sum().reindex(MESES_ORDEM[:7]).fillna(0).reset_index()
        fig_l = px.line(df_d, x="Mês", y="Valor", markers=True, title="Evolução Mensal")
        fig_l.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_l, use_container_width=True)
    with c2:
        fig_pie = px.pie(st.session_state.df[st.session_state.df["Mês"] == m_v], names='Pago', hole=0.5, color_discrete_map={'Sim': '#00D4FF', 'Não': '#e74c3c'})
        fig_pie.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

# --- ABA 3: ADMINISTRAÇÃO ---
if is_admin:
    with tab3:
        with st.expander("➕ Cadastrar/Excluir Líder"):
            col_cad, col_exclui = st.columns(2)
            with col_cad:
                with st.form("form_novo_lider"):
                    novo_nome = st.text_input("Nome do Líder:")
                    if st.form_submit_button("Adicionar", use_container_width=True):
                        if novo_nome:
                            novas = pd.DataFrame([{"Mês": m, "Líder": novo_nome, "Valor": 0.0, "Pago": "Não"} for m in MESES_ORDEM[:7]])
                            st.session_state.df = pd.concat([st.session_state.df, novas], ignore_index=True)
                            st.session_state.df.to_csv(ARQUIVO_DIZIMOS, index=False); st.rerun()
            with col_exclui:
                lider_para_excluir = st.selectbox("Remover Líder:", [""] + sorted(st.session_state.df["Líder"].unique()))
                if st.button("❌ Excluir", type="primary", use_container_width=True) and lider_para_excluir:
                    st.session_state.df = st.session_state.df[st.session_state.df["Líder"] != lider_para_excluir]
                    st.session_state.df.to_csv(ARQUIVO_DIZIMOS, index=False); st.rerun()

        st.markdown("### 📝 Lançar Valores")
        m_l = st.selectbox("Mês:", MESES_ORDEM[:7], key="l_diz")
        df_edicao = st.session_state.df[st.session_state.df["Mês"] == m_l].copy()
        
        df_editado = st.data_editor(df_edicao, use_container_width=True, hide_index=True,
            column_config={
                "Mês": None, "Líder": st.column_config.Column(disabled=True),
                "Valor": st.column_config.NumberColumn("R$", format="%.2f", width="small"),
                "Pago": st.column_config.SelectboxColumn("Status", options=["Sim", "Não"], width="small")
            })
        
        if st.button("💾 Salvar Lançamentos", use_container_width=True):
            idx_mes = st.session_state.df[st.session_state.df["Mês"] == m_l].index
            st.session_state.df.loc[idx_mes, ["Valor", "Pago"]] = df_editado[["Valor", "Pago"]].values
            st.session_state.df.to_csv(ARQUIVO_DIZIMOS, index=False); st.success("Salvo!"); st.rerun()
