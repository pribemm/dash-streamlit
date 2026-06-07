import streamlit as st
import pandas as pd
from datetime import datetime
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
    get_vendas_medias_diarias,
    get_faturamento_por_produto
)

from scripts.layout import (periodo, 
                            cabecalho, 
                            layout,
                            kpi_card,
                            divisor,
                            secao_container
                            )

from scripts.utils import calcular_grandezas_periodo

st.set_page_config(
    page_title="Dashboard de Desempenho",
    page_icon="📊",
    layout="wide"
)

# layout
layout()

# Filtro de período
start_date, end_date = periodo("Desempenho")

faturamento_total = get_faturamento_total(start_date, end_date)
vendas_periodo = get_total_vendas(start_date, end_date)
ticket_medio = get_ticket_medio(start_date, end_date)
lucro_bruto = get_lucro_total(start_date, end_date)
margem_lucro = get_margem_lucro_geral(start_date, end_date)
vendas_medias_diarias = get_vendas_medias_diarias(start_date, end_date)
tabela_produtos = get_faturamento_por_produto(start_date, end_date)


dias=calcular_grandezas_periodo(start_date, end_date)['dias_totais']
semanas=calcular_grandezas_periodo(start_date, end_date)['semanas_totais']
meses=calcular_grandezas_periodo(start_date, end_date)['meses_totais']

# Cabeçalho
cabecalho("Gestão de Performance Comercial", "Acompanhamento do faturamento, ticket médio e saúde financeira")


card_11, card_12, card_13 = st.columns(3, gap="small")

with card_11:
    kpi_card(
    titulo="Ticket Médio",
    valor=ticket_medio,
    texto_status="Receita ÷ Total de Vendas",
    formato="moeda"
    )

with card_12:
    kpi_card(
    titulo="Vendas",
    valor=vendas_periodo,
    texto_status="Total de Vendas",
    formato="unidade"
    )

with card_13:
    kpi_card(
    titulo="Faturamento",
    valor=faturamento_total,
    texto_status="Total de Receita",
    formato="moeda"
    )

divisor()

# Segunda linha de cards
# Primeira linha de card
card_21, card_22, card_23 = st.columns(3, gap="small")

with card_21:
    kpi_card(
    titulo="Receita Mensal média",
    valor=faturamento_total/meses,
    texto_status= f'Total de meses ={meses}',
    formato="moeda"
    )
  
with card_22:
    kpi_card(
    titulo="Receita Semanal Média no Período",
    valor=faturamento_total/semanas,
    texto_status= f'Total de Semanas = {semanas}',
    formato="moeda"
    )
   
with card_23:
    kpi_card(
    titulo="Receita Diária Média no Período",
    valor=faturamento_total/dias,
    texto_status= f'Número de dias = {dias}',
    formato="moeda"
    )
    
divisor()

secao_container(
    titulo= "Faturamento por Produto",
    conteudo=tabela_produtos,
    altura_tabela = 250,
    mensagem_vazio = "Nenhum dado disponível.",
    icone = " "
)

divisor()


