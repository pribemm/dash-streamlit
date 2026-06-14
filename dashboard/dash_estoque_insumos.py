# import pandas as pd
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

import streamlit as st
from scripts.get_data import get_consumo_insumos_por_periodo, get_giro_estoque_insumos
from scripts.layout import (layout, 
                            periodo, 
                            secao_ranking_barras,
                            render_cards_cobertura,
                            get_alertas_estoque)



layout()

st.title("Estoque e Insumos")

c11, c12 = st.columns([2,1])

with c11:
    st.subheader("Consumo de Insumos no Período")

with c12:
    start_date, end_date = periodo()

# Dados
consumo=get_consumo_insumos_por_periodo(start_date, end_date)
tabela_giro_estoque = get_giro_estoque_insumos(start_date, end_date)

alertas = get_alertas_estoque()

render_cards_cobertura(alertas, n=8)

secao_ranking_barras(
    df=consumo,
    col_nome= "Insumo",
    col_valor= "Valor Gasto",
    titulo = "Ranking de Valor Gasto com Insumos",
    descricao = "Ranking dos 10 insumos com maior gasto durante o período selecionado.",
    top_n = 10,
    tipo_valor = "moeda",
    mensagem_vazio = "Nenhum dado disponível.",
)

secao_ranking_barras(
    df=consumo,
    col_nome= "Insumo",
    col_valor= "Quantidade Utilizada",
    titulo = "Ranking de Quantidade Insumos Usados no Período",
    descricao = "Ranking dos 10 insumos mais consumidos durante o período selecionado.",
    top_n = 10,
    tipo_valor = "decimal",
    mensagem_vazio = "Nenhum dado disponível.",
)


st.subheader("Giro de Estoque por Insumo")

st.dataframe(tabela_giro_estoque[['Insumo', 'Consumo Mensal', 'Estoque Atual', 'Giro', 'Status']],
             column_config={
            "Insumo": st.column_config.TextColumn(
                "Insumo",
                help="Nome do insumo cadastrado no sistema",
            ),
            "Consumo Mensal": st.column_config.TextColumn(
                "Consumo Mensal",
                help="Quantidade média consumida por mês no período selecionado",
            ),
            "Estoque Atual": st.column_config.TextColumn(
                "Estoque Atual",
                help="Estoque Final = Estoque Inicial + Entradas - Saídas - Consumo",
            ),
            "Giro": st.column_config.TextColumn(
                "Giro",
                help="Consumo Mensal ÷ Estoque Médio. Quanto maior, mais rápido o insumo é consumido",
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                help="Alto = giro > 2x/mês. Normal = entre 0.5x e 2x. Baixo = menos de 0.5x/mês",
            ),
        },
        width='stretch',
        hide_index=True,
    )


