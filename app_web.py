"""Radicais Livres 2026 — controle de frequência e dízimos.

Os dados ficam nos mesmos arquivos de sempre: dados_dizimos.csv e
frequencia_celula_2026.csv (com cópia de segurança em backups/ a cada salvamento).
"""
import calendar
import hmac
import os
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Radicais Livres 2026", layout="wide", page_icon="⛪")

# ───────────────────────── CONFIGURAÇÕES ─────────────────────────
ANO = 2026
ARQUIVO_DIZIMOS = "dados_dizimos.csv"
ARQUIVO_FREQ = "frequencia_celula_2026.csv"
PASTA_BACKUP = "backups"
MAX_BACKUPS = 30

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DISCIPULADORES = ["André e Larissa", "Lucas e Rosana", "Deric e Nayara"]
TIPOS = ["Célula", "Culto de Jovens"]
INDICADORES = {"ME": "Membros", "FA": "Freq. Ativa", "VI": "Visitantes"}
CORES_IND = {"Membros": "#00D4FF", "Freq. Ativa": "#3B82F6", "Visitantes": "#00E6CC"}
CORES_TIPO = {"Célula": "#00D4FF", "Culto de Jovens": "#A78BFA"}
CHAVE_FREQ = ["Mês", "Discipulador", "Tipo"]
COLS_S = [f"S{i}_{ind}" for i in range(1, 6) for ind in INDICADORES]

AGORA = datetime.now(ZoneInfo("America/Sao_Paulo"))
if AGORA.year == ANO:
    IDX_MES_ATUAL = AGORA.month - 1
else:
    IDX_MES_ATUAL = 11 if AGORA.year > ANO else 0


def mes_encerrado(idx_mes):
    return (AGORA.year, AGORA.month) > (ANO, idx_mes + 1)


def sabados_do_mes(idx_mes):
    return [f"{sem[calendar.SATURDAY]:02d}/{idx_mes + 1:02d}"
            for sem in calendar.monthcalendar(ANO, idx_mes + 1) if sem[calendar.SATURDAY]]


SABADOS = {m: sabados_do_mes(i) for i, m in enumerate(MESES)}


def _versao_streamlit():
    try:
        return tuple(int(p) for p in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


# Versões novas do Streamlit trocaram use_container_width por width="stretch".
LARGURA = {"width": "stretch"} if _versao_streamlit() >= (1, 52) else {"use_container_width": True}
SEM_BARRA = {"displayModeBar": False}


def _segredo(nome, padrao=None):
    try:
        if hasattr(st.secrets, "load_if_toml_exists") and not st.secrets.load_if_toml_exists():
            return padrao
        return st.secrets[nome]
    except Exception:
        return padrao


SENHA_ADMIN = _segredo("senha_admin")

# ───────────────────────── ESTILO ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, .stApp, .stApp p, .stApp label, .stApp input, .stApp button { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 15% -10%, #12284A 0%, rgba(11,18,32,0) 60%), #0B1220; color: #E2E8F0; }
.stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #E2E8F0; }
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }

