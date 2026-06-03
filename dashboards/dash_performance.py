import pandas as pd
import streamlit as st

st.title("Desempenho")

p1, p2, p3 = st.columns(3)

with p1:
    periodo = st.selectbox("Período", ["Diário", "Semanal", "Mensal", "Trimestral", "Semestral", "Anual", "Personalizado"], index=5)

if periodo == "Personalizado":
    with p2:
        periodo_inicio, periodo_fim = st.columns(2)

        with periodo_inicio:
            inicio = st.date_input("Data inicial", format="DD-MM-YYYY")

        with periodo_fim:
            fim = st.date_input("Data final", format="DD-MM-YYYY")

            # if inicio and fim:
            #     df_filtrado = df[
            #         (df["data"] >= pd.to_datetime(inicio)) &
            #         (df["data"] <= pd.to_datetime(fim))
            #     ]
with p3:
    granularidade = st.selectbox("Granularidade", ["Diária", "Semanal", "Mensal"], index=1)

st.subheader("Ranking de Vendas de Produtos")

st.subheader("Ranking Margem de Lucro de Produtos")

st.subheader("Ranking de Vendas por Categoria")

st.subheader("Índice de Retorno de Rentabilidade")
