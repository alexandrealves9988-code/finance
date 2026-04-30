import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Controladoria/FP&A Dashboard | Orçado vs Realizado",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    :root {
        --bg: #0a0e1a;
        --surface: #111827;
        --surface2: #1a2235;
        --accent: #00d4aa;
        --accent2: #3b82f6;
        --danger: #ef4444;
        --warning: #f59e0b;
        --success: #10b981;
        --text: #e2e8f0;
        --text-muted: #64748b;
        --border: #1e293b;
    }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        background-color: var(--bg);
        color: var(--text);
    }

    .stApp { background-color: var(--bg); }

    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }

    .metric-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: var(--accent);
    }
    .metric-card.danger::before { background: var(--danger); }
    .metric-card.warning::before { background: var(--warning); }
    .metric-card.success::before { background: var(--success); }

    .metric-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 8px;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 28px;
        font-weight: 600;
        color: var(--text);
        line-height: 1;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 500;
        margin-top: 6px;
    }
    .delta-pos { color: var(--success); }
    .delta-neg { color: var(--danger); }

    .section-title {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent);
        margin: 24px 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
    }

    .alert-box {
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .alert-danger { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); color: #fca5a5; }
    .alert-warning { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); color: #fcd34d; }
    .alert-success { background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: #6ee7b7; }

    .stDataFrame { border-radius: 10px; overflow: hidden; }

    div[data-testid="stNumberInput"] input {
        background: var(--surface2);
        border: 1px solid var(--border);
        color: var(--text);
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
    }

    .stSelectbox select, .stSlider {
        background: var(--surface2);
        color: var(--text);
    }

    h1 { font-size: 28px !important; font-weight: 700 !important; color: var(--text) !important; }
    h2 { font-size: 18px !important; font-weight: 600 !important; color: var(--text) !important; }
    h3 { font-size: 14px !important; font-weight: 600 !important; color: var(--text-muted) !important; }

    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface);
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: var(--text-muted);
        font-weight: 500;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background: var(--accent) !important;
        color: #0a0e1a !important;
    }

    .stButton > button {
        background: var(--accent);
        color: #0a0e1a;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.05em;
        padding: 10px 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #00b894;
        transform: translateY(-1px);
    }

    .highlight-row { background: rgba(0, 212, 170, 0.05) !important; }

    footer { display: none; }
    #MainMenu { display: none; }
    header { display: none; }