.topo { text-align: center; margin-bottom: 1.4rem; }
.topo-titulo { background: linear-gradient(90deg, #00D4FF 0%, #3B82F6 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; font-size: clamp(26px, 5vw, 40px); letter-spacing: -0.5px; line-height: 1.1; margin: 0; }
.topo-sub { color: #94A3B8 !important; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; margin: 6px 0 0 0; }

.secao { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; font-size: 18px; font-weight: 700; color: #F1F5F9; margin: 1.4rem 0 .7rem 0; }
.secao small { font-size: 12px; font-weight: 500; color: #94A3B8; }

.kpi-grade { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 6px; }
.kpi { background: linear-gradient(145deg, #15223D 0%, #0E182C 100%); border: 1px solid #22304D; border-radius: 16px; padding: 16px 18px; }
.kpi.destaque { border-color: rgba(0,212,255,.55); box-shadow: 0 0 0 1px rgba(0,212,255,.12), 0 10px 30px -18px rgba(0,212,255,.6); }
.kpi-rotulo { color: #94A3B8; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; }
.kpi-valor { color: #F8FAFC; font-size: 28px; font-weight: 800; line-height: 1.25; font-variant-numeric: tabular-nums; }
.kpi.destaque .kpi-valor { color: #00D4FF; }
.kpi-detalhe { color: #94A3B8; font-size: 12px; min-height: 18px; }
.delta { display: block; font-weight: 600; margin-top: 2px; }
.delta.sobe { color: #34D399; } .delta.desce { color: #F87171; } .delta.neutro { color: #94A3B8; }

.heroi { background: linear-gradient(100deg, #15223D 0%, #0B4FB3 100%); border: 1px solid #22304D; border-left: 5px solid #00D4FF; border-radius: 18px; padding: 24px 26px; margin-bottom: 14px; }
.heroi-rotulo { color: #CBD5E1; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; }
.heroi-valor { color: #FFFFFF; font-size: clamp(28px, 6vw, 40px); font-weight: 900; line-height: 1.2; font-variant-numeric: tabular-nums; }

.alerta { background: rgba(127,29,29,.35); border: 1px solid #DC2626; color: #FECACA; padding: 14px 16px; border-radius: 12px; margin-bottom: 12px; }
.nota { background: #111C33; border: 1px solid #22304D; color: #CBD5E1; padding: 12px 16px; border-radius: 12px; margin-bottom: 12px; font-size: 14px; }
.nota.ok { border-color: rgba(52,211,153,.5); } .nota.atencao { border-color: rgba(251,191,36,.6); }

.stTabs [data-baseweb="tab-list"] { gap: 6px; background: #111C33; padding: 6px; border-radius: 14px; border: 1px solid #22304D; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; height: auto; }
.stTabs [data-baseweb="tab"] p { color: #94A3B8; font-weight: 600; font-size: 15px; }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, #00D4FF 0%, #3B82F6 100%); }
.stTabs [aria-selected="true"] p { color: #06121F; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

[data-testid="stForm"] { background: #111C33; border: 1px solid #22304D; border-radius: 16px; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button { background: linear-gradient(90deg, #00D4FF 0%, #3B82F6 100%); color: #06121F; border: 0; border-radius: 10px; font-weight: 700; padding: .5rem 1.2rem; }
.stButton > button p, .stDownloadButton > button p, [data-testid="stFormSubmitButton"] > button p { color: #06121F; font-weight: 700; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { filter: brightness(1.1); color: #06121F; }
.stButton > button:disabled { opacity: .45; }
[data-testid="stSidebar"] { background: #0E182C; border-right: 1px solid #22304D; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────── FORMATAÇÃO ─────────────────────────
def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def num(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def cartao(rotulo, valor, detalhe="", destaque=False):
    classe = "kpi destaque" if destaque else "kpi"
    return (f'<div class="{classe}"><div class="kpi-rotulo">{rotulo}</div>'
            f'<div class="kpi-valor">{valor}</div>'
            f'<div class="kpi-detalhe">{detalhe or "&nbsp;"}</div></div>')


def grade(cartoes):
    st.markdown('<div class="kpi-grade">' + "".join(cartoes) + '</div>', unsafe_allow_html=True)


def secao(titulo, detalhe=""):
    extra = f"<small>{detalhe}</small>" if detalhe else ""
    st.markdown(f'<div class="secao">{titulo} {extra}</div>', unsafe_allow_html=True)


def delta_html(atual, anterior, referencia):
    if not anterior:
        return ""
    pct = (atual - anterior) / anterior * 100
    if abs(pct) < 0.5:
        return f'<span class="delta neutro">● igual a {referencia}</span>'
    seta, classe = ("▲", "sobe") if pct > 0 else ("▼", "desce")
    return f'<span class="delta {classe}">{seta} {abs(pct):.0f}% vs {referencia}</span>'


def estilo(fig, altura=380):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", family="Inter, sans-serif", size=13),
        height=altura, margin=dict(l=10, r=10, t=36, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.16, xanchor="center", x=0.5, title_text=""),
        hoverlabel=dict(bgcolor="#0E182C", font_color="#F8FAFC", bordercolor="#22304D"),
        bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor="#334155", title_text="")
    fig.update_yaxes(gridcolor="rgba(148,163,184,.14)", zeroline=False, title_text="")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=14, color="#F1F5F9")))
    return fig


# ───────────────────────── DADOS: VALIDAÇÃO ─────────────────────────
class ErroDados(Exception):
    pass


def _numerico(serie):
    numero = pd.to_numeric(serie, errors="coerce")
    if numero.isna().any():
        texto = (serie.astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False)
                 .str.replace(",", ".", regex=False).str.strip())
        numero = numero.fillna(pd.to_numeric(texto, errors="coerce"))
    return numero.fillna(0)


def normalizar_dizimos(df):
    """Valida o formato e completa os meses que faltam, sem tocar no que já existe."""
    faltando = {"Mês", "Líder", "Valor", "Pago"} - set(df.columns)
    if faltando:
        raise ErroDados("faltam as colunas " + ", ".join(sorted(faltando)) + " nos dados de dízimos")
    df = df.copy()
    df["Mês"] = df["Mês"].astype(str).str.strip()
    df["Líder"] = df["Líder"].astype(str).str.strip()
    lideres = [l for l in dict.fromkeys(df["Líder"]) if l]
    existentes = set(zip(df["Mês"], df["Líder"]))
    novas = [{"Mês": m, "Líder": l, "Valor": 0.0, "Pago": "Não"}
             for m in MESES for l in lideres if (m, l) not in existentes]
    if novas:
        df = pd.concat([df, pd.DataFrame(novas)], ignore_index=True)
    df["Valor"] = _numerico(df["Valor"]).astype(float)
    df["Pago"] = df["Pago"].astype(str).str.strip().str.lower().map(lambda v: "Sim" if v == "sim" else "Não")
    ordem_m = {m: i for i, m in enumerate(MESES)}
    ordem_l = {l: i for i, l in enumerate(lideres)}
    df = (df.assign(_m=df["Mês"].map(ordem_m).fillna(99), _l=df["Líder"].map(ordem_l).fillna(9999))
            .sort_values(["_m", "_l"], kind="stable").drop(columns=["_m", "_l"]).reset_index(drop=True))
    return df


def normalizar_freq(df):
    faltando = set(CHAVE_FREQ) - set(df.columns)
    if faltando:
        raise ErroDados("faltam as colunas " + ", ".join(sorted(faltando)) + " nos dados de frequência")
    df = df.copy()
    for c in CHAVE_FREQ:
        df[c] = df[c].astype(str).str.strip()
    for c in COLS_S:
        if c not in df.columns:
            df[c] = 0
    discs = list(dict.fromkeys(DISCIPULADORES + [d for d in df["Discipulador"] if d]))
    existentes = set(zip(df["Mês"], df["Discipulador"], df["Tipo"]))
    novas = [{"Mês": m, "Discipulador": d, "Tipo": t}
             for m in MESES for d in discs for t in TIPOS if (m, d, t) not in existentes]
    if novas:
        df = pd.concat([df, pd.DataFrame(novas)], ignore_index=True)
    for c in COLS_S:
        df[c] = _numerico(df[c]).round().clip(lower=0).astype(int)
    ordem_m = {m: i for i, m in enumerate(MESES)}
    ordem_d = {d: i for i, d in enumerate(discs)}
    ordem_t = {t: i for i, t in enumerate(TIPOS)}
    df = (df.assign(_m=df["Mês"].map(ordem_m).fillna(99), _d=df["Discipulador"].map(ordem_d).fillna(99),
                    _t=df["Tipo"].map(ordem_t).fillna(99))
            .sort_values(["_m", "_d", "_t"], kind="stable").drop(columns=["_m", "_d", "_t"]).reset_index(drop=True))
    extras = [c for c in df.columns if c not in CHAVE_FREQ + COLS_S]
    return df[CHAVE_FREQ + COLS_S + extras]


def padrao_dizimos():
    base = pd.DataFrame([{"Mês": MESES[0], "Líder": f"Líder {i:02d}", "Valor": 0.0, "Pago": "Não"}
                         for i in range(1, 26)])
    return normalizar_dizimos(base)


def padrao_freq():
    return normalizar_freq(pd.DataFrame(columns=CHAVE_FREQ))


NORMALIZAR = {ARQUIVO_DIZIMOS: normalizar_dizimos, ARQUIVO_FREQ: normalizar_freq}
PADRAO = {ARQUIVO_DIZIMOS: padrao_dizimos, ARQUIVO_FREQ: padrao_freq}


# ───────────────────────── DADOS: ARMAZENAMENTO ─────────────────────────
def _ler_csv(nome):
    if not os.path.exists(nome) or os.path.getsize(nome) == 0:
        return None
    return pd.read_csv(nome, encoding="utf-8-sig")


def _gravar_csv(nome, df):
    if os.path.exists(nome):
        os.makedirs(PASTA_BACKUP, exist_ok=True)
        carimbo = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y%m%d-%H%M%S")
        shutil.copy2(nome, os.path.join(PASTA_BACKUP, f"{carimbo}_{nome}"))
        antigos = sorted(f for f in os.listdir(PASTA_BACKUP) if f.endswith("_" + nome))
        for velho in antigos[:-MAX_BACKUPS]:
            os.remove(os.path.join(PASTA_BACKUP, velho))
    temporario = nome + ".tmp"
    df.to_csv(temporario, index=False)
    os.replace(temporario, nome)


def carregar_atual(nome):
    """Lê direto do arquivo. Se a leitura falhar, levanta erro: nunca devolve tabela zerada."""
    try:
        df = _ler_csv(nome)
    except Exception as erro:
        raise ErroDados(f"não consegui ler os dados ({nome}): {erro}") from erro
    if df is None:
        return PADRAO[nome]()
    return NORMALIZAR[nome](df)


@st.cache_data(ttl=30, show_spinner="Carregando dados…")
def carregar(nome):
    return carregar_atual(nome)


def gravar(nome, df):
    _gravar_csv(nome, df)
    carregar.clear()


def salvar_frequencia(editado):
    atual = carregar_atual(ARQUIVO_FREQ)  # relê antes de gravar: não apaga o que outra pessoa salvou
    for _, linha in editado.iterrows():
        filtro = ((atual["Mês"] == linha["Mês"]) & (atual["Discipulador"] == linha["Discipulador"])
                  & (atual["Tipo"] == linha["Tipo"]))
        for c in COLS_S:
            valor = pd.to_numeric(linha[c], errors="coerce")
            atual.loc[filtro, c] = 0 if pd.isna(valor) else max(0, int(round(valor)))
    gravar(ARQUIVO_FREQ, atual)


def salvar_dizimos(mes, editado):
    atual = carregar_atual(ARQUIVO_DIZIMOS)
    for _, linha in editado.iterrows():
        filtro = (atual["Mês"] == mes) & (atual["Líder"] == linha["Líder"])
        valor = pd.to_numeric(linha["Valor"], errors="coerce")
        atual.loc[filtro, "Valor"] = 0.0 if pd.isna(valor) else float(valor)
        atual.loc[filtro, "Pago"] = "Sim" if linha["Pago"] == "Sim" else "Não"
    gravar(ARQUIVO_DIZIMOS, atual)


def formato_longo(df):
    longo = df.melt(id_vars=CHAVE_FREQ, value_vars=COLS_S, var_name="col", value_name="Valor")
    longo["Semana"] = longo["col"].str[1].astype(int)
    longo["Indicador"] = longo["col"].str[3:]
    n_sab = longo["Mês"].map({m: len(s) for m, s in SABADOS.items()}).fillna(0)
    return longo[longo["Semana"] <= n_sab].drop(columns="col")


def resumo(base, mes, tipo):
    """Totais por indicador e quantidade de sábados que têm lançamento."""
    f = base[(base["Mês"] == mes) & (base["Tipo"] == tipo)]
    por_sabado = f.groupby("Semana")["Valor"].sum()
    totais = f.groupby("Indicador")["Valor"].sum().reindex(list(INDICADORES)).fillna(0)
    return totais, int((por_sabado > 0).sum())


# ───────────────────────── CARGA ─────────────────────────
try:
    df_diz = carregar(ARQUIVO_DIZIMOS)
    df_freq = carregar(ARQUIVO_FREQ)
except Exception as erro:
    st.error(f"⚠️ Os dados não puderam ser carregados: {erro}")
    st.info("Nada foi alterado. O app fica bloqueado para não gravar por cima dos seus dados. "
            "Recarregue a página; se o erro continuar, confira o arquivo CSV.")
    st.stop()

if "rev" not in st.session_state:
    st.session_state.rev = 0


def concluir(mensagem):
    st.session_state.rev += 1
    st.session_state.aviso = mensagem
    st.rerun()


# ───────────────────────── CABEÇALHO ─────────────────────────
with st.sidebar:
    st.markdown("### 🔐 Acesso")
    senha = st.text_input("Senha administrativa", type="password")
    is_admin = bool(senha) and hmac.compare_digest(senha.encode(), str(SENHA_ADMIN or "1234").encode())
    if senha and not is_admin:
        st.caption("Senha incorreta.")

st.markdown('<div class="topo"><p class="topo-titulo">⛪ RADICAIS LIVRES 2026</p>'
            '<p class="topo-sub">Frequência e dízimos</p></div>', unsafe_allow_html=True)

if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

if is_admin:
    aba_freq, aba_fin, aba_admin = st.tabs(["📊 Frequência", "💰 Finanças", "⚙️ Admin"])
else:
    aba_freq, aba_fin = st.tabs(["📊 Frequência", "💰 Finanças"])
    aba_admin = None

# ───────────────────────── ABA 1: FREQUÊNCIA ─────────────────────────
with aba_freq:
    discs_todos = list(dict.fromkeys(df_freq["Discipulador"]))
    c1, c2 = st.columns([1, 2])
    mes_sel = c1.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="f_mes")
    disc_sel = c2.multiselect("👥 Discipuladores", discs_todos, default=discs_todos, key="f_disc")

    idx_mes = MESES.index(mes_sel)
    sabados = SABADOS[mes_sel]
    n_sab = len(sabados)
    mes_ant = MESES[idx_mes - 1] if idx_mes > 0 else None

    if not disc_sel:
        st.info("Selecione pelo menos um discipulador para ver os dados.")
    else:
        longo = formato_longo(df_freq)
        longo_sel = longo[longo["Discipulador"].isin(disc_sel)]

        for tipo, titulo in (("Célula", "🏠 Células"), ("Culto de Jovens", "🎸 Culto de Jovens")):
            totais, n = resumo(longo_sel, mes_sel, tipo)
            totais_ant, n_ant = resumo(longo_sel, mes_ant, tipo) if mes_ant else (None, 0)
            secao(titulo, f"{n} de {n_sab} sábados com lançamento em {mes_sel}")
            itens = []
            for ind, nome in list(INDICADORES.items()) + [("TOTAL", "Total")]:
                valor = int(totais.sum()) if ind == "TOTAL" else int(totais[ind])
                detalhe = ""
                if n:
                    media = valor / n
                    detalhe = f"média {num(media)} por sábado"
                    if n_ant:
                        valor_ant = totais_ant.sum() if ind == "TOTAL" else totais_ant[ind]
                        detalhe += delta_html(media, valor_ant / n_ant, mes_ant)
                itens.append(cartao(nome, valor, detalhe, destaque=(ind == "TOTAL")))
            grade(itens)

        do_mes = longo_sel[longo_sel["Mês"] == mes_sel]
        por_sab = do_mes.groupby(["Semana", "Tipo", "Indicador"], as_index=False)["Valor"].sum()
        por_sab["Sábado"] = por_sab["Semana"].map(lambda i: sabados[i - 1])
        por_sab["Indicador"] = por_sab["Indicador"].map(INDICADORES)

        if por_sab["Valor"].sum() == 0:
            st.info(f"Ainda não há lançamentos em {mes_sel}. Use a tabela abaixo para lançar.")
        else:
            secao("Público por sábado")
            fig = px.bar(por_sab, x="Sábado", y="Valor", color="Indicador", barmode="group", facet_col="Tipo",
                         text="Valor", color_discrete_map=CORES_IND,
                         category_orders={"Sábado": sabados, "Tipo": TIPOS, "Indicador": list(INDICADORES.values())})
            fig.update_xaxes(type="category")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            st.plotly_chart(estilo(fig, 400), config=SEM_BARRA, **LARGURA)

            g1, g2 = st.columns(2)
            with g1:
                secao("Média de público", "só sábados com lançamento")
                total_sab = por_sab.groupby(["Semana", "Tipo"])["Valor"].transform("sum")
                media = (por_sab[total_sab > 0].groupby(["Tipo", "Indicador"], as_index=False)["Valor"]
                         .mean().round(1))
                fig = px.bar(media, x="Indicador", y="Valor", color="Tipo", barmode="group", text="Valor",
                             color_discrete_map=CORES_TIPO,
                             category_orders={"Indicador": list(INDICADORES.values()), "Tipo": TIPOS})
                fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
                st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)
            with g2:
                janela = MESES[max(0, idx_mes - 3): idx_mes + 1]
                secao("Evolução mensal", "pessoas por sábado, últimos 4 meses")
                evo = longo_sel[longo_sel["Mês"].isin(janela)]
                evo = evo.groupby(["Mês", "Discipulador", "Tipo", "Semana"], as_index=False)["Valor"].sum()
                evo = (evo[evo["Valor"] > 0].groupby(["Mês", "Discipulador", "Tipo"], as_index=False)["Valor"]
                       .mean().round(1).rename(columns={"Valor": "Média"}))
                if evo.empty:
                    st.info("Sem dados nesse período.")
                else:
                    fig = px.line(evo, x="Mês", y="Média", color="Discipulador", facet_row="Tipo", markers=True,
                                  category_orders={"Mês": janela, "Tipo": TIPOS, "Discipulador": discs_todos},
                                  color_discrete_sequence=["#00D4FF", "#A78BFA", "#34D399", "#FBBF24", "#F472B6"])
                    fig.update_xaxes(type="category")
                    fig.update_traces(line_width=3, marker_size=8)
                    st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)

        # Lançamento
        secao("📝 Lançamento de dados", "ME = membros · FA = frequência ativa · VI = visitantes")
        modo_edicao = st.toggle("Habilitar tabela para edição", value=False)

        df_mes = df_freq[(df_freq["Mês"] == mes_sel) & (df_freq["Discipulador"].isin(disc_sel))].reset_index(drop=True)
        visiveis = [f"S{i}_{ind}" for i in range(1, n_sab + 1) for ind in INDICADORES]
        conf = {"Discipulador": st.column_config.Column(disabled=True),
                "Tipo": st.column_config.Column(disabled=True)}
        for i in range(1, n_sab + 1):
            for ind in INDICADORES:
                conf[f"S{i}_{ind}"] = st.column_config.NumberColumn(f"{sabados[i - 1]} · {ind}", min_value=0, step=1)
        ordem = ["Discipulador", "Tipo"] + visiveis

        if modo_edicao:
            with st.form("form_freq"):
                chave = f"ed_freq_{mes_sel}_{'|'.join(disc_sel)}_{st.session_state.rev}"
                editado = st.data_editor(df_mes, column_config=conf, column_order=ordem, hide_index=True,
                                         key=chave, **LARGURA)
                if st.form_submit_button("💾 Salvar frequência"):
                    try:
                        salvar_frequencia(editado)
                    except Exception as erro:
                        st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                    else:
                        concluir(f"Frequência de {mes_sel} salva.")
        else:
            st.dataframe(df_mes, column_config=conf, column_order=ordem, hide_index=True, **LARGURA)

# ───────────────────────── ABA 2: FINANÇAS ─────────────────────────
with aba_fin:
    pagos = df_diz[df_diz["Pago"] == "Sim"]
    st.markdown(f'<div class="heroi"><div class="heroi-rotulo">Total acumulado de dízimos ({ANO})</div>'
                f'<div class="heroi-valor">{formatar_brl(pagos["Valor"].sum())}</div></div>', unsafe_allow_html=True)

    mes_fin = st.selectbox("📅 Mês", MESES, index=IDX_MES_ATUAL, key="fin_mes")
    idx_fin = MESES.index(mes_fin)
    do_mes_fin = df_diz[df_diz["Mês"] == mes_fin]
    n_lideres = len(do_mes_fin)
    em_dia = int((do_mes_fin["Pago"] == "Sim").sum())
    arrecadado = pagos[pagos["Mês"] == mes_fin]["Valor"].sum()
    detalhe_arr = ""
    if idx_fin > 0:
        anterior = pagos[pagos["Mês"] == MESES[idx_fin - 1]]["Valor"].sum()
        detalhe_arr = delta_html(arrecadado, anterior, MESES[idx_fin - 1])
    grade([
        cartao(f"Arrecadado em {mes_fin}", formatar_brl(arrecadado), detalhe_arr, destaque=True),
        cartao("Líderes em dia", f"{em_dia} de {n_lideres}", f"{n_lideres - em_dia} pendente(s)"),
        cartao("Adimplência", f"{(em_dia / n_lideres * 100) if n_lideres else 0:.0f}%"),
        cartao("Média por dízimo", formatar_brl(arrecadado / em_dia) if em_dia else "—"),
    ])

    f1, f2 = st.columns([2, 1])
    with f1:
        secao("Arrecadação mensal")
        mensal = pagos.groupby("Mês")["Valor"].sum().reindex(MESES).fillna(0).reset_index()
        mensal["Rótulo"] = mensal["Valor"].map(lambda v: formatar_brl(v) if v else "")
        mensal["Mês curto"] = mensal["Mês"].str[:3]
        fig = px.bar(mensal, x="Mês curto", y="Valor", text="Rótulo")
        fig.update_traces(marker_color=["#00D4FF" if m == mes_fin else "#1E4FA8" for m in mensal["Mês"]],
                          marker_line_width=0, textposition="outside", cliponaxis=False,
                          hovertemplate="%{x}: %{text}<extra></extra>")
        fig.update_xaxes(type="category")
        st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)
    with f2:
        secao(f"Status em {mes_fin}")
        if do_mes_fin.empty:
            st.info("Sem líderes cadastrados.")
        else:
            fig = px.pie(do_mes_fin, names="Pago", color="Pago", hole=0.62,
                         color_discrete_map={"Sim": "#00D4FF", "Não": "#EF4444"},
                         category_orders={"Pago": ["Sim", "Não"]})
            fig.update_traces(textinfo="value+percent", marker_line_width=0)
            st.plotly_chart(estilo(fig, 380), config=SEM_BARRA, **LARGURA)

# ───────────────────────── ABA 3: ADMIN ─────────────────────────
if aba_admin is not None:
    with aba_admin:
        secao("⚠️ Pendências de dízimo")
        mes_pend = st.selectbox("Mês para verificar", MESES, index=max(0, IDX_MES_ATUAL - 1), key="adm_pend")
        pendentes = df_diz[(df_diz["Mês"] == mes_pend) & (df_diz["Pago"] == "Não")]
        if pendentes.empty:
            st.success(f"✅ Tudo em dia em {mes_pend}!")
        else:
            if mes_encerrado(MESES.index(mes_pend)):
                st.markdown(f'<div class="alerta"><b>Atenção:</b> {mes_pend} encerrou com '
                            f'{len(pendentes)} pendência(s).</div>', unsafe_allow_html=True)
            else:
                st.warning(f"{len(pendentes)} líder(es) ainda sem lançamento em {mes_pend}.")
            st.dataframe(pendentes[["Líder"]].reset_index(drop=True), hide_index=True, **LARGURA)

        secao("📝 Gestão de dízimos")
        mes_lanc = st.selectbox("Mês para lançamento", MESES, index=IDX_MES_ATUAL, key="adm_mes")
        base_diz = df_diz[df_diz["Mês"] == mes_lanc][["Líder", "Valor", "Pago"]].reset_index(drop=True)
        with st.form("form_diz"):
            editado_diz = st.data_editor(
                base_diz, hide_index=True, key=f"ed_diz_{mes_lanc}_{st.session_state.rev}",
                column_config={"Líder": st.column_config.Column(disabled=True),
                               "Valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.0),
                               "Pago": st.column_config.SelectboxColumn("Status", options=["Sim", "Não"], required=True)},
                **LARGURA)
            if st.form_submit_button("💾 Salvar dízimos"):
                try:
                    salvar_dizimos(mes_lanc, editado_diz)
                except Exception as erro:
                    st.error(f"Não foi possível salvar, nada foi alterado: {erro}")
                else:
                    concluir(f"Dízimos de {mes_lanc} salvos.")

        secao("💾 Backup e restauração")
        carimbo = AGORA.strftime("%Y-%m-%d")
        b1, b2 = st.columns(2)
        b1.download_button("⬇️ Baixar frequência (CSV)", df_freq.to_csv(index=False).encode("utf-8"),
                           file_name=f"{carimbo}_{ARQUIVO_FREQ}", mime="text/csv")
        b2.download_button("⬇️ Baixar dízimos (CSV)", df_diz.to_csv(index=False).encode("utf-8"),
                           file_name=f"{carimbo}_{ARQUIVO_DIZIMOS}", mime="text/csv")

        with st.expander("Restaurar a partir de um CSV de backup"):
            destino = st.radio("Este arquivo é de:", ["Frequência", "Dízimos"], horizontal=True)
            enviado = st.file_uploader("Arquivo CSV", type="csv")
            confirma = st.checkbox("Entendo que isso substitui os dados atuais desse tipo")
            if st.button("Restaurar", disabled=not (enviado and confirma)):
                nome = ARQUIVO_FREQ if destino == "Frequência" else ARQUIVO_DIZIMOS
                try:
                    novo = NORMALIZAR[nome](pd.read_csv(enviado, encoding="utf-8-sig"))
                    gravar(nome, novo)
                except Exception as erro:
                    st.error(f"Arquivo não restaurado, nada foi alterado: {erro}")
                else:
                    concluir(f"{destino} restaurada a partir do arquivo enviado.")
