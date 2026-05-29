import pandas as pd
import matplotlib.pyplot as plt
# import streamlit as st


# @st.cache_data
def carregar_dados_pedidos():
    df_pedido = pd.read_csv('dash_streamlit/dados/pedidos.csv')
    df_pedido['data'] = pd.to_datetime(df_pedido['data'], dayfirst=True)
    return df_pedido


# @st.cache_data
def carregar_dados_receitas():
    df_receitas_insumos = pd.read_csv('dash_streamlit/dados/receitas_insumos.csv')
    df_insumos = pd.read_csv('dash_streamlit/dados/insumos.csv')
    return df_receitas_insumos, df_insumos


def gerar_grafico_mensal(df_pedido):

    df_semanal = df_pedido.loc[:,['data','valor_total']].groupby(pd.Grouper(key='data', freq="ME")).sum()

    fig, ax = plt.subplots()
    df_semanal.plot(kind="bar", ax=ax)
    
    ax.set_title("Vendas Mensais")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Número de pedidos")
    
    nomes_meses = [d.strftime('%Y-%m') for d in df_semanal.index]
    ax.set_xticklabels(nomes_meses, rotation=45, ha='right')
    plt.tight_layout()
    return fig


def gerar_grafico_semanal(df_pedido):
    df_semanal = df_pedido.loc[:,['data','valor_total']].groupby(pd.Grouper(key='data', freq="W")).sum()

    fig, ax = plt.subplots()
    df_semanal.plot(kind="bar", ax=ax)

    ax.set_title("Vendas Semanais")
    ax.set_xlabel("Semana")
    ax.set_ylabel("Número de pedidos")
    ax.set_xticklabels(df_semanal.index, rotation=45, ha='right')
    plt.tight_layout()
    return fig


def gerar_top_produtos(df_pedido, top_n=5):
    df_produtos = df_pedido.explode('produto') 
    df_produtos['produto'] = df_produtos['produto'].str.strip('[]').str.split(',')
    df_produtos = df_produtos.explode('produto')
    top_produtos = df_produtos['produto'].value_counts().head(top_n)
    return top_produtos


def carregar_itens_pedido():
    df_itens_pedido = pd.read_csv('dash_streamlit/dados/itens_pedido.csv')
    return df_itens_pedido  


def gerar_tabela_produtos_mais_vendidos(df_pedido, n=5):  
    df_pedido = carregar_itens_pedido()
    tabela_qtd_produtos = df_pedido.groupby('id_cardapio')['quantidade'].sum().reset_index()
    tabela_qtd_produtos = tabela_qtd_produtos.sort_values(by='quantidade', ascending=False)
    tabela_qtd_produtos['faturamento_unitario'] = df_pedido[df_pedido['id_cardapio'] == row['id_cardapio']]['preco_unitario'].values[0]
    tabela_qtd_produtos['faturamento_total'] = tabela_qtd_produtos['quantidade'] * tabela_qtd_produtos['faturamento_unitario']
    df_tabela_qtd_produtos = pd.DataFrame(tabela_qtd_produtos)
    return df_tabela_qtd_produtos.head(n)


def calcular_ticket_medio(df_pedido):
    ticket_medio = df_pedido['valor_total'].sum() / len(df_pedido)
    return round(ticket_medio, 2)


def tabela_vendas_diarias(df_pedido):
    vendas_diarias = df_pedido.groupby(df_pedido['data'].dt.date).size()
    return vendas_diarias.reset_index(name='vendas_diarias')

# df_pedido = carregar_dados_pedidos()
# tabela_vendas_diarias = tabela_vendas_diarias(df_pedido)
# print(tabela_vendas_diarias)


def calcular_vendas_medias_diarias(df_pedido):
    vendas_diarias = df_pedido.groupby(df_pedido['data'].dt.date).size()
    vendas_medias_diarias = vendas_diarias.mean()
    return round(vendas_medias_diarias, 2)


def calcular_custo(df_pedido):
    custo_total = df_pedido['custo_total'].sum()
    return round(custo_total, 2)


def custo_total_receita(id_receita, df_receitas_insumos, df_insumos):
    custo_total = 0
    receitas_filtradas = df_receitas_insumos[df_receitas_insumos['id_receita'] == id_receita]
    
    for index, receita in receitas_filtradas.iterrows():
        id_insumo = receita['id_insumo']
        quantidade = receita['quantidade']
        preco_unitario = df_insumos[df_insumos['id_insumo'] == id_insumo]['custo_unitario'].values[0]
        custo_total += quantidade * preco_unitario
    return custo_total