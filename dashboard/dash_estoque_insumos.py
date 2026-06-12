# import pandas as pd
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

import streamlit as st
from scripts.get_data import get_consumo_insumos_por_periodo, get_giro_estoque_insumos
from scripts.layout import (layout, periodo, secao_ranking_barras)

layout()

st.title("Estoque e Insumos")

c11, c12 = st.columns([2,1])

with c11:
    st.subheader("Consumo de Insumos no Período")

with c12:
    start_date, end_date = periodo()

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


# cards_grid(produtos, card_estoque, n_colunas=4)