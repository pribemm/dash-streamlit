import pandas as pd
import streamlit as st
from utils.layout import card_kpi

receita_mensal = float(10000.41)
receita_semanal_media = float(2500.10)
receita_diaria_media = float(357.15)
ticket_medio = float(50.25)
total_vendas = int(200)
tabela_qtd_vendas = pd.DataFrame({
    'Produto': ['Marmita Fit', 'Marmita Tradicional', 'Marmita Vegana'],
    'Quantidade Vendida': [80, 100, 20],
    'Receita Gerada': [4000.00, 5000.00, 1000.00],
    'Ticket Médio': [50.00, 50.00, 50.00]
})

st.title("Estatísticas de Vendas")

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

st.subheader("Visão Geral das Vendas")
c11, c12, c13 = st.columns(3)

with c11:
    st.markdown(
        card_kpi(
            "Receita Mensal",
            f"R$ {receita_mensal:,.2f}",
            "https://cdn-icons-png.flaticon.com/512/3135/3135706.png",
            "Últimos 30 dias"
        ),
        unsafe_allow_html=True
    )

with c12:
    st.markdown(
        card_kpi(
            "Receita Semanal Média",
            f"R$ {receita_semanal_media:,.2f}",
            "https://cdn-icons-png.flaticon.com/512/2920/2920244.png",
            "~ 4,3 semanas "
        ),
        unsafe_allow_html=True
    )

with c13:
    st.markdown(
        card_kpi(
            "Receita Diária Média",
            f"R$ {receita_diaria_media:,.2f}",
            "https://cdn-icons-png.flaticon.com/512/1828/1828919.png",
            "124 vendas em média"
        ),
        unsafe_allow_html=True
    )
# c11.metric("Receita Mensal", f"R$ {receita_mensal:,.2f}", border=True)
# c12.metric("Receita Semanal Média", f"R$ {receita_semanal_media:,.2f}", border=True)
# c13.metric("Receita Diária Média", f"R$ {receita_diaria_media:,.2f}", border=True)

st.subheader("Métricas de Vendas")
c21, c22 = st.columns(2)

with c21:
    st.markdown(
        card_kpi(
            "Ticket Médio",
            f"R$ {ticket_medio:,.2f}",
            "https://cdn-icons-png.flaticon.com/512/2920/2920244.png",
            "Média do valor de cada venda"
        ),
        unsafe_allow_html=True
    )

with c22:
    st.markdown(
        card_kpi(
            "Total de Vendas",
            total_vendas,
            "https://cdn-icons-png.flaticon.com/512/3135/3135706.png",
            "Número total de vendas realizadas"
        ),
        unsafe_allow_html=True
    )

st.subheader("Quantidade de Vendas por Produto")
st.table(tabela_qtd_vendas, border='horizontal', height='stretch')
