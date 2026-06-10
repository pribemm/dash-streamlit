import streamlit as st
import sys
import os

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.get_data import (get_faturamento_total,
                             get_custos_totais,
                             get_lucro_total,
                             get_vendas_por_pagamento)

from scripts.layout import (divisor, kpi_card, layout, periodo, secao_ranking_barras)

# layout
layout()

st.title("Financeiros")

c11, c12 = st.columns([2,1])

with c11:
    st.subheader("Dados Financeiros no Período")

with c12:
    start_date, end_date = periodo()

# Dados
faturamento_total = get_faturamento_total(start_date, end_date)
custos_totais = get_custos_totais(start_date, end_date)
lucro_bruto = get_lucro_total(start_date, end_date)
margem_lucro = (lucro_bruto / faturamento_total * 100) if faturamento_total > 0 else 0
formas_pagamento = get_vendas_por_pagamento(start_date, end_date)

c21, c22, c23 = st.columns(3)

with c21:
    kpi_card(titulo="Entradas", 
            valor=faturamento_total, 
            texto_status="Receita de Vendas",
            formato="moeda",
            ajuda="Soma total de todas as vendas confirmadas no período.")

with c22:
    kpi_card(titulo="Saídas", 
             valor=custos_totais, 
             texto_status="Custos de Insumos",
             formato="moeda",
             ajuda="Total gasto com a compra de insumos baseados nas receitas dos produtos vendidos.")
    
with c23:
    kpi_card(titulo="Saldo", 
             valor=lucro_bruto, 
             texto_status=f"{margem_lucro:.2f}% de margem",
             formato="moeda",
             classe_status="kpi-positive" if lucro_bruto > 0 else "kpi-negative",
             ajuda="Lucro bruto calculado como Entradas - Saídas, indicando a saúde financeira do negócio.")

divisor()    

secao_ranking_barras(df=formas_pagamento,
                    col_nome="Forma de Pagamento",
                    col_valor="Porcentagem do Total",
                    col_texto_barra="Total Vendas",
                    tipo_texto_barra="unidade",
                    tipo_valor="percentual",
                    top_n=len(formas_pagamento),
                    titulo="Formas de Pagamento",
                    descricao=f"% do Faturamento e Quantidade de Vendas por Forma de Pagamento.",
)
