import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.get_data import (
    get_vendas_produtos,
    get_margem_lucro_produtos,
    get_vendas_categorias,
    get_indice_retorno_rentabilidade,
    get_margem_lucro_produtos_formatado,
    grafico_barras_horizontais
)
from scripts.layout import periodo


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Dashboard de Desempenho",
    page_icon="📊",
    layout="wide"
)


# layout
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

# funcoes auciliare
def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return valor


def formatar_percentual(valor):
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return valor


def exibir_dataframe(df, altura=None):
    """
    Exibe dataframe com configuração padrão para o dashboard.
    """
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        height=altura
    )

# Filtro de período
start_date, end_date = periodo("Desempenho")

# Carregamento de Dados
ranking_vendas_categorias = get_vendas_categorias(start_date, end_date)
ranking_vendas = get_vendas_produtos(start_date, end_date)
ranking_margem_lucro = get_margem_lucro_produtos(start_date, end_date)
indice_rentabilidade = get_indice_retorno_rentabilidade(start_date, end_date)

# Tratamento de Dados
ranking_vendas_categorias_exibicao = ranking_vendas_categorias.copy()
if not ranking_vendas_categorias_exibicao.empty and 'Valor Total' in ranking_vendas_categorias_exibicao.columns:
    ranking_vendas_categorias_exibicao['Valor Total'] = ranking_vendas_categorias_exibicao['Valor Total'].apply(formatar_moeda)

ranking_vendas_exibicao = ranking_vendas.copy()

ranking_margem_lucro_exibicao = ranking_margem_lucro.copy()
if not ranking_margem_lucro_exibicao.empty:
    colunas_margem = [
        col for col in ['Produto', 'Margem de Lucro']
        if col in ranking_margem_lucro_exibicao.columns
    ]
    ranking_margem_lucro_exibicao = ranking_margem_lucro_exibicao[colunas_margem]

# Cabeçalho
st.markdown(f"""
<div class="dashboard-header">
    <p class="dashboard-title">📊 Dashboard de Desempenho Comercial</p>
    <p class="dashboard-subtitle">
        Visão geral de vendas, categorias, produtos e rentabilidade no período selecionado.
    </p>
</div>
""", unsafe_allow_html=True)

# Indicadores
status_rentabilidade = "Rentável" if indice_rentabilidade > 0 else "Não rentável"
classe_rentabilidade = "kpi-positive" if indice_rentabilidade > 0 else "kpi-negative"

total_categorias = len(ranking_vendas_categorias) if ranking_vendas_categorias is not None else 0
total_produtos = len(ranking_vendas) if ranking_vendas is not None else 0
total_produtos_margem = len(ranking_margem_lucro) if ranking_margem_lucro is not None else 0

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4, gap="large")

with col_kpi1:
    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Retorno sobre Investimento</div>
            <div class="kpi-value">{indice_rentabilidade:.2f}%</div>
            <div class="{classe_rentabilidade}">{status_rentabilidade}</div>
        </div>
        """, unsafe_allow_html=True)

with col_kpi2:
    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Categorias analisadas</div>
            <div class="kpi-value">{total_categorias}</div>
        </div>
        """, unsafe_allow_html=True)

with col_kpi3:
    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Produtos vendidos</div>
            <div class="kpi-value">{total_produtos}</div>
        </div>
        """, unsafe_allow_html=True)

with col_kpi4:
    with st.container(border=True):
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Produtos com margem</div>
            <div class="kpi-value">{total_produtos_margem}</div>
        </div>
        """, unsafe_allow_html=True)


st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)

# Vendas por categoria
with st.container(border=True):
    st.markdown("""
    <div class="section-title">🏷️   Análise de Vendas por Categoria</div>
    <div class="section-description">
        Ranking das categorias com maior volume financeiro no período selecionado.
    </div>
    """, unsafe_allow_html=True)

    if not ranking_vendas_categorias_exibicao.empty:
        exibir_dataframe(ranking_vendas_categorias_exibicao, altura=230)
    else:
        st.info("Nenhum dado disponível para vendas por categoria.")


st.markdown("<br>", unsafe_allow_html=True)

# Anáise de produtos
col_produtos, col_margem = st.columns(2, gap="large")

with col_produtos:
    with st.container(border=True):

        st.markdown("""
        <div class="section-title"> Ranking de Vendas de Produtos</div>
        <div class="section-description">
            Top 5 produtos com maior volume financeiro no período selecionado.
        </div>
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
            color: #333333;
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
            position: relative;
            overflow: hidden;
        }
        .bar-fill {
            background-color: #111111;
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
            color: #555555;
            white-space: nowrap;
        }
        </style>
        """, unsafe_allow_html=True)

        if not ranking_vendas_exibicao.empty:

            # Nomes das colunas (já renomeadas na função)
            col_nome  = 'Produto'
            col_valor = 'Valor Total das Vendas'
            col_qtd   = 'Quantidade Vendida'

            df = ranking_vendas_exibicao.copy()
         
            df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
            df[col_qtd]   = pd.to_numeric(df[col_qtd],   errors='coerce').fillna(0)

            # ordenar e pegar top 5
            df = df.sort_values(by=col_valor, ascending=False)
            df = df.head(5).reset_index(drop=True)

            max_valor = df[col_valor].max()

            # Renderizar cada barra
            for _, row in df.iterrows():
                nome      = row[col_nome]
                valor     = row[col_valor]
                quantidade = int(row[col_qtd])
                percentual = (valor / max_valor * 100) if max_valor > 0 else 0
                valor=f'R${valor:.2f}'

                st.markdown(f"""
                <div class="bar-row">
                    <div class="bar-label">{nome}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentual:.1f}%;">
                            {quantidade}
                        </div>
                    </div>
                    <div class="bar-value">{valor}</div>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.info("Nenhum dado disponível para vendas de produtos.")


with col_margem:
    with st.container(border=True):

        st.markdown("""
        <div class="section-title"> Ranking de Margem de Lucro</div>
        <div class="section-description">
            Top 5 produtos com maior margem de lucro no período selecionado.
        </div>
        """, unsafe_allow_html=True)

        
        grafico_barras_horizontais(df=ranking_margem_lucro,
            col_nome='name_product',
            col_valor='margem_percentual',
            col_texto='total_lucro',
            top_n = 5,
            formato_valor = "percentual",  # "moeda", "percentual" ou "numero"
            formato_texto = "moeda"  # "moeda", "percentual" ou "numero"
        )

# Rodapé
st.markdown(f"""
<div class="custom-footer">
    Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
</div>
""", unsafe_allow_html=True)
