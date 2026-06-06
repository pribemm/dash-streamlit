import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.get_data import get_vendas_produtos, get_margem_lucro_produtos, get_vendas_categorias, get_indice_retorno_rentabilidade, get_margem_lucro_produtos_formatado
from scripts.layout import periodo

st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* Aumentar espaçamento entre elementos */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Estilo para as colunas */
    .stColumn {
        padding: 0 15px !important;
    }
    
    /* Estilo para as tabelas */
    .stTable {
        margin-bottom: 25px !important;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Cabeçalho das tabelas */
    .stTable thead th {
        background-color: #2c3e50 !important;
        color: white !important;
        padding: 12px !important;
        font-weight: bold !important;
    }
    
    /* Células das tabelas */
    .stTable tbody td {
        padding: 10px !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }
    
    /* Hover nas linhas */
    .stTable tbody tr:hover {
        background-color: #f5f5f5 !important;
    }
    
    /* Estilo para métricas */
    [data-testid="stMetric"] {
        background-color: rgba(102, 126, 234, 0.5);
        padding: 20px;
        border-radius: 15px;
        color: black;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    [data-testid="stMetric"] label {
        color: white !important;
        font-size: 16px !important;
    }
    
    [data-testid="stMetric"] .stMetricValue {
        color: white !important;
        font-size: 32px !important;
        font-weight: bold !important;
    }
    
    /* Títulos das seções */
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 0;
        margin-bottom: 1rem;
        color: #2c3e50;
        border-left: 4px solid #3498db;
        padding-left: 15px;
    }
    
    /* Espaçamento entre seções */
    hr {
        margin: 30px 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, #e0e0e0, #3498db, #e0e0e0);
    }
    </style>
""", unsafe_allow_html=True)

start_date, end_date = periodo("Desempenho")

# Primeira linha
st.markdown('<p class="section-title"> Análise de Vendas</p>', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.markdown("#### Ranking de Vendas por Categoria")
    ranking_vendas_categorias = get_vendas_categorias(start_date, end_date)
    ranking_vendas_categorias['Valor Total'] = ranking_vendas_categorias['Valor Total'].apply(
        lambda x: f"R$ {x:.2f}".replace('.', ',')
    )
    
    if not ranking_vendas_categorias.empty:
        st.table(ranking_vendas_categorias, border='horizontal')
    else:
        st.info(" Nenhum dado disponível")

with col2:
    st.markdown("#### Índice de Retorno de Rentabilidade")
    indice_rentabilidade = get_indice_retorno_rentabilidade(start_date, end_date)
    st.metric(
        label="Retorno sobre Investimento",
        value=f"{indice_rentabilidade:.2f}%",
        delta="Rentável" if indice_rentabilidade > 0 else "Não rentável"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Segunda linha
st.markdown('<p class="section-title"> Análise de Produtos</p>', unsafe_allow_html=True)
col3, col4 = st.columns(2, gap="large")

with col3:
    st.markdown("#### Ranking de Vendas de Produtos")
    ranking_vendas = get_vendas_produtos(start_date, end_date)
    if not ranking_vendas.empty:
        st.table(ranking_vendas, border='horizontal')
    else:
        st.info(" Nenhum dado disponível")

with col4:
    st.markdown("#### Ranking Margem de Lucro de Produtos")
    ranking_margem_lucro = get_margem_lucro_produtos_formatado(start_date, end_date)
    if not ranking_margem_lucro.empty:
        st.table(ranking_margem_lucro[['Produto', 'Margem de Lucro']], border='horizontal')
    else:
        st.info(" Nenhum dado disponível")

st.markdown("---")
st.caption(f" Última atualização: {datetime.now().strftime('%d/%m/%Y às %H:%M')}")