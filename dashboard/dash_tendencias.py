import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.utils import gerar_grafico
from scripts.get_data import (get_vendas_por_dia_semana, 
                              get_vendas_por_mes)
from scripts.layout import (layout, 
                            cabecalho, 
                            secao_ranking_barras, 
                            divisor)

# Aplicar o design system global (fontes, cores de fundo e espaçamentos)
layout()

# Cabeçalho estilizado com tipografia hierárquica
cabecalho("Tendências e Análises", "Análise de sazonalidade, comportamento semanal e projeções de crescimento")

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_date = datetime.combine(today, datetime.max.time())
start_date = datetime.combine(today - relativedelta(years=1), datetime.min.time())

st.info(f"Período de análise fixo: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} (Últimos 12 meses)")

get_vendas_sazonais_semana = get_vendas_por_dia_semana(start_date, end_date)
get_vendas_sazonais_mes = get_vendas_por_mes(start_date, end_date)

# 1. Ranking de Sazonalidade Semanal usando componente padrão
secao_ranking_barras(
    df=get_vendas_sazonais_semana,
    col_nome="Dia da Semana",
    col_valor="Total de Vendas",
    col_texto_barra="Variação (%)",
    titulo="Sazonalidade por Dia da Semana",
    descricao="Volume de vendas por dia da semana comparado à variação percentual do período anterior.",
    tipo_valor="unidade",
    tipo_texto_barra="percentual",
    top_n=7
)

divisor()

# 2. Gráfico de Evolução Mensal (o componente gerar_grafico já traz títulos estilizados)
gerar_grafico(
    titulo="Evolução Mensal e Média Móvel",
    descricao="Comparativo de unidades vendidas e tendência (média móvel de 3 meses).",
    granularidade="mensal", 
    dataframe=get_vendas_sazonais_mes, 
    start_date=start_date, 
    end_date=end_date,
    colunas=["Total de Vendas", "Média Móvel (3 meses)"],
    tipo_grafico='linhas',
    coluna_data="Mês",
    cores={"Total de Vendas": "#4682b4", "Média Móvel (3 meses)": "#ff69b4"}
)

# 3. Tabela de Crescimento detalhada
with st.container(border=True):
    st.markdown("""
    <div class="section-title">Análise de Crescimento de Receita</div>
    <div class="section-description">Detalhamento mensal de receita, variação percentual e indicadores de tendência.</div>
    """, unsafe_allow_html=True)
    
    # Exibir a tabela com largura total
    st.dataframe(
        get_vendas_sazonais_mes[["Mês", 'Receita', 'Crescimento (%)', 'Tendência']],
        width='stretch',
        hide_index=True,
        height=500,
        column_config={
            "Mês": st.column_config.Column("Mês", width="auto"),
            "Receita": st.column_config.Column("Receita", width="auto"),
            "Crescimento (%)": st.column_config.Column("Crescimento (%)", width="auto"),
            "Tendência": st.column_config.Column("Tendência", width="auto"),
        }

    )