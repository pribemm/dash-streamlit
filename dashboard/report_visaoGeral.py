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
)

from scripts.layout import (periodo, 
                            cabecalho, 
                            layout,
                            kpi_card,
                            divisor,
                            secao_ranking_barras
                            )

from scripts.utils import (calcular_grandezas_periodo, gerar_grafico_temporal,
                           gerar_grafico)

st.set_page_config(
    page_title="Visão Geral",
    page_icon="📊",
    layout="wide"
)

# layout
layout()


# Cabeçalho
cabecalho("Visão Geral", "Dados de vendas e faturamento")

# Filtros
col_opt_granularidade, col_opt_periodo, col_opt_grafico = st.columns(3)

with col_opt_periodo:
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
        with col_opt_grafico:
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

with col_opt_granularidade:
    opcao_granularidade = st.selectbox(
        "Agrupamento do Gráfico:",
        options=["Diaria", "Semanal", "Mensal"],
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

divisor()

# Segunda linha - Gráficos de evolução temporal
st.subheader("Evolução Temporal")

df_vendas_bruto=get_dados_vendas_filtrados(start_date, end_date)


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

# gerar_grafico_temporal(
#     titulo="Evolução de Vendas no Período",
#     descricao="Gráfico de evolução do volume de vendas ao longo do tempo.", 
#     granularidade=opcao_granularidade,
#     dataframe=df_vendas_bruto,
#     coluna='quantity',
#     start_date=start_date,
#     end_date=end_date
# )

# Obter dados de lucro por período
df_lucro_periodo = get_lucro_por_periodo(start_date, end_date)

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