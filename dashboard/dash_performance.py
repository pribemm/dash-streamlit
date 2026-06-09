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
    get_indice_retorno_rentabilidade
)
from scripts.layout import (periodo, 
                            rodape, 
                            layout, 
                            cabecalho, 
                            kpi_card, 
                            divisor, 
                            secao_container,
                            secao_ranking_barras)

from scripts.utils import (formatar_moeda)


st.set_page_config(
    page_title="Dashboard de Desempenho",
    page_icon="📊",
    layout="wide"
)

# layout
layout()

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
cabecalho("Desempenho", "Visão geral de vendas, categorias, produtos e rentabilidade no período selecionado.")

# Indicadores
status_rentabilidade = "Rentável" if indice_rentabilidade > 0 else "Não rentável"
classe_rentabilidade = "kpi-positive" if indice_rentabilidade > 0 else "kpi-negative"
total_categorias = len(ranking_vendas_categorias) if ranking_vendas_categorias is not None else 0
total_produtos = len(ranking_vendas) if ranking_vendas is not None else 0
total_produtos_margem = len(ranking_margem_lucro) if ranking_margem_lucro is not None else 0

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4, gap="large")

with col_kpi1:
    kpi_card(
    titulo="Retorno sobre Investimento",
    valor=indice_rentabilidade,
    formato="percentual",
    classe_status=classe_rentabilidade,
    texto_status=status_rentabilidade
    )

with col_kpi2:
    kpi_card(
    titulo="Categorias Analisadas",
    valor=total_categorias,
    formato="unidade"
    )


with col_kpi3:
    kpi_card(
    titulo="Produtos vendidos",
    valor=total_produtos,
    formato="unidade"
    )


with col_kpi4:
    kpi_card(
    titulo="Produtos com margem",
    valor=total_produtos_margem,
    formato="unidade"
    )
    
divisor()

# Vendas por categoria
secao_container(
    titulo="Análise de Vendas por Categoria",
    descricao="Ranking das categorias com maior volume financeiro no período selecionado.",
    conteudo=ranking_vendas_categorias_exibicao,
    altura_tabela=230,
    icone="🏷️"
)

# Anáise de produtos
col_produtos, col_margem = st.columns(2, gap="large")

with col_produtos:
    secao_ranking_barras(
    df=ranking_vendas_exibicao,
    col_nome="Produto",
    col_valor="Valor Total das Vendas",
    col_texto_barra="Quantidade Vendida",
    titulo="Ranking de Vendas de Produtos",
    descricao="Top 5 produtos com maior volume financeiro no período selecionado.",
    )

with col_margem:
    secao_ranking_barras(
    df=ranking_margem_lucro,
    col_nome="name_product",
    col_valor="margem_percentual",
    col_texto_barra="total_lucro",
    titulo="Ranking de Margem de Lucro",
    descricao="Top 5 produtos com maior margem de lucro no período selecionado.",
    )

# Rodapé
rodape()
