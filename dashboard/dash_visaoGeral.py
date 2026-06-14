# report_visaoGeral.py
from datetime import datetime, timedelta
import streamlit as st
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.get_data import (
    get_faturamento_total,
    get_total_vendas,
    get_ticket_medio,
    get_lucro_total,
    get_margem_lucro_geral,
    get_faturamento_por_produto,
    get_dados_vendas_filtrados,
    get_lucro_por_periodo,
    get_vendas_produtos,
    get_insumos_estoque_baixo,
)

from scripts.layout import (
    layout,
    kpi_card,
    divisor,
    periodo,
    secao_ranking_barras,
    cards_grid,
)

from scripts.utils import (calcular_grandezas_periodo, gerar_grafico_temporal,
                           gerar_grafico)

# layout
layout()

st.title("Visão Geral")

c11, c12 = st.columns(2)

with c11:
    st.subheader("Dados de Vendas e Faturamento no Período")

with c12:
    col_periodo, col_personalizado, col_granularidade = st.columns(3)
    with col_periodo:
        periodo_selecionado = st.selectbox(
            "Selecione o período:",
            ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"],
            index=5,
            key="periodo_selectbox"
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
            with col_personalizado:
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

            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.max.time())


    with col_granularidade:
        opcao_granularidade = st.selectbox(
            "Agrupamento dos Gráficos:",
            options=["diaria", "semanal", "mensal"],
            index=0
        )
    
st.divider()

# Exibir o período selecionado
st.info(f"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

dias=calcular_grandezas_periodo(start_date, end_date)['dias_totais']
semanas=calcular_grandezas_periodo(start_date, end_date)['semanas_totais']
meses=calcular_grandezas_periodo(start_date, end_date)['meses_totais']

# @st.cache_data(ttl=300)
faturamento_total = get_faturamento_total(start_date, end_date)
vendas_periodo = get_total_vendas(start_date, end_date)
ticket_medio = get_ticket_medio(start_date, end_date)
lucro_bruto = get_lucro_total(start_date, end_date)
margem_lucro = get_margem_lucro_geral(start_date, end_date)
vendas_medias_diarias = vendas_periodo/dias
tabela_produtos = get_faturamento_por_produto(start_date, end_date)
df_lucro_periodo = get_lucro_por_periodo(start_date, end_date)
df_vendas_bruto=get_dados_vendas_filtrados(start_date, end_date)

# Carregar métricas e dados agregados

# Primeira linha de cards
col_11, col_12, col_13, col_14 = st.columns(4, gap="small")

with col_11:
    kpi_card(
    titulo="Faturamento Total",
    valor=faturamento_total,
    texto_status=f"{vendas_periodo} vendas no período",
    formato="moeda",
    ajuda="Faturamento gerado pelas vendas realizadas no período selecionado."
    )
    
with col_12:
    valor_ticket = (
        faturamento_total / vendas_periodo
        if vendas_periodo > 0
        else None
    )

    kpi_card(
        titulo="Ticket Médio",
        valor=valor_ticket,
        texto_status="Sem vendas no período" if valor_ticket is None else "Valor Médio por Venda",
        formato="moeda",
        ajuda="Faturamento total dividido pelo número total de vendas no período selecionado."
    )

with col_13:
    kpi_card(
    titulo="Lucro Bruto",
    valor=lucro_bruto,
    texto_status=f"{margem_lucro:.2f}% da Margem.",
    formato="moeda",
    ajuda="Lucro bruto gerado pelas vendas no período selecionado."
    )

with col_14:
    kpi_card(
    titulo="Vendas Médias Diárias",
    valor=f"{vendas_medias_diarias:.4f}",
    texto_status=f"{vendas_periodo} vendas no período",
    formato="unidade",
    ajuda="Total de vendas dividido pelo número de dias do período."
    )

low_stock_insumos = get_insumos_estoque_baixo(start_date, end_date)
if not low_stock_insumos.empty:
    st.subheader("Insumos com Estoque Baixo")
    produtos_baixo = []
    for _, row in low_stock_insumos.iterrows():
        produtos_baixo.append(
            (
                row["Insumo"],
                row["Unidade"],
                f"{row['Dias']} d",
                f"{row['Estoque Atual']:.2f}"
            )
        )
    cards_grid(produtos_baixo, n_colunas=4)
else:
    st.info("Nenhum insumo com estoque abaixo do mínimo no período selecionado.")

divisor()

# Segunda linha - Gráficos de evolução temporal
st.subheader("Evolução Temporal")

gerar_grafico(
    titulo="Evolução de Vendas no Período",
    descricao="Gráfico de evolução do volume de vendas ao longo do tempo.",
    granularidade=opcao_granularidade,
    dataframe=df_vendas_bruto,
    start_date=start_date,
    end_date=end_date,
    colunas=['quantity'],
    tipo_grafico='barras'
)

# Obter dados de lucro por período

# Mapear nomes para colunas

mapa_colunas = {
    "Receita": "total_price",
    "Lucro Bruto": "lucro_bruto_total"
}

gerar_grafico(
    titulo="Evolução de Receita e Lucro no Período",
    descricao="Gráfico comparativo entre receita total e lucro bruto ao longo do tempo.",
    granularidade=opcao_granularidade,
    dataframe=df_lucro_periodo,
    start_date=start_date,
    end_date=end_date,
    colunas=['total_price', 'lucro_bruto_total'],
    tipo_grafico='linhas',
)


divisor()

# Terceira linha - Top Produtos
ranking_vendas = get_vendas_produtos(start_date, end_date)
ranking_vendas_exibicao = ranking_vendas.copy()

secao_ranking_barras(
    df=ranking_vendas_exibicao,
    col_nome="Produto",
    col_valor="Valor Total das Vendas",
    col_texto_barra="Quantidade Vendida",
    titulo="Ranking de Vendas de Produtos",
    descricao="Top 5 produtos com maior volume de vendas no período selecionado.",
    )
        
 
# Rodapé
st.markdown("---")
st.caption(f"Ranking baseado na quantidade de unidades vendidas")