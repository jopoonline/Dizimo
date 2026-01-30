import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página: wide para PC e ícone de igreja
st.set_page_config(page_title="Gestão Igreja PRO", layout="wide", page_icon="⛪")

# --- BLOCO DE ESTILO (CSS) PARA CORREÇÃO VISUAL ---
st.markdown("""
    <style>
    /* Força a visibilidade das métricas (Total Acumulado) */
    [data-testid="stMetricValue"] {
        color: #1f1f1f !important;
        font-weight: bold;
        font-size: 2rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5f6368 !important;
        font-weight: 500 !important;
    }
    .stMetric {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
    }
    /* Melhora a visibilidade na barra lateral */
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] label {
        color: #1f1f1f !important;
    }
    /* Estilo para os botões */
    .stButton button {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES INICIAIS ---
SENHA_ADMIN = "1234"
ARQUIVO_DADOS = "dados_dizimos.csv"
MESES_ORDEM = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho"]

@st.cache_data
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS)
    else:
        # Cria base inicial se o arquivo não existir
        nomes = [f"Líder {i:02d}" for i in range(1, 26)]
        return pd.DataFrame({
            "Mês": [m for m in MESES_ORDEM for _ in nomes],
            "Líder": nomes * len(MESES_ORDEM),
            "Valor": 0.0,
            "Pago": "Não"
        })

# Inicialização do estado da sessão
if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1043/1043323.png", width=80)
    st.title("Administração")
    senha_digitada = st.text_input("Senha de Acesso:", type="password")
    is_admin = senha_digitada == SENHA_ADMIN
    
    if is_admin:
        st.success("🔓 Modo Editor Ativo")
    else:
        st.warning("🔒 Modo Visualização")

st.title("⛪ Gestão Financeira de Líderes")

# --- SISTEMA DE ABAS ---
if is_admin:
    abas = st.tabs(["📊 Visão Geral", "📝 Lançamentos Mensais"])
else:
    abas = st.tabs(["📊 Visão Geral"])

# --- ABA 1: VISUALIZAÇÃO DE RESULTADOS ---
with abas[0]:
    df_pago = st.session_state.df[st.session_state.df["Pago"] == "Sim"]
    total_geral = df_pago["Valor"].sum()
    
    # Cartão de Destaque
    st.metric(label="💰 Total Acumulado (Jan a Jul)", 
              value=f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("---")
    
    # Layout Responsivo: Lado a lado no PC, Empilhado no Celular
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Evolução Mensal")
        df_mes_grafico = df_pago.groupby("Mês", sort=False)["Valor"].sum().reindex(MESES_ORDEM).fillna(0).reset_index()
        
        fig_linha = px.line(df_mes_grafico, x="Mês", y="Valor", text="Valor", 
                            markers=True, color_discrete_sequence=["#2ecc71"])
        fig_linha.update_traces(texttemplate='R$ %{y:.0f}', textposition="top center")
        fig_linha.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                                xaxis_title="", yaxis_title="", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_linha, use_container_width=True)

    with col2:
        mes_view = st.selectbox("Status detalhado de:", MESES_ORDEM, key="view_mes")
        st.subheader(f"📊 {mes_view}")
        df_pizza = st.session_state.df[st.session_state.df["Mês"] == mes_view]
        
        fig_pizza = px.pie(df_pizza, names='Pago', color='Pago', 
                           color_discrete_map={'Sim': '#27ae60', 'Não': '#e74c3c'}, hole=0.5)
        fig_pizza.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
        st.plotly_chart(fig_pizza, use_container_width=True)

# --- ABA 2: EDITOR (PROTEGIDA POR SENHA) ---
if is_admin:
    with abas[1]:
        st.subheader("✏️ Atualização de Lançamentos")
        st.write("Selecione o mês, altere os dados na tabela e clique no botão azul para salvar.")
        
        mes_edit = st.selectbox("Mês de edição:", MESES_ORDEM, key="edit_mes")
        
        # Filtramos apenas o mês selecionado para editar
        df_filtrado = st.session_state.df[st.session_state.df["Mês"] == mes_edit].copy()

        df_editado = st.data_editor(
            df_filtrado, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Pago": st.column_config.SelectboxColumn("✅ Pago", options=["Sim", "Não"], required=True),
                "Valor": st.column_config.NumberColumn("💵 Valor (R$)", format="%.2f", min_value=0),
                "Líder": st.column_config.TextColumn("👤 Nome do Líder"),
                "Mês": st.column_config.Column(disabled=True)
            }
        )

        if st.button("💾 Salvar Alterações Agora", use_container_width=True, type="primary"):
            # Atualiza o DataFrame principal com as mudanças feitas no filtro
            # Encontramos os índices das linhas que foram editadas e atualizamos no df original
            st.session_state.df.loc[st.session_state.df["Mês"] == mes_edit, :] = df_editado
            
            # Salva no arquivo CSV
            st.session_state.df.to_csv(ARQUIVO_DADOS, index=False)
            
            # Limpa cache para garantir que os gráficos atualizem
            st.cache_data.clear()
            
            st.success(f"Dados de {mes_edit} salvos com sucesso!")
            st.rerun()
