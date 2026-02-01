import streamlit as st
import pandas as pd
import plotly.express as px
import os
import calendar
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# --- ESTILO CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 15px; border-radius: 12px; border: 1px solid #334155;
        text-align: center; margin-bottom: 10px;
    }
    .metric-value { color: #00D4FF; font-size: 24px; font-weight: 800; margin: 0; }
    .metric-label { color: #94A3B8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
    .type-label { 
        background-color: #00D4FF; color: #0F172A; padding: 2px 8px; 
        border-radius: 5px; font-size: 12px; font-weight: bold; margin-bottom: 8px; display: inline-block;
    }
    .main-title {
        background: linear-gradient(90deg, #00D4FF 0%, #0072FF 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 900; font-size: 38px; text-align: center; margin-bottom: 20px;
    }
    .edit-section {
        background-color: #1E293B; padding: 20px; border-radius: 15px;
        border-top: 3px solid #00D4FF; margin-top: 30px;
    }
    .pending-card {
        background-color: #450a0a; border: 1px solid #dc2626;
        padding: 15px; border-radius: 10px; color: #fecaca; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
ARQUIVO_DIZIMOS = "dados_dizimos.csv"
ARQUIVO_FREQ = "frequencia_celula_2026.csv"
MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DISCIPULADORES = ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"]
TIPOS = ["Célula", "Culto de Jovens"]
CORES_AZYK = {"ME": "#00D4FF", "FA": "#0072FF", "VI": "#00E6CC"}

meses_map = {m: list(calendar.month_name)[i+1] for i, m in enumerate(MESES_ORDEM)}
mes_atual_numero = datetime.now().month

# --- FUNÇÕES DE DADOS COM TRATAMENTO DE ERRO ---
def carregar_dizimos_inicial():
    if os.path.exists(ARQUIVO_DIZIMOS):
        try:
            return pd.read_csv(ARQUIVO_DIZIMOS)
        except:
            pass
    lideres_padrao = [f"Líder {i:02d}" for i in range(1, 26)]
    data = []
    for m in MESES_ORDEM[:7]:
        for l in lideres_padrao:
            data.append({"Mês": m, "Líder": l, "Valor": 0.0, "Pago": "Não"})
    return pd.DataFrame(data)

def inicializar_frequencia():
    if os.path.exists(ARQUIVO_FREQ):
        try:
            df = pd.read_csv(ARQUIVO_FREQ)
            if "Discipulador" in df.columns:
                return df
        except:
            pass
    data = []
    for mes in MESES_ORDEM:
        for discipulador in DISCIPULADORES:
            for tipo in TIPOS:
                row = {"Mês": mes, "Discipulador": discipulador, "Tipo": tipo}
                for i in range(1, 6):
                    row[f"S{i}_ME"] = 0
                    row[f"S{i}_FA"] = 0
                    row[f"S{i}_VI"] = 0
                data.append(row)
    df_new = pd.DataFrame(data)
    df_new.to_csv(ARQUIVO_FREQ, index=False)
    return df_new

# Inicialização do State
if 'df' not in st.session_state:
    st.session_state.df = carregar_dizimos_inicial()
if 'df_freq' not in st.session_state:
    st.session_state.df_freq = inicializar_frequencia()

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_sabados_do_mes(mes_nome, ano=2026):
    mes_num = list(calendar.month_name).index(meses_map[mes_nome])
    cal = calendar.monthcalendar(ano, mes_num)
    return [f"{semana[calendar.SATURDAY]:02d}/{mes_num:02d}" for semana in cal if semana[calendar.SATURDAY] != 0]

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔐 Acesso")
    senha = st.text_input("Senha Administrativa:", type="password")
    is_admin = (senha == "1234")

st.markdown('<p class="main-title">⛪ RADICAIS LIVRES 2026</p>', unsafe_allow_html=True)

# Define abas
if is_admin:
    tab1, tab2, tab3 = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    tab1, tab2 = st.tabs(["📊 Frequência", "💰 Finanças"])

# --- ABA 1: FREQUÊNCIA ---
with tab1:
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        mes_sel = st.selectbox("📅 Selecione o Mês:", MESES_ORDEM, key="f_mes")
    with col_sel2:
        disc_filtro = st.multiselect("👥 Filtrar Discipuladores:", DISCIPULADORES, default=DISCIPULADORES)

    sabados = obter_sabados_do_mes(mes_sel)
    n_sab = len(sabados)
    
    # Filtro robusto
    df_full = st.session_state.df_freq
    df_mes_f = df_full[(df_full["Mês"] == mes_sel) & (df_full["Discipulador"].isin(disc_filtro))].copy().reset_index(drop=True)

    def render_metrics(df_filter, titulo_tipo):
        cols_me = [f"S{i}_ME" for i in range(1, n_sab+1)]
        cols_fa = [f"S{i}_FA" for i in range(1, n_sab+1)]
        cols_vi = [f"S{i}_VI" for i in range(1, n_sab+1)]
        me = int(df_filter[cols_me].sum().sum())
        fa = int(df_filter[cols_fa].sum().sum())
        vi = int(df_filter[cols_vi].sum().sum())
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Membros</p><p class="metric-value">{me}</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Freq. Ativa</p><p class="metric-value">{fa}</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Visitantes</p><p class="metric-value">{vi}</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card" style="border-color:#00D4FF"><span class="type-label">{titulo_tipo}</span><p class="metric-label">Total</p><p class="metric-value">{me+fa+vi}</p></div>', unsafe_allow_html=True)

    st.write("### 🏠 Resumo de Células")
    render_metrics(df_mes_f[df_mes_f["Tipo"] == "Célula"], "CÉLULA")
    st.write("### 🎸 Resumo de Culto de Jovens")
    render_metrics(df_mes_f[df_mes_f["Tipo"] == "Culto de Jovens"], "CULTO")
    st.divider()

    # Gráficos de Frequência
    l_p = []
    for _, r in df_mes_f.iterrows():
        for i in range(1, n_sab + 1):
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "ME", "Valor": r[f"S{i}_ME"]})
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "FA", "Valor": r[f"S{i}_FA"]})
            l_p.append({"Sábado": sabados[i-1], "Tipo": r["Tipo"], "Indicador": "VI", "Valor": r[f"S{i}_VI"]})
    
    if l_p:
        df_p = pd.DataFrame(l_p).groupby(["Sábado", "Tipo", "Indicador"])["Valor"].sum().reset_index()
        st.plotly_chart(px.bar(df_p, x="Sábado", y="Valor", color="Indicador", barmode="group", facet_col="Tipo", text="Valor", color_discrete_map=CORES_AZYK).update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=380), use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_avg = df_p.groupby(["Tipo", "Indicador"])["Valor"].mean().reset_index()
            st.plotly_chart(px.line(df_avg, x="Indicador", y="Valor", color="Tipo", markers=True, text="Valor", title="Média de Público").update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=350), use_container_width=True)
        with col_g2:
            idx_sel_f = MESES_ORDEM.index(mes_sel)
            janela = MESES_ORDEM[max(0, idx_sel_f - 3) : idx_sel_f + 1]
            l_evo = []
            for m in janela:
                n_s = len(obter_sabados_do_mes(m))
                for d in disc_filtro:
                    for t in TIPOS:
                        cols_e = [f"S{i}_{ind}" for i in range(1, 6) for ind in ["ME", "FA", "VI"]]
                        total_v = df_full[(df_full["Mês"] == m) & (df_full["Discipulador"] == d) & (df_full["Tipo"] == t)][cols_e].sum().sum()
                        l_evo.append({"Mês": m, "Discipulador": d, "Tipo": t, "Média": round(total_v/n_s, 1) if n_s > 0 else 0})
            if l_evo:
                df_evo = pd.DataFrame(l_evo)
                df_evo["Mês"] = pd.Categorical(df_evo["Mês"], categories=janela, ordered=True)
                st.plotly_chart(px.line(df_evo, x="Mês", y="Média", color="Discipulador", facet_row="Tipo", markers=True, title="Evolução Mensal").update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", height=400), use_container_width=True)

    # Tabela Final
    st.markdown('<div class="edit-section">', unsafe_allow_html=True)
    st.markdown("### 📝 Lançamento de Dados")
    modo_edicao = st.toggle("Habilitar Tabela para Edição", value=False)
    
    conf_f = {"Mês": None, "Discipulador": st.column_config.Column(disabled=True), "Tipo": st.column_config.Column(disabled=True)}
    for i in range(1, 6):
        if i <= n_sab:
            conf_f[f"S{i}_ME"] = st.column_config.NumberColumn(f"{sabados[i-1]}|ME")
            conf_f[f"S{i}_FA"] = st.column_config.NumberColumn(f"{sabados[i-1]}|FA")
            conf_f[f"S{i}_VI"] = st.column_config.NumberColumn(f"{sabados[i-1]}|VI")
        else:
            conf_f[f"S{i}_ME"] = conf_f[f"S{i}_FA"] = conf_f[f"S{i}_VI"] = None

    if modo_edicao:
        df_ed_f = st.data_editor(df_mes_f, column_config=conf_f, use_container_width=True, hide_index=True)
        if st.button("💾 Salvar Frequência"):
            for _, row in df_ed_f.iterrows():
                idx = st.session_state.df_freq[(st.session_state.df_freq["Mês"] == row["Mês"]) & (st.session_state.df_freq["Discipulador"] == row["Discipulador"]) & (st.session_state.df_freq["Tipo"] == row["Tipo"])].index
                st.session_state.df_freq.loc[idx, :] = row.values
            st.session_state.df_freq.to_csv(ARQUIVO_FREQ, index=False)
            st.success("Salvo!"); st.rerun()
    else:
        st.dataframe(df_mes_f, column_config=conf_f, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: FINANÇAS ---
with tab2:
    df_pago = st.session_state.df[st.session_state.df["Pago"] == "Sim"]
    st.markdown(f'<div style="background:linear-gradient(90deg, #1E293B, #0072FF); padding:25px; border-radius:15px; border-left:5px solid #00D4FF; margin-bottom:20px;"><p class="metric-label" style="color:#cbd5e1">Total Acumulado Dizímos (2026)</p><p style="font-size:36px; font-weight:900; margin:0;">{formatar_brl(df_pago["Valor"].sum())}</p></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        df_d = df_pago.groupby("Mês", sort=False)["Valor"].sum().reindex(MESES_ORDEM[:7]).fillna(0).reset_index()
        fig_l = px.line(df_d, x="Mês", y="Valor", text="Valor", markers=True, title="Arrecadação Mensal")
        fig_l.update_traces(texttemplate='R$ %{y:,.2f}', textposition="top center", line_color="#00D4FF")
        fig_l.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig_l, use_container_width=True)
    with c2:
        m_v = st.selectbox("Status Mensal:", MESES_ORDEM[:7], key="v_diz")
        st.plotly_chart(px.pie(st.session_state.df[st.session_state.df["Mês"] == m_v], names='Pago', hole=0.5, color_discrete_map={'Sim': '#00D4FF', 'Não': '#EF4444'}), use_container_width=True)

# --- ABA 3: ADMIN ---
if is_admin:
    with tab3:
        st.markdown("### ⚠️ Verificação de Pendências")
        mes_pendencia = st.selectbox("Selecione o Mês para verificar:", MESES_ORDEM[:7], index=max(0, mes_atual_numero-2))
        df_pendentes = st.session_state.df[(st.session_state.df["Mês"] == mes_pendencia) & (st.session_state.df["Pago"] == "Não")].copy()
        
        if (MESES_ORDEM.index(mes_pendencia) + 1) < mes_atual_numero:
            st.markdown(f'<div class="pending-card"><b>ATENÇÃO:</b> O mês de {mes_pendencia} encerrou com pendências.</div>', unsafe_allow_html=True)
        
        if not df_pendentes.empty:
            st.warning(f"Líderes pendentes em {mes_pendencia}:")
            st.table(df_pendentes[["Líder", "Pago"]])
        else:
            st.success(f"✅ Tudo em dia em {mes_pendencia}!")

        st.divider()
        st.markdown("### 📝 Gestão de Dízimos")
        m_l = st.selectbox("Mês para Lançamento:", MESES_ORDEM[:7], key="admin_mes")
        df_ed_diz = st.data_editor(st.session_state.df[st.session_state.df["Mês"] == m_l], use_container_width=True, hide_index=True,
            column_config={"Mês": None, "Líder": st.column_config.Column(disabled=True), "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"), "Pago": st.column_config.SelectboxColumn("Status", options=["Sim", "Não"])})
        
        if st.button("💾 Salvar Dízimos"):
            idx = st.session_state.df[st.session_state.df["Mês"] == m_l].index
            st.session_state.df.loc[idx, ["Valor", "Pago"]] = df_ed_diz[["Valor", "Pago"]].values
            st.session_state.df.to_csv(ARQUIVO_DIZIMOS, index=False)
            st.success("Salvo!"); st.rerun()
