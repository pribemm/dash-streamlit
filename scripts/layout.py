from datetime import datetime, timedelta
from tracemalloc import start
from turtle import pd as pd_turtle
import pandas as pd
import streamlit as st
from dateutil.relativedelta import relativedelta
from scripts.utils import exibir_dataframe

import streamlit as st

def periodo(title):
    col_title, col_filter = st.columns([3, 1])

    with col_title:
        st.title(title)

    with col_filter:
        st.markdown("<br>", unsafe_allow_html=True)
        periodo_selecionado = st.selectbox(
            "Selecione o período:",
            ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"],
            index=5,
            key="periodo_selectbox"  # Adicionar key para evitar duplicação
        )

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = None
    end_date = None

    if periodo_selecionado == "Diário":
        start_date = today - timedelta(days=1)
        end_date = today
    elif periodo_selecionado == "Semanal":
        start_date = today - timedelta(weeks=1)
        end_date = today
    elif periodo_selecionado == "Mensal":
        start_date = today - relativedelta(months=1)
        end_date = today
    elif periodo_selecionado == "Trimestral":
        start_date = today - relativedelta(months=3)
        end_date = today
    elif periodo_selecionado == "Semestral":
        start_date = today - relativedelta(months=6)
        end_date = today
    elif periodo_selecionado == "Anual":
        start_date = today - relativedelta(years=1)
        end_date = today
    elif periodo_selecionado == "Personalizado":
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Data Inicial", 
                value=today - timedelta(days=30),
                format="DD/MM/YYYY",
                key="start_date"
            )
        with col2:
            end_date = st.date_input(
                "Data Final", 
                value=today,
                format="DD/MM/YYYY",
                key="end_date"
            )
        
        if start_date > end_date:
            st.error("A data inicial deve ser anterior à data final!")
        
        # Converter para datetime
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        
        # Exibir o período selecionado
        st.info(f"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    return start_date, end_date

def card_kpi(titulo, valor, icone, descricao=None):
    return f"""
    <div style="
        border:1px solid #e6e6e6;
        padding:16px;
        border-radius:12px;
        display:flex;
        align-items:center;
        gap:12px;
        background-color:#ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    ">
        <img src="{icone}" width="30">
        <div>
            <div style="font-size:15px; color:#6b7280;">
                {titulo}
            </div>
            <div style="font-size:22px; font-weight:600; color:#111827;">
                {valor}
            </div>
            <div style="font-size:14px; color:#6b7280;">
                {descricao if descricao else ''}
            </div>
        </div>
    </div>
    """

def card_estoque(nome, unidade, dias, estoque):
    return f"""
    <div class="card">
        <div class="card-title">{nome} ({unidade})</div>
        
        <div class="card-main">
            <span class="card-value">{dias}</span>
            <span class="card-unit">dias</span>
        </div>
        
        <div class="card-footer">
            Estoque: <b>{estoque}</b>
        </div>
    </div>
    """

def cards_grid(lista, n_colunas=4):
    for i in range(0, len(lista), n_colunas):
        cols = st.columns(n_colunas, gap="large")

        for j in range(n_colunas):
            with cols[j]:
                if i + j < len(lista):
                    st.markdown(
                        card_estoque(*lista[i + j]),
                        unsafe_allow_html=True
                    )
                else:
                    st.empty()

def rodape():
    st.markdown(f"""
    <div class="custom-footer">
        Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    </div>
    """, unsafe_allow_html=True)

def layout():
    st.markdown("""
    <style>
        /* Fundo geral */
        .stApp {
            background-color: #f5f7fb;
        }

        /* Container principal */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
            max-width: 1450px;
        }

        /* Header padrão transparente */
        header[data-testid="stHeader"] {
            background-color: transparent;
        }

        /* Remove menu e rodapé padrão */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* Cabeçalho do dashboard */
        .dashboard-header {
            background: linear-gradient(135deg, #ffffff 0%, #eef4ff 100%);
            border: 1px solid #dbe5f5;
            border-radius: 18px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.06);
        }

        .dashboard-title {
            font-size: 2rem;
            font-weight: 800;
            color: #1f2937;
            margin: 0;
            line-height: 1.2;
        }

        .dashboard-subtitle {
            font-size: 0.95rem;
            color: #6b7280;
            margin-top: 8px;
            margin-bottom: 0;
        }

        /* Subtítulos dentro dos containers */
        .section-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #1f2937;
            margin-bottom: 4px;
        }

        .section-description {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 18px;
        }

        /* KPI customizado */
        .kpi-box {
            background: #ffffff;
            border-radius: 14px;
            padding: 8px 4px 4px 4px;
        }

        .kpi-label {
            font-size: 0.85rem;
            color: #6b7280;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
        }

        .kpi-positive {
            color: #059669;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .kpi-negative {
            color: #dc2626;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .kpi-neutral {
            color: #2563eb;
            font-size: 0.9rem;
            font-weight: 700;
        }

        /* Dataframes */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        /* Espaçamento dos containers com borda */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff;
            border-radius: 16px;
            box-shadow: 0 4px 14px rgba(31, 41, 55, 0.04);
        }

        /* Linha divisória discreta */
        .soft-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #d1d5db, transparent);
            margin: 28px 0;
        }

        /* Rodapé customizado */
        .custom-footer {
            text-align: center;
            color: #6b7280;
            font-size: 0.85rem;
            margin-top: 26px;
            padding-top: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

def cabecalho(title, subtitle):
    st.markdown(f"""
    <div class="dashboard-header">
        <p class="dashboard-title">📊 {title}</p>
        <p class="dashboard-subtitle">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(
    titulo: str,
    valor,
    sufixo: str = "",
    classe_status: str = "",
    texto_status: str = "",
    formato: str = "decimal"  # "numero", "percentual", "moeda"
):
    """
    Componente de KPI reutilizável

    Parâmetros:
    - titulo: nome do KPI
    - valor: valor numérico
    - sufixo: ex "%", "R$", etc
    - classe_status: classe CSS (ex: sucesso, alerta, negativo)
    - texto_status: texto abaixo do valor
    - formato: "decimal", "percentual", "moeda", "inteiro"
    """

    if formato == "percentual":
        valor_fmt = f"{valor:.2f}%".replace(".", ",")
    elif formato == "moeda":
        valor_fmt = f"R$ {valor:,.2f}".replace(".", ",")
    elif formato == "decimal":
        valor_fmt = f"{valor:.2f}"
    elif formato == "unidade":
        valor_fmt = f"{valor} un."
    else:
        valor_fmt = f"{valor}"

    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor_fmt}{sufixo}</div>
            <div class="{classe_status}">{texto_status}</div>
        </div>
        """, unsafe_allow_html=True)

def divisor():
    st.markdown("""
    <div class="soft-divider"></div>
    """, unsafe_allow_html=True)

def secao_container(
    titulo: str,
    descricao: str = "",
    conteudo=None,
    altura_tabela: int = 250,
    mensagem_vazio: str = "Nenhum dado disponível.",
    icone: str = "📊"
):
    """
    Componente de seção padronizada

    Parâmetros:
    - titulo: título da seção
    - descricao: texto descritivo
    - conteudo: dataframe ou qualquer render
    - altura_tabela: altura da tabela
    - mensagem_vazio: fallback
    - icone: emoji opcional
    """

    with st.container(border=True):
        st.markdown(f"""
        <div class="section-title">{icone} {titulo}</div>
        <div class="section-description">{descricao}</div>
        """, unsafe_allow_html=True)

        if conteudo is None:
            st.info(mensagem_vazio)

        elif hasattr(conteudo, "empty"):
            if not conteudo.empty:
                exibir_dataframe(conteudo, altura=altura_tabela)
            else:
                st.info(mensagem_vazio)

        else:
            conteudo()

def secao_ranking_barras(
    df: pd.DataFrame,
    col_nome: str,
    col_valor: str,
    col_texto_barra: str,
    titulo: str = "Ranking",
    descricao: str = "",
    top_n: int = 5,
    prefixo_valor: str = "R$",
    mensagem_vazio: str = "Nenhum dado disponível.",
):
    """
    Componente de ranking com barras horizontais

    Parâmetros:
    - df: dataframe base
    - col_nome: coluna exibida à esquerda (label)
    - col_valor: coluna usada para tamanho da barra
    - col_texto_barra: texto dentro da barra
    - titulo: título da seção
    - descricao: descrição
    - top_n: quantidade de itens
    - prefixo_valor: prefixo monetário
    """

    with st.container(border=True):

        st.markdown(f"""
        <div class="section-title">{titulo}</div>
        <div class="section-description">{descricao}</div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <style>
        .bar-row {
            display: flex;
            align-items: center;
            margin-bottom: 14px;
        }
        .bar-label {
            width: 180px;
            font-size: 13px;
            color: #333;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .bar-container {
            flex: 1;
            background-color: #e5e7eb;
            border-radius: 20px;
            height: 22px;
            margin: 0 12px;
            overflow: hidden;
        }
        .bar-fill {
            background-color: #111;
            height: 100%;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            min-width: 30px;
        }
        .bar-value {
            width: 100px;
            text-align: right;
            font-size: 12px;
            color: #555;
            white-space: nowrap;
        }
        </style>
        """, unsafe_allow_html=True)

        if df is None or df.empty:
            st.info(mensagem_vazio)
            return

        df_plot = df.copy()

        # garantir numérico
        df_plot[col_valor] = pd.to_numeric(df_plot[col_valor], errors='coerce').fillna(0)
        df_plot[col_texto_barra] = pd.to_numeric(df_plot[col_texto_barra], errors='coerce').fillna(0)

        # ordenar + top N
        df_plot = df_plot.sort_values(by=col_valor, ascending=False).head(top_n)

        max_valor = df_plot[col_valor].max()

        for _, row in df_plot.iterrows():

            nome = row[col_nome]
            valor = row[col_valor]
            texto_barra = int(row[col_texto_barra])

            percentual = (valor / max_valor * 100) if max_valor > 0 else 0
            valor_formatado = f"{prefixo_valor}{valor:,.2f}"

            st.markdown(f"""
            <div class="bar-row">
                <div class="bar-label">{nome}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: {percentual:.1f}%;">
                        {texto_barra}
                    </div>
                </div>
                <div class="bar-value">{valor_formatado}</div>
            </div>
            """, unsafe_allow_html=True)
