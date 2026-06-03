# import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from utils.layout import cards_grid, card_estoque

st.title("Estoque e Insumos")

st.subheader("Consumo de Insumos por Período")

st.subheader("Giro de estoque por Insumo")

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

cards_grid(produtos, card_estoque, n_cols=4)