</style>
""", unsafe_allow_html=True)

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

CATEGORIAS = {
    "RECEITAS": {
        "Receita Bruta": {"default": 500000, "tipo": "receita"},
        "Deduções": {"default": -50000, "tipo": "deducao"},
    },
    "CUSTOS": {
        "CMV / CPV": {"default": -150000, "tipo": "custo"},
        "Pessoal": {"default": -80000, "tipo": "custo"},
        "Ocupação": {"default": -20000, "tipo": "custo"},
        "Marketing": {"default": -25000, "tipo": "custo"},
        "TI e Sistemas": {"default": -10000, "tipo": "custo"},
        "Outros Custos Op.": {"default": -15000, "tipo": "custo"},
    },
    "FINANCEIRO": {
        "Receitas Financeiras": {"default": 5000, "tipo": "receita"},
        "Despesas Financeiras": {"default": -12000, "tipo": "custo"},
    }
}

def format_brl(value):
    if abs(value) >= 1_000_000:
        return f"R$ {value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"R$ {value/1_000:.0f}K"
    return f"R$ {value:,.0f}"

def format_pct(value):
    color = "delta-pos" if value >= 0 else "delta-neg"
    sign = "+" if value >= 0 else ""
    return f'<span class="{color}">{sign}{value:.1f}%</span>'

def init_session():
    if "orcado" not in st.session_state:
        st.session_state.orcado = {}
        st.session_state.realizado = {}
        for grupo, cats in CATEGORIAS.items():
            for cat, info in cats.items():
                st.session_state.orcado[cat] = [info["default"]] * 12
                st.session_state.realizado[cat] = [0.0] * 12

def get_mes_atual():
    return datetime.now().month - 1

def calcular_dre(orcado, realizado, mes_atual):
    resultado = {}
    for grupo, cats in CATEGORIAS.items():
        for cat in cats:
            orc = st.session_state.orcado[cat]
            real = st.session_state.realizado[cat]
            proj = []
            for i in range(12):
                if i <= mes_atual:
                    proj.append(real[i])
                else:
                    proj.append(orc[i])
            resultado[cat] = {
                "orcado": orc,
                "realizado": real,
                "projetado": proj
            }
    return resultado

def calcular_fluxo_caixa(dre_data, mes_atual):
    fluxo_orc = []
    fluxo_real = []
    fluxo_proj = []
    for m in range(12):
        tot_orc = sum(dre_data[cat]["orcado"][m] for cat in dre_data)
        tot_real = sum(dre_data[cat]["realizado"][m] for cat in dre_data) if m <= mes_atual else 0
        tot_proj = sum(dre_data[cat]["projetado"][m] for cat in dre_data)
        fluxo_orc.append(tot_orc)
        fluxo_real.append(tot_real)
        fluxo_proj.append(tot_proj)
    return fluxo_orc, fluxo_real, fluxo_proj

def metric_card(label, value, delta=None, card_class=""):
    delta_html = ""
    if delta is not None:
        delta_html = f'<div class="metric-delta">{format_pct(delta)}</div>'
    return f"""
    <div class="metric-card {card_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{format_brl(value)}</div>
        {delta_html}
    </div>
    """

# ─── INIT ────────────────────────────────────────────────────────────────────
init_session()
mes_atual = get_mes_atual()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuração")
    st.markdown("---")

    ano = st.selectbox("Ano de referência", [2024, 2025, 2026], index=1)
    mes_fechamento = st.selectbox(
        "Último mês fechado",
        options=list(range(12)),
        format_func=lambda x: MESES[x],
        index=mes_atual
    )
    mes_atual = mes_fechamento

    st.markdown("---")
    st.markdown('<div class="section-title">Orçamento Mensal Base</div>', unsafe_allow_html=True)

    col_reset, col_apply = st.columns(2)
    with col_reset:
        if st.button("🔄 Reset", use_container_width=True):
            for grupo, cats in CATEGORIAS.items():
                for cat, info in cats.items():
                    st.session_state.orcado[cat] = [info["default"]] * 12
                    st.session_state.realizado[cat] = [0.0] * 12
            st.rerun()

    st.markdown("---")
    st.markdown("**Cenário de Projeção**")
    fator_proj = st.slider("Fator de crescimento (%)", -20, 30, 0, 1)
    st.caption("Aplicado ao orçamento dos meses futuros")

    st.markdown("---")
    st.caption("Projeto FP&AControladoria Dashboard")
    st.caption("Desenvolvido por Alexandre Bomfim")

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_title, col_info = st.columns([3, 1])
with col_title:
    st.markdown(f"# 📊 FP&A Dashboard — {ano}")
    st.markdown(f"<span style='color:#64748b;font-size:13px'>Período de análise: Jan a {MESES[mes_atual]} (realizado) · {MESES[mes_atual+1] if mes_atual < 11 else '—'} a Dez (projetado)</span>", unsafe_allow_html=True)

st.markdown("---")

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📥 Entrada de Dados", "📈 Orçado vs Realizado", "💰 Fluxo de Caixa", "📋 DRE Completa"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ENTRADA DE DADOS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Insira os dados orçados e realizados por categoria")
    st.caption("Valores negativos = saídas/custos · Valores positivos = receitas")

    cat_selecionada = st.selectbox(
        "Selecione a categoria para editar",
        options=[cat for grupo in CATEGORIAS.values() for cat in grupo.keys()]
    )

    st.markdown(f'<div class="section-title">✏️ Editando: {cat_selecionada}</div>', unsafe_allow_html=True)

    col_orc, col_real = st.columns(2)

    with col_orc:
        st.markdown("**Orçado (R$)**")
        orc_vals = st.session_state.orcado[cat_selecionada].copy()
        for i, mes in enumerate(MESES):
            orc_vals[i] = st.number_input(
                mes, value=float(orc_vals[i]),
                key=f"orc_{cat_selecionada}_{i}",
                step=1000.0, format="%.0f"
            )
        st.session_state.orcado[cat_selecionada] = orc_vals

    with col_real:
        st.markdown("**Realizado (R$)**")
        real_vals = st.session_state.realizado[cat_selecionada].copy()
        for i, mes in enumerate(MESES[:mes_atual + 1]):
            real_vals[i] = st.number_input(
                mes, value=float(real_vals[i]),
                key=f"real_{cat_selecionada}_{i}",
                step=1000.0, format="%.0f"
            )
        st.session_state.realizado[cat_selecionada] = real_vals

    st.markdown("---")
    st.markdown("**Resumo da categoria selecionada**")

    orc_total = sum(st.session_state.orcado[cat_selecionada])
    real_total = sum(st.session_state.realizado[cat_selecionada][:mes_atual + 1])
    var = ((real_total - orc_total) / abs(orc_total) * 100) if orc_total != 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card("Total Orçado (ano)", orc_total), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Total Realizado (até agora)", real_total), unsafe_allow_html=True)
    with c3:
        card_class = "success" if var >= 0 else "danger"
        st.markdown(metric_card("Variação", real_total - orc_total * (mes_atual + 1) / 12, var, card_class), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ORÇADO VS REALIZADO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    dre_data = calcular_dre(None, None, mes_atual)

    # KPIs principais
    receita_orc = sum(st.session_state.orcado["Receita Bruta"])
    receita_real = sum(st.session_state.realizado["Receita Bruta"][:mes_atual + 1])
    receita_orc_parcial = sum(st.session_state.orcado["Receita Bruta"][:mes_atual + 1])

    resultado_orc_total = sum(
        sum(st.session_state.orcado[cat]) for cat in dre_data
    )
    resultado_real = sum(
        sum(st.session_state.realizado[cat][:mes_atual + 1]) for cat in dre_data
    )
    resultado_orc_parcial = sum(
        sum(st.session_state.orcado[cat][:mes_atual + 1]) for cat in dre_data
    )

    var_receita = ((receita_real - receita_orc_parcial) / abs(receita_orc_parcial) * 100) if receita_orc_parcial else 0
    var_resultado = ((resultado_real - resultado_orc_parcial) / abs(resultado_orc_parcial) * 100) if resultado_orc_parcial else 0

    margem_orc = (resultado_orc_parcial / receita_orc_parcial * 100) if receita_orc_parcial else 0
    margem_real = (resultado_real / receita_real * 100) if receita_real else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cc = "success" if var_receita >= 0 else "danger"
        st.markdown(metric_card("Receita Realizada", receita_real, var_receita, cc), unsafe_allow_html=True)
    with c2:
        cc = "success" if var_resultado >= 0 else "danger"
        st.markdown(metric_card("Resultado Realizado", resultado_real, var_resultado, cc), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Receita Orçada (ano)", receita_orc), unsafe_allow_html=True)
    with c4:
        delta_mg = margem_real - margem_orc
        cc = "success" if delta_mg >= 0 else "danger"
        st.markdown(metric_card(f"Margem Líquida", resultado_real, delta_mg, cc), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico Orçado vs Realizado por mês
    fig_ovr = go.Figure()

    orc_mensal = [sum(st.session_state.orcado[cat][m] for cat in dre_data) for m in range(12)]
    real_mensal = [sum(st.session_state.realizado[cat][m] for cat in dre_data) for m in range(mes_atual + 1)]
    proj_mensal = [sum(dre_data[cat]["projetado"][m] for cat in dre_data) for m in range(12)]

    fig_ovr.add_trace(go.Bar(
        x=MESES, y=orc_mensal,
        name="Orçado", marker_color="rgba(59,130,246,0.4)",
        marker_line_color="#3b82f6", marker_line_width=1
    ))
    fig_ovr.add_trace(go.Bar(
        x=MESES[:mes_atual + 1], y=real_mensal,
        name="Realizado", marker_color="rgba(0,212,170,0.7)",
        marker_line_color="#00d4aa", marker_line_width=1
    ))
    fig_ovr.add_trace(go.Scatter(
        x=MESES[mes_atual + 1:], y=proj_mensal[mes_atual + 1:],
        name="Projetado", mode="lines+markers",
        line=dict(color="#f59e0b", width=2, dash="dot"),
        marker=dict(size=6, color="#f59e0b")
    ))
    fig_ovr.add_vline(
        x=mes_atual + 0.5, line_dash="dash",
        line_color="rgba(100,116,139,0.5)", line_width=1,
        annotation_text="Hoje", annotation_font_color="#64748b"
    )
    fig_ovr.update_layout(
        title="Resultado Mensal — Orçado vs Realizado vs Projetado",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        barmode="group", bargap=0.2,
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
        xaxis=dict(gridcolor="rgba(30,41,59,0.5)", showline=False),
        yaxis=dict(gridcolor="rgba(30,41,59,0.5)", showline=False, tickformat=",.0f", tickprefix="R$ "),
        height=400
    )
    st.plotly_chart(fig_ovr, use_container_width=True)

    # Variação por categoria
    st.markdown('<div class="section-title">Variação por Categoria (Orçado vs Realizado)</div>', unsafe_allow_html=True)

    variacoes = []
    for grupo, cats in CATEGORIAS.items():
        for cat in cats:
            orc_p = sum(st.session_state.orcado[cat][:mes_atual + 1])
            real_p = sum(st.session_state.realizado[cat][:mes_atual + 1])
            var_abs = real_p - orc_p
            var_pct = (var_abs / abs(orc_p) * 100) if orc_p != 0 else 0
            variacoes.append({
                "Categoria": cat, "Grupo": grupo,
                "Orçado": orc_p, "Realizado": real_p,
                "Variação (R$)": var_abs, "Variação (%)": var_pct
            })

    df_var = pd.DataFrame(variacoes).sort_values("Variação (%)")

    fig_var = go.Figure(go.Bar(
        x=df_var["Variação (%)"],
        y=df_var["Categoria"],
        orientation="h",
        marker_color=["#ef4444" if v < 0 else "#10b981" for v in df_var["Variação (%)"]],
        text=[f"{v:+.1f}%" for v in df_var["Variação (%)"]],
        textposition="outside"
    ))
    fig_var.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        xaxis=dict(gridcolor="rgba(30,41,59,0.3)", zeroline=True, zerolinecolor="#334155"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=350, margin=dict(l=0, r=60, t=10, b=10)
    )
    st.plotly_chart(fig_var, use_container_width=True)

    # Alertas
    st.markdown('<div class="section-title">⚠️ Alertas de Desvio</div>', unsafe_allow_html=True)
    alertas = [v for v in variacoes if abs(v["Variação (%)"]) > 10]
    if alertas:
        for a in alertas:
            tipo = "alert-danger" if a["Variação (%)"] < -10 else "alert-warning"
            icone = "🔴" if a["Variação (%)"] < -10 else "🟡"
            st.markdown(f"""
            <div class="alert-box {tipo}">
                {icone} <strong>{a['Categoria']}</strong>:
                desvio de {a['Variação (%)']:+.1f}%
                ({format_brl(a['Variação (R$)'])})
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-box alert-success">✅ Nenhuma categoria com desvio superior a 10%</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FLUXO DE CAIXA
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    dre_data = calcular_dre(None, None, mes_atual)
    fluxo_orc, fluxo_real, fluxo_proj = calcular_fluxo_caixa(dre_data, mes_atual)

    # Cumulativo
    fluxo_orc_cum = np.cumsum(fluxo_orc).tolist()
    fluxo_real_cum = np.cumsum(fluxo_real[:mes_atual + 1]).tolist()
    fluxo_proj_cum = []
    acum = fluxo_real_cum[-1] if fluxo_real_cum else 0
    for i in range(mes_atual + 1, 12):
        acum += fluxo_proj[i]
        fluxo_proj_cum.append(acum)

    # KPIs fluxo
    saldo_atual = fluxo_real_cum[-1] if fluxo_real_cum else 0
    saldo_projetado = fluxo_proj_cum[-1] if fluxo_proj_cum else saldo_atual
    saldo_orcado = fluxo_orc_cum[-1]

    meses_negativos = [MESES[i] for i in range(mes_atual + 1) if fluxo_real[i] < 0]
    meses_proj_negativos = [MESES[i] for i in range(mes_atual + 1, 12) if fluxo_proj[i] < 0]

    c1, c2, c3 = st.columns(3)
    with c1:
        cc = "success" if saldo_atual >= 0 else "danger"
        st.markdown(metric_card("Saldo Acumulado Atual", saldo_atual, card_class=cc), unsafe_allow_html=True)
    with c2:
        cc = "success" if saldo_projetado >= 0 else "danger"
        st.markdown(metric_card("Saldo Projetado (Dez)", saldo_projetado, card_class=cc), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Saldo Orçado (Dez)", saldo_orcado), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico fluxo mensal
    fig_fc = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           row_heights=[0.6, 0.4], vertical_spacing=0.08)

    # Barras mensais
    cores_real = ["#10b981" if v >= 0 else "#ef4444" for v in fluxo_real]
    fig_fc.add_trace(go.Bar(
        x=MESES[:mes_atual + 1], y=fluxo_real[:mes_atual + 1],
        name="Realizado", marker_color=cores_real, showlegend=True
    ), row=1, col=1)

    cores_proj = ["rgba(245,158,11,0.6)" if v >= 0 else "rgba(239,68,68,0.4)" for v in fluxo_proj[mes_atual + 1:]]
    fig_fc.add_trace(go.Bar(
        x=MESES[mes_atual + 1:], y=fluxo_proj[mes_atual + 1:],
        name="Projetado", marker_color=cores_proj, showlegend=True
    ), row=1, col=1)

    fig_fc.add_trace(go.Scatter(
        x=MESES, y=fluxo_orc,
        name="Orçado", mode="lines",
        line=dict(color="#3b82f6", width=2, dash="dot")
    ), row=1, col=1)

    # Linha acumulada
    x_cum = MESES[:mes_atual + 1]
    fig_fc.add_trace(go.Scatter(
        x=x_cum, y=fluxo_real_cum,
        name="Acumulado Real", mode="lines+markers",
        line=dict(color="#00d4aa", width=2),
        marker=dict(size=6), fill="tozeroy",
        fillcolor="rgba(0,212,170,0.05)"
    ), row=2, col=1)

    if fluxo_proj_cum:
        x_proj_cum = MESES[mes_atual + 1:]
        fig_fc.add_trace(go.Scatter(
            x=x_proj_cum, y=fluxo_proj_cum,
            name="Acumulado Proj.", mode="lines+markers",
            line=dict(color="#f59e0b", width=2, dash="dot"),
            marker=dict(size=6)
        ), row=2, col=1)

    fig_fc.add_hline(y=0, line_color="rgba(100,116,139,0.4)", row=1, col=1)
    fig_fc.add_hline(y=0, line_color="rgba(100,116,139,0.4)", row=2, col=1)

    fig_fc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.1),
        height=500, barmode="group"
    )
    for i in [1, 2]:
        fig_fc.update_xaxes(gridcolor="rgba(30,41,59,0.3)", row=i, col=1)
        fig_fc.update_yaxes(gridcolor="rgba(30,41,59,0.3)", tickformat=",.0f",
                            tickprefix="R$ ", row=i, col=1)

    st.plotly_chart(fig_fc, use_container_width=True)

    # Alertas de quebra de caixa
    st.markdown('<div class="section-title">🚨 Análise de Quebra de Caixa</div>', unsafe_allow_html=True)

    if meses_negativos:
        st.markdown(f"""
        <div class="alert-box alert-danger">
            🔴 <strong>Meses com resultado negativo (realizado):</strong> {', '.join(meses_negativos)}
        </div>
        """, unsafe_allow_html=True)
    if meses_proj_negativos:
        st.markdown(f"""
        <div class="alert-box alert-warning">
            🟡 <strong>Meses com risco de resultado negativo (projetado):</strong> {', '.join(meses_proj_negativos)}
        </div>
        """, unsafe_allow_html=True)
    if saldo_projetado < 0:
        st.markdown(f"""
        <div class="alert-box alert-danger">
            🔴 <strong>Atenção:</strong> Saldo acumulado projetado para dezembro é negativo ({format_brl(saldo_projetado)}).
            Revisão orçamentária recomendada.
        </div>
        """, unsafe_allow_html=True)
    if not meses_negativos and not meses_proj_negativos and saldo_projetado >= 0:
        st.markdown('<div class="alert-box alert-success">✅ Nenhuma quebra de caixa identificada no período</div>', unsafe_allow_html=True)

    # Tabela mensal
    st.markdown('<div class="section-title">Detalhamento Mensal</div>', unsafe_allow_html=True)
    rows = []
    for i, mes in enumerate(MESES):
        real_v = fluxo_real[i] if i <= mes_atual else None
        proj_v = fluxo_proj[i] if i > mes_atual else None
        orc_v = fluxo_orc[i]
        var_v = (real_v - orc_v) if real_v is not None else None
        rows.append({
            "Mês": mes,
            "Orçado": f"R$ {orc_v:,.0f}",
            "Realizado": f"R$ {real_v:,.0f}" if real_v is not None else "—",
            "Projetado": f"R$ {proj_v:,.0f}" if proj_v is not None else "—",
            "Variação": f"R$ {var_v:+,.0f}" if var_v is not None else "—",
            "Status": "✅" if real_v and real_v >= 0 else ("⚠️" if proj_v and proj_v < 0 else "🔵")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DRE COMPLETA
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    dre_data = calcular_dre(None, None, mes_atual)

    st.markdown("### DRE — Demonstrativo de Resultado do Exercício")
    st.caption(f"Realizado até {MESES[mes_atual]} · Projetado de {MESES[mes_atual+1] if mes_atual < 11 else '—'} a Dez")

    linhas_dre = []
    receita_liq_orc = 0
    receita_liq_real = 0
    receita_liq_proj = 0

    for grupo, cats in CATEGORIAS.items():
        linhas_dre.append({
            "Linha": f"▸ {grupo}", "Orçado Anual": "", "Realizado": "", "Projetado Ano": "", "Var %": ""
        })
        subtotal_orc = subtotal_real = subtotal_proj = 0
        for cat in cats:
            orc_a = sum(dre_data[cat]["orcado"])
            real_a = sum(dre_data[cat]["realizado"][:mes_atual + 1])
            proj_a = sum(dre_data[cat]["projetado"])
            var_pct = ((real_a - sum(dre_data[cat]["orcado"][:mes_atual + 1])) /
                       abs(sum(dre_data[cat]["orcado"][:mes_atual + 1])) * 100) \
                if sum(dre_data[cat]["orcado"][:mes_atual + 1]) != 0 else 0
            subtotal_orc += orc_a
            subtotal_real += real_a
            subtotal_proj += proj_a
            linhas_dre.append({
                "Linha": f"  {cat}",
                "Orçado Anual": f"R$ {orc_a:,.0f}",
                "Realizado": f"R$ {real_a:,.0f}",
                "Projetado Ano": f"R$ {proj_a:,.0f}",
                "Var %": f"{var_pct:+.1f}%"
            })

        if grupo == "RECEITAS":
            receita_liq_orc = subtotal_orc
            receita_liq_real = subtotal_real
            receita_liq_proj = subtotal_proj

    # EBITDA / Resultado
    res_orc = sum(sum(dre_data[cat]["orcado"]) for cat in dre_data)
    res_real = sum(sum(dre_data[cat]["realizado"][:mes_atual + 1]) for cat in dre_data)
    res_proj = sum(sum(dre_data[cat]["projetado"]) for cat in dre_data)
    var_res = ((res_real - sum(sum(dre_data[cat]["orcado"][:mes_atual + 1]) for cat in dre_data)) /
               abs(sum(sum(dre_data[cat]["orcado"][:mes_atual + 1]) for cat in dre_data)) * 100) \
        if sum(sum(dre_data[cat]["orcado"][:mes_atual + 1]) for cat in dre_data) != 0 else 0

    linhas_dre.append({"Linha": "─" * 40, "Orçado Anual": "", "Realizado": "", "Projetado Ano": "", "Var %": ""})
    linhas_dre.append({
        "Linha": "🏁 RESULTADO LÍQUIDO",
        "Orçado Anual": f"R$ {res_orc:,.0f}",
        "Realizado": f"R$ {res_real:,.0f}",
        "Projetado Ano": f"R$ {res_proj:,.0f}",
        "Var %": f"{var_res:+.1f}%"
    })

    mg_orc = (res_orc / receita_liq_orc * 100) if receita_liq_orc else 0
    mg_real = (res_real / receita_liq_real * 100) if receita_liq_real else 0
    mg_proj = (res_proj / receita_liq_proj * 100) if receita_liq_proj else 0
    linhas_dre.append({
        "Linha": "   Margem Líquida",
        "Orçado Anual": f"{mg_orc:.1f}%",
        "Realizado": f"{mg_real:.1f}%",
        "Projetado Ano": f"{mg_proj:.1f}%",
        "Var %": f"{mg_real - mg_orc:+.1f}pp"
    })

    df_dre = pd.DataFrame(linhas_dre)
    st.dataframe(df_dre, use_container_width=True, hide_index=True, height=600)

    # Gráfico waterfall resultado
    st.markdown('<div class="section-title">Composição do Resultado</div>', unsafe_allow_html=True)

    categorias_wf = list(dre_data.keys()) + ["Resultado"]
    valores_real_wf = [sum(dre_data[cat]["realizado"][:mes_atual + 1]) for cat in dre_data] + [res_real]
    tipos_wf = ["relative"] * len(dre_data) + ["total"]

    fig_wf = go.Figure(go.Waterfall(
        name="Realizado",
        orientation="v",
        measure=tipos_wf,
        x=categorias_wf,
        y=valores_real_wf,
        connector=dict(line=dict(color="rgba(100,116,139,0.3)")),
        increasing=dict(marker_color="#10b981"),
        decreasing=dict(marker_color="#ef4444"),
        totals=dict(marker_color="#3b82f6")
    ))
    fig_wf.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#e2e8f0"),
        height=400,
        yaxis=dict(gridcolor="rgba(30,41,59,0.3)", tickformat=",.0f", tickprefix="R$ "),
        xaxis=dict(gridcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig_wf, use_container_width=True)
