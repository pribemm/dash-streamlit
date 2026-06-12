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
                              get_previsao_demanda_vendas)
from scripts.layout import (layout, 
                            cabecalho, periodo, 
                            secao_ranking_barras, 
                            divisor)

# Aplicar o design system global (fontes, cores de fundo e espaçamentos)
layout()

# Cabeçalho estilizado com tipografia hierárquica
st.title("Avançado")


today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_date = datetime.combine(today, datetime.max.time())
start_date = datetime.combine(today - relativedelta(years=1), datetime.min.time())

st.info(f"Período de análise fixo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} (Últimos 12 meses)")

divisor()

previsao_vendas = get_previsao_demanda_vendas(product_id=1)

st.dataframe(previsao_vendas)

df_juntos = get_produtos_vendidos_juntos(start_date, end_date)
correlacao = pd.DataFrame({
    "Produtos Combinados": df_juntos["Produto A"] + " e " + df_juntos["Produto B"],
    "Frequência": df_juntos["Frequência"],
    "Porcentagem do Total": df_juntos["Porcentagem do Total"]
})

secao_ranking_barras(
    df=correlacao,
    col_nome="Produtos Combinados",
    col_valor="Porcentagem do Total",
    col_texto_barra="Frequência",
    tipo_valor="percentual",
    tipo_texto_barra="unidade",
    titulo="Vendas Combinadas de Produtos",
    descricao="Análise das combinações de produtos mais vendidas.",
    )