import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from datetime import datetime
from typing import Union
import streamlit as st

# Configuração da conexão com o banco de dados
engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/projeto_es")

conn = psycopg2.connect(
    host="localhost",
    database="projeto_es",
    user="postgres",
    password="postgres",
    port="5432"
)


def carregar_tabela(nome_tabela: str) -> pd.DataFrame:
    """Carrega uma tabela do banco de dados para um DataFrame do Pandas."""
    query = f"SELECT * FROM public.{nome_tabela};"
    return pd.read_sql(query, engine)

# print(pd.read_sql("SELECT * FROM public.products;", engine))

def get_vendas_produtos(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Calcula o ranking de vendas de produtos por quantidade e valor total."""
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    products = carregar_tabela('products')

    df = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df = pd.merge(df, products, left_on='product_id', right_on='id', suffixes=('_sale', '_product'))

    ranking_vendas = df.groupby(['product_id', 'name']).agg(
    quantidade_vendida=('quantity', 'sum'),
    valor_total_vendas=('total_price', 'sum')
    ).reset_index().sort_values(by='valor_total_vendas', ascending=False)

    ranking_vendas = ranking_vendas.head(5).reset_index(drop=True)

    ranking_vendas.insert(0, 'Posição', range(1, len(ranking_vendas) + 1))

    ranking_vendas = ranking_vendas.rename(columns={
        'name': 'Produto',
        'quantidade_vendida': 'Quantidade Vendida',
        'valor_total_vendas': 'Valor Total das Vendas'
    })

    return ranking_vendas


def get_margem_lucro_produtos(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Calcula o ranking de margem de lucro de produtos."""
    products = carregar_tabela('products')
    recipes = carregar_tabela('recipes')
    recipe_items = carregar_tabela('recipe_items')
    ingredients = carregar_tabela('ingredients')
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')

    # Calcular custo de produção por produto
    df_recipes = pd.merge(recipe_items, ingredients, left_on='ingredient_id', right_on='id', suffixes=('_recipe', '_ingredient'))
    df_recipes['custo_ingrediente'] = df_recipes['quantity'] * df_recipes['purchase_price'] # Assumindo unidades compatíveis
    custo_por_produto = df_recipes.groupby('recipe_id')['custo_ingrediente'].sum().reset_index()

    df_products_cost = pd.merge(recipes, custo_por_produto, left_on='id', right_on='recipe_id', suffixes=('_recipe', '_cost'))
    df_products_cost = pd.merge(products, df_products_cost, left_on='id', right_on='product_id', suffixes=('_product', '_cost'))

    # Filtrar vendas por período para considerar apenas os produtos vendidos no período
    df_sales_filtered = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_sales_filtered['sold_at'] = pd.to_datetime(df_sales_filtered['sold_at'])

    if start_date and end_date:
        df_sales_filtered = df_sales_filtered[(df_sales_filtered['sold_at'] >= start_date) & (df_sales_filtered['sold_at'] <= end_date)]

    # Unir dados de custo com dados de vendas filtrados
    df_final = pd.merge(df_sales_filtered, df_products_cost, left_on='product_id', right_on='id_product', how='inner')

    # Calcular lucro e margem
    df_final['lucro_bruto_unitario'] = df_final['sale_price'] - df_final['custo_ingrediente']
    df_final['lucro_bruto_total'] = df_final['lucro_bruto_unitario'] * df_final['quantity']

    # Agrupar por produto para calcular a margem média
    margem_lucro = df_final.groupby(['product_id_x', 'name_product']).agg(
        total_vendas=('total_price', 'sum'),
        total_custo=('custo_ingrediente', lambda x: (x * df_final.loc[x.index, 'quantity']).sum()),
        total_lucro=('lucro_bruto_total', 'sum')
    ).reset_index()

    margem_lucro['margem_percentual'] = (margem_lucro['total_lucro'] / margem_lucro['total_vendas']) * 100

    margem_lucro = margem_lucro.head(5).reset_index(drop=True)

    margem_lucro.insert(0, 'Posição', range(1, len(margem_lucro) + 1))
    return margem_lucro

def get_margem_lucro_produtos_formatado(start_date: datetime = None, end_date: datetime = None):
    """Retorna DataFrame formatado para exibição."""
    
    df = get_margem_lucro_produtos(start_date, end_date)
    
    if df.empty:
        return df
    
    df_formatado = df.copy()
    
    df_formatado['total_vendas'] = df_formatado['total_vendas'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
    df_formatado['total_custo'] = df_formatado['total_custo'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
    df_formatado['total_lucro'] = df_formatado['total_lucro'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
    df_formatado['margem_percentual'] = df_formatado['margem_percentual'].apply(lambda x: f"{x:.2f}%".replace('.', ','))
    
    df_formatado = df_formatado.rename(columns={
        'name_product': 'Produto',
        'total_vendas': 'Total de Vendas',
        'total_custo': 'Total de Custo',
        'total_lucro': 'Total de Lucro',
        'margem_percentual': 'Margem de Lucro'
    })
    df_formatado = df_formatado.sort_values(by='Margem de Lucro', ascending=False)

    return df_formatado


def get_vendas_categorias(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Calcula o ranking de vendas por categoria de produtos."""
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    products = carregar_tabela('products')
    categories = carregar_tabela('categories')

    df = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df = pd.merge(df, products, left_on='product_id', right_on='id', suffixes=('_sale', '_product'))
    df = pd.merge(df, categories, left_on='category_id', right_on='id', suffixes=('_product', '_category'))

    df['sold_at'] = pd.to_datetime(df['sold_at'])

    if start_date and end_date:
        df = df[(df['sold_at'] >= start_date) & (df['sold_at'] <= end_date)]

    ranking_categorias = df.groupby(['category_id', 'name_category']).agg(
    quantidade_vendida=('quantity', 'sum'),
    valor_total_vendas=('total_price', 'sum')
    ).reset_index().sort_values(by='valor_total_vendas', ascending=False)

    ranking_categorias = ranking_categorias.head(5).reset_index(drop=True)

    ranking_categorias.insert(0, 'Posição', range(1, len(ranking_categorias) + 1))

    ranking_categorias = ranking_categorias.rename(columns={
        'name_category': 'Categoria',
        'quantidade_vendida': 'Quantidade',
        'valor_total_vendas': 'Valor Total'
    })

    return ranking_categorias
    
def get_indice_retorno_rentabilidade(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Índice de Retorno de Rentabilidade (Lucro Líquido / Custo Total)."""
   
    margem_lucro_df = get_margem_lucro_produtos(start_date, end_date)

    if margem_lucro_df.empty:
        return 0.0

    lucro_liquido_total = margem_lucro_df['total_lucro'].sum()
    custo_total = margem_lucro_df['total_custo'].sum()

    if custo_total == 0:
        return 0.0

    indice_rentabilidade = (lucro_liquido_total / custo_total) * 100

    return indice_rentabilidade


def grafico_barras_horizontais(
    df: pd.DataFrame,
    col_nome: str,
    col_valor: str,
    col_texto: str,
    top_n: int = 5,
    formato_valor: str = "moeda",  # "moeda", "percentual" ou "numero"
    formato_texto: str = "moeda"  # "moeda", "percentual" ou "numero",
):
    """
    Renderiza gráfico de barras horizontais estilo dashboard.

    Parâmetros:
    - df: DataFrame
    - col_nome: coluna do eixo Y (nome)
    - col_valor: coluna que define o tamanho da barra
    - col_texto: texto dentro da barra
    - top_n: quantidade de itens (default 5)
    - formato_valor: formato do valor à direita ("moeda", "percentual", "numero")
    """
    df = df.copy()

    df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)

    df = df.sort_values(by=col_valor, ascending=False)
    df = df.head(top_n).reset_index(drop=True)

    max_valor = df[col_valor].max()

    st.markdown("""
    <style>
    .bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }
    .bar-label {
        width: 180px;
        font-size: 13px;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .bar-container {
        flex: 1;
        background-color: #e5e7eb;
        border-radius: 20px;
        height: 22px;
        margin: 0 12px;
        overflow: hidden;
    }
    .bar-fill {
        background-color: #111;
        height: 100%;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 10px;
        color: white;
        font-size: 11px;
        font-weight: 600;
        min-width: 30px;
    }
    .bar-value {
        width: 90px;
        text-align: right;
        font-size: 12px;
        color: #555;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    for _, row in df.iterrows():
        nome = row[col_nome]
        valor = row[col_valor]
        texto = row[col_texto]

        percentual = (valor / max_valor * 100) if max_valor > 0 else 0

        # formatação do valor da direita
        if formato_valor == "moeda":
            valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif formato_valor == "percentual":
            valor_fmt = f"{valor:.2f}%".replace(".", ",")
        else:
            valor_fmt = f"{valor:.2f}"

        if formato_texto == "moeda":
            texto_fmt = f"R$ {texto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif formato_texto == "percentual":
            texto_fmt = f"{texto:.2f}%".replace(".", ",")
        else:
            texto_fmt = f"{texto:.2f}"

        st.markdown(f"""
        <div class="bar-row">
            <div class="bar-label">{nome}</div>
            <div class="bar-container">
                <div class="bar-fill" style="width: {percentual:.1f}%;">
                    {texto_fmt}
                </div>
            </div>
            <div class="bar-value">{valor_fmt}</div>
        </div> """, unsafe_allow_html=True)

def get_dados_vendas_filtrados(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Função auxiliar para unificar e filtrar as vendas no período."""
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    
    # Merge para associar os itens aos dados gerais da venda (como data e total)
    df = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df['sold_at'] = pd.to_datetime(df['sold_at'])
    
    if start_date and end_date:
        df = df[(df['sold_at'] >= start_date) & (df['sold_at'] <= end_date)]
        
    return df


def get_faturamento_total(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Faturamento Total (Soma do valor total de todas as vendas do período)."""
    sales = carregar_tabela('sales')
    sales['sold_at'] = pd.to_datetime(sales['sold_at'])
    
    if start_date and end_date:
        sales = sales[(sales['sold_at'] >= start_date) & (sales['sold_at'] <= end_date)]
        
    return float(sales['total_amount'].sum())


def get_total_vendas(start_date: datetime = None, end_date: datetime = None) -> int:
    """Calcula a quantidade total de pedidos/vendas realizadas no período."""
    sales = carregar_tabela('sale_items')
    sales['created_at'] = pd.to_datetime(sales['created_at'])
    
    if start_date and end_date:
        sales = sales[(sales['created_at'] >= start_date) & (sales['created_at'] <= end_date)]
        
    return int(sales.shape[0])


def get_ticket_medio(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Ticket Médio (Faturamento Total / Total de Vendas)."""
    faturamento = get_faturamento_total(start_date, end_date)
    total_vendas = get_total_vendas(start_date, end_date)
    
    if total_vendas == 0:
        return 0.0
        
    return faturamento / total_vendas


def get_lucro_total(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Lucro Bruto Total do período baseado nos custos de receita."""
    # Reaproveita a lógica que você já criou na sua função original
    margem_df = get_margem_lucro_produtos(start_date, end_date)
    
    if margem_df.empty:
        return 0.0
        
    return float(margem_df['total_lucro'].sum())


def get_lucro_por_periodo(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Retorna Receita e Lucro desagregados por período para gráficos temporais."""
    products = carregar_tabela('products')
    recipes = carregar_tabela('recipes')
    recipe_items = carregar_tabela('recipe_items')
    ingredients = carregar_tabela('ingredients')
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')

    # Calcular custo de produção por produto
    df_recipes = pd.merge(recipe_items, ingredients, left_on='ingredient_id', right_on='id', suffixes=('_recipe', '_ingredient'))
    df_recipes['custo_ingrediente'] = df_recipes['quantity'] * df_recipes['purchase_price']
    custo_por_produto = df_recipes.groupby('recipe_id')['custo_ingrediente'].sum().reset_index()

    df_products_cost = pd.merge(recipes, custo_por_produto, left_on='id', right_on='recipe_id', suffixes=('_recipe', '_cost'))
    df_products_cost = pd.merge(products, df_products_cost, left_on='id', right_on='product_id', suffixes=('_product', '_cost'))

    # Filtrar vendas por período
    df_sales_filtered = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_sales_filtered['sold_at'] = pd.to_datetime(df_sales_filtered['sold_at'])

    if start_date and end_date:
        df_sales_filtered = df_sales_filtered[(df_sales_filtered['sold_at'] >= start_date) & (df_sales_filtered['sold_at'] <= end_date)]

    # Unir dados de custo com vendas
    df_final = pd.merge(df_sales_filtered, df_products_cost, left_on='product_id', right_on='id_product', how='inner')

    # Calcular lucro por item
    df_final['lucro_bruto_unitario'] = df_final['sale_price'] - df_final['custo_ingrediente']
    df_final['lucro_bruto_total'] = df_final['lucro_bruto_unitario'] * df_final['quantity']

    # Retornar com colunas necessárias para o gráfico
    return df_final[['sold_at', 'total_price', 'lucro_bruto_total', 'quantity']]


def get_margem_lucro_geral(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula a Margem de Lucro Geral em % do período (Lucro Total / Faturamento Total * 100)."""
    faturamento = get_faturamento_total(start_date, end_date)
    lucro = get_lucro_total(start_date, end_date)
    
    if faturamento == 0:
        return 0.0
        
    return (lucro / faturamento) * 100


def get_vendas_medias_diarias(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o volume médio de faturamento por dia com base nos dias que tiveram vendas."""
    sales = carregar_tabela('sale_items')
    sales['created_at'] = pd.to_datetime(sales['created_at'])
    
    if start_date and end_date:
        sales = sales[(sales['created_at'] >= start_date) & (sales['created_at'] <= end_date)]
        
    if sales.empty:
        return 0.0
        
    faturamento_por_dia = sales.groupby(sales['created_at'].dt.date)['total_price'].sum()
    
    return float(faturamento_por_dia.mean())

def get_faturamento_por_produto(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """
    Gera um DataFrame onde cada linha é um produto contendo:
    Categoria, Quantidade Vendida, Faturamento e % do Faturamento Total no período.
    """
    # Carregar as tabelas necessárias utilizando sua função nativa
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    products = carregar_tabela('products')
    categories = carregar_tabela('categories')

    # Corrige tipo de data e aplicar o filtro de período nas vendas
    sales['sold_at'] = pd.to_datetime(sales['sold_at'])
    if start_date and end_date:
        sales = sales[(sales['sold_at'] >= start_date) & (sales['sold_at'] <= end_date)]

    # Se não houver vendas no período, retorna um DataFrame vazio com as colunas certas
    if sales.empty:
        return pd.DataFrame(columns=['Produto', 'Categoria', 'Quantidade Vendida', 'Faturamento', '% do faturamento total'])

    # Cruzamento as tabelas (sales -> sale_items -> products -> categories)
    df = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df = pd.merge(df, products, left_on='product_id', right_on='id', suffixes=('_sale', '_product'))
    df = pd.merge(df, categories, left_on='category_id', right_on='id', suffixes=('_product', '_category'))

    # Nota: Usamos 'total_price' dos itens de venda para calcular o faturamento do produto
    df_agrupado = df.groupby(['name_product', 'name_category']).agg(
        quantidade_vendida=('quantity', 'sum'),
        faturamento=('total_price', 'sum')
    ).reset_index()

    faturamento_total_periodo = df_agrupado['faturamento'].sum()
    
    if faturamento_total_periodo > 0:
        df_agrupado['pct_faturamento'] = (df_agrupado['faturamento'] / faturamento_total_periodo) * 100
    else:
        df_agrupado['pct_faturamento'] = 0.0

    df_final = df_agrupado.rename(columns={
        'name_product': 'Produto',
        'name_category': 'Categoria',
        'quantidade_vendida': 'Quantidade Vendida',
        'faturamento': 'Faturamento',
        'pct_faturamento': '% do faturamento total'
    })

    df_final = df_final.sort_values(by='Faturamento', ascending=False).reset_index(drop=True)
    
    df_final['Faturamento'] = df_final['Faturamento'].apply(
        lambda x: f"R$ {x:.2f}".replace('.', ',')
    )
    
    df_final['% do faturamento total'] = df_final['% do faturamento total'].apply(
        lambda x: f"{x:.2f}%".replace('.', ',')
    )
    return df_final