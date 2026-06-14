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
                            kpi_card, 
                            divisor, 
                            secao_container,
                            secao_ranking_barras)

from scripts.utils import (formatar_moeda)

# layout
layout()

st.title("Desempenho Comercial")

c11, c12 = st.columns([2,1])

with c11:
    st.subheader("Dados de Desempenho no Período")

with c12:
    start_date, end_date = periodo()

# Exibir o período selecionado
st.info(f"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

# Carregamento de Dados
ranking_vendas_categorias = get_vendas_categorias(start_date, end_date)
ranking_vendas = get_vendas_produtos(start_date, end_date)
ranking_margem_lucro = get_margem_lucro_produtos(start_date, end_date)
indice_rentabilidade = get_indice_retorno_rentabilidade(start_date, end_date)

# Tratamento de Dados
ranking_vendas_categorias_exibicao = ranking_vendas_categorias.copy()
if not ranking_vendas_categorias_exibicao.empty and 'Valor Total' in ranking_vendas_categorias_exibicao.columns:
    ranking_vendas_categorias_exibicao['Valor Total'] = ranking_vendas_categorias_exibicao['Valor Total'].apply(formatar_moeda)

ranking_margem_lucro_exibicao = ranking_margem_lucro.copy()

if not ranking_margem_lucro_exibicao.empty:
    colunas_margem = [
        col for col in ['Produto', 'Margem de Lucro']
        if col in ranking_margem_lucro_exibicao.columns
    ]
    ranking_margem_lucro_exibicao = ranking_margem_lucro_exibicao[colunas_margem]


# Indicadores
status_rentabilidade = "Rentável" if indice_rentabilidade > 0 else "Não rentável"
classe_rentabilidade = "kpi-positive" if indice_rentabilidade > 0 else "kpi-negative"
total_produtos = ranking_vendas['Quantidade Vendida'].sum() if not ranking_vendas.empty else 0
receita = ranking_vendas['Valor Total das Vendas'].sum() if not ranking_vendas.empty else 0

col_kpi1, col_kpi2, col_kpi3 = st.columns(3, gap="large")

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
    titulo="Produtos vendidos",
    valor=total_produtos,
    formato="unidade"
    )


with col_kpi3:
    kpi_card(
    titulo="Produtos com margem",
    valor=receita,
    formato="moeda"
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
    df=ranking_vendas,
    col_nome="Produto",
    col_valor="Valor Total das Vendas",
    tipo_valor="moeda",
    titulo="Ranking de Receita por Produto",
    descricao="Produtos com maior volume financeiro no período selecionado.",
    )

    secao_ranking_barras(
    df=ranking_margem_lucro,
    col_nome="name_product",
    col_valor="total_lucro",
    tipo_valor="moeda",
    titulo="Ranking de Lucro por Produto",
    descricao="Produtos com maior margem de lucro.",
    )    

with col_margem:
    
    secao_ranking_barras(
    df=ranking_vendas,
    col_nome="Produto",
    col_valor="Quantidade Vendida",
    tipo_valor="unidade",
    titulo="Ranking de Vendas por Produto",
    descricao="Produtos com maior volume de vendas no período selecionado.",
    )

    secao_ranking_barras(
    df=ranking_margem_lucro,
    col_nome="name_product",
    col_valor="margem_percentual",
    tipo_valor="percentual",
    titulo="Ranking de Margem de Lucro por Produto",
    descricao="Produtos com maior margem de lucro.",
    )

    

# Rodapé
rodape()    
