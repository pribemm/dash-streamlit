import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.get_data import (get_produtos_vendidos_juntos,
                            get_previsao_demanda_vendas,
                            get_abc_produtos,
                            get_previsao_demanda,
                            )

from scripts.layout import (layout,
                            render_cards_abc,
                            render_cards_previsao,
                            secao_ranking_barras, 
                            divisor)

layout()

st.title("Avançado")

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_date = datetime.combine(today, datetime.max.time())
start_date = datetime.combine(today - relativedelta(years=1), datetime.min.time())

st.info(f"Período de análise fixo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} (Últimos 12 meses)")

previsoes = get_previsao_demanda()
df_abc = get_abc_produtos(start_date, end_date)
previsao_vendas = get_previsao_demanda_vendas(product_id=1)
df_juntos = get_produtos_vendidos_juntos(start_date, end_date)
correlacao = pd.DataFrame({
    "Produtos Combinados": df_juntos["Produto A"] + " e " + df_juntos["Produto B"],
    "Frequência": df_juntos["Frequência"],
    "Porcentagem do Total": df_juntos["Porcentagem do Total"]
})


divisor()

st.subheader("Previsão de Demanda")

render_cards_previsao(previsoes)

st.markdown("""
<div style="
    background-color: #e6f3ff;
    padding: 15px;
    border-radius: 8px;
    border-left: 5px solid #1f77b4;
    color: #000;
">
Projeta os 3 meses seguintes usando a reta de tendência com o crescimento médio histórico.
</div>
""", unsafe_allow_html=True)

st.subheader("Análise ABC de produtos")

render_cards_abc(df_abc)

st.markdown("""
<div style="
    background-color: #e6f3ff;
    padding: 15px;
    border-radius: 8px;
    border-left: 5px solid #1f77b4;
    color: #000;
">
Classificação dos itens de acordo com a importância na receita.</div>
""", unsafe_allow_html=True)

divisor()

secao_ranking_barras(
    df=correlacao,
    col_nome="Produtos Combinados",
    col_valor="Porcentagem do Total",
    tipo_valor="percentual",
    titulo="Vendas mais Efetuadas Juntas",
    descricao="Análise das combinações de produtos mais vendidas.",
    )

