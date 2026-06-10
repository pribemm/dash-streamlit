# import pandas as pd
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

import streamlit as st
from scripts.get_data import get_consumo_insumos_por_periodo, get_giro_estoque_insumos
from scripts.layout import (periodo, secao_ranking_barras)

st.title("Estoque e Insumos")

start_date, end_date = periodo()

st.subheader("Consumo de Insumos no Período")

consumo=get_consumo_insumos_por_periodo(start_date, end_date)
secao_ranking_barras(
    df=consumo,
    col_nome= "Insumo",
    col_valor= "Valor Gasto",
    col_texto_barra= "Quantidade Utilizada",
    titulo = "Consumo de Insumos no Período",
    descricao = "Ranking dos insumos mais consumidos e o valor gasto em cada um durante o período selecionado.",
    top_n = 10,
    tipo_valor = "moeda",
    tipo_texto_barra = "peso",
    prefixo_valor = "R$",
    mensagem_vazio = "Nenhum dado disponível.",
)

st.subheader("Giro de Estoque por Insumo")
tabela_giro_estoque = get_giro_estoque_insumos(start_date, end_date)[['Insumo', 'Consumo Mensal', 'Estoque Atual', 'Giro', 'Status']]

st.table(tabela_giro_estoque)

st.markdown("""
<style>
.grid-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}
.card-wrapper {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

html = '<div class="grid-container">'

produtos = [
    ("Arroz", "Kg", 13, 49),
    ("Feijão", "Kg", 1, 4),
    ("Filé de frango", "Kg", 10, 20),
    ("Refrigerante", "Uni.", 11, 490),
    ("Macarrão", "Kg", 5, 30),
    ("Carne", "Kg", 8, 120),
    ("Leite", "Uni.", 20, 100),
    ("Suco", "Uni.", 15, 75),
]

# cards_grid(produtos, card_estoque, n_colunas=4)