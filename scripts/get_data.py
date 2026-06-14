import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import streamlit as st
import numpy as np
import sys
import os
from sqlalchemy import text

current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from scripts.layout import estilo_grafico_barras
from scripts.utils import get_payment_name
from scripts.db import carregar_tabela, engine


# try:
#     conn = psycopg2.connect(
#         host="localhost",
#         database="marmitaria",
#         user="postgres",
#         password="postgres",
#         port="5432"
#     )
#     conn.close()
# except Exception as e:
#     print("Erro ao conectar ao banco de dados:", e)

def carregar_vendas_periodo(
    start_date: datetime = None,
    end_date: datetime = None,
    apenas_concluidas: bool = True
) -> pd.DataFrame:
    """
    Carrega vendas com filtro de data direto no SQL.
    Evita trazer toda a tabela para o Python só para filtrar depois.
    """
    conditions = []
    params = {}

    if start_date is not None:
        conditions.append("sold_at >= :start_date")
        params["start_date"] = start_date
    if end_date is not None:
        conditions.append("sold_at <= :end_date")
        params["end_date"] = end_date
    if apenas_concluidas:
        conditions.append("status = 0")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    query = text(f"SELECT * FROM public.sales {where}")

    with engine.connect() as conn:
        return pd.read_sql(query, conn, params=params)

def get_vendas_produtos(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Calcula o ranking de vendas de produtos por quantidade e valor total."""
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    products = carregar_tabela('products')

    df_sales = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_sales['sold_at'] = pd.to_datetime(df_sales['sold_at'])

    if start_date is not None:
        df_sales = df_sales[df_sales['sold_at'] >= start_date]
    if end_date is not None:
        df_sales = df_sales[df_sales['sold_at'] <= end_date]

    df = pd.merge(df_sales, products, left_on='product_id', right_on='id', suffixes=('_sale', '_product'))

    ranking_vendas = df.groupby(['product_id', 'name']).agg(
    quantidade_vendida=('quantity', 'sum'),
    valor_total_vendas=('total_price', 'sum')
    ).reset_index().sort_values(by='valor_total_vendas', ascending=False)

    ranking_vendas.insert(0, 'Posição', range(1, len(ranking_vendas) + 1))

    ranking_vendas = ranking_vendas.rename(columns={
        'name': 'Produto',
        'quantidade_vendida': 'Quantidade Vendida',
        'valor_total_vendas': 'Valor Total das Vendas'
    })

    return ranking_vendas


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

def get_consumo_insumos_por_periodo(
    start_date: datetime = None, end_date: datetime = None
) -> pd.DataFrame:
    """Retorna o consumo de insumos por período.

    Cada linha representa um insumo com a quantidade utilizada e o valor gasto.

    Args:
        start_date: Data inicial do período (inclusive). Se None, sem limite inferior.
        end_date: Data final do período (inclusive). Se None, sem limite superior.

    Returns:
        DataFrame com colunas: Insumo, Código, Quantidade Utilizada, Valor Gasto.
    """
    # Dados utilizados
    ingredients = carregar_tabela("ingredients")
    recipes = carregar_tabela("recipes")        
    recipe_items = carregar_tabela("recipe_items")
    sales = carregar_tabela("sales")
    sale_items = carregar_tabela("sale_items")
    
    # Filtro de período
    sales["sold_at"] = pd.to_datetime(sales["sold_at"])
    if start_date:
        sales = sales[sales["sold_at"] >= start_date]
    if end_date:
        sales = sales[sales["sold_at"] <= end_date]

    # Considera apenas vendas concluídas
    if "status" in sales.columns:
        sales = sales[sales["status"] == 0]
       
    # --- Retorno antecipado se não há vendas no período ---
    if sales.empty:
        return pd.DataFrame({
            "Insumo": ingredients["name"],
            "Quantidade Utilizada": 0.0,
            "Valor Gasto": 0.0,
        })

    sale_items = sale_items.rename(columns={"id": "sale_item_id", "quantity": "qty_sold"})

    df = pd.merge(
        sale_items[["sale_item_id", "sale_id", "product_id", "qty_sold"]],
        sales[["id"]],          # só precisamos confirmar que a venda existe no filtro
        left_on="sale_id",
        right_on="id",
        how="inner",
    ).drop(columns=["id"])
    
    if df.empty:
        return pd.DataFrame({
            "Insumo": ingredients["name"],
            "Quantidade Utilizada": 0.0,
            "Valor Gasto": 0.0,
        })

    recipes = recipes.rename(columns={"id": "recipe_id"})

    df = pd.merge(
        df,
        recipes[["recipe_id", "product_id"]],
        on="product_id",
        how="inner",            # produtos sem receita são descartados
    )

    recipe_items = recipe_items.rename(columns={"quantity": "qty_recipe"})

    df = pd.merge(
        df,
        recipe_items[["recipe_id", "ingredient_id", "qty_recipe"]],
        on="recipe_id",
        how="inner",
    )

    ingredients = ingredients.rename(columns={"id": "ingredient_id"})

    df = pd.merge(
        df,
        ingredients[["ingredient_id", "name", "code", "purchase_price"]],
        on="ingredient_id",
        how="left",
    )
    
    df["Quantidade Utilizada"] = df["qty_sold"] * df["qty_recipe"]
    df["Valor Gasto"] = df["Quantidade Utilizada"] * df["purchase_price"]

    df_consumo = (
        df.groupby(["ingredient_id", "name"], as_index=False)
        .agg({"Quantidade Utilizada": "sum", "Valor Gasto": "sum"})
        .rename(columns={"name": "Insumo"})
        .sort_values(by="Valor Gasto", ascending=False)
        .reset_index(drop=True)
    )

    return df_consumo[["Insumo", "Quantidade Utilizada", "Valor Gasto"]]


def get_giro_estoque_insumos(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Gera a tabela de giro de estoque por insumo."""

    ingredients = carregar_tabela("ingredients")
    recipes = carregar_tabela("recipes")
    recipe_items = carregar_tabela("recipe_items")
    sales = carregar_tabela("sales")
    sale_items = carregar_tabela("sale_items")
    stock_movements = carregar_tabela("stock_movements")

    # ── Tratamento de datas───
    if start_date is None and end_date is None:
        end_date = pd.Timestamp.now().normalize()
        start_date = end_date - pd.Timedelta(days=29)
    elif start_date is None:
        end_date = pd.to_datetime(end_date)
        start_date = end_date - pd.Timedelta(days=29)
    elif end_date is None:
        start_date = pd.to_datetime(start_date)
        end_date = start_date + pd.Timedelta(days=29)
    else:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Apenas vendas finalizadas
    sales["sold_at"] = pd.to_datetime(sales["sold_at"], utc=True).dt.tz_convert(None)
    if "status" in sales.columns:
        sales = sales[sales["status"] == 0]

    sales_periodo = sales[
        (sales["sold_at"] >= start_date) & (sales["sold_at"] <= end_date)
    ]

    # Calcular consumo por ingrediente 
    sale_items = sale_items.rename(columns={"quantity": "qty_sold"})
    df_vendas = pd.merge(
        sale_items[["sale_id", "product_id", "qty_sold"]],
        sales_periodo[["id"]],
        left_on="sale_id",
        right_on="id",
        how="inner",
    ).drop(columns=["id"])

    # Filtrar apenas receitas ativas
    recipes = recipes.rename(columns={"id": "recipe_id"})
    if "active" in recipes.columns:
        recipes = recipes[recipes["active"] == True]

    df_vendas = pd.merge(
        df_vendas,
        recipes[["recipe_id", "product_id"]],
        on="product_id",
        how="inner",
    )

    recipe_items = recipe_items.rename(columns={"quantity": "qty_recipe"})
    df_vendas = pd.merge(
        df_vendas,
        recipe_items[["recipe_id", "ingredient_id", "qty_recipe"]],
        on="recipe_id",
        how="inner",
    )

    df_vendas["Quantidade Utilizada"] = df_vendas["qty_sold"] * df_vendas["qty_recipe"]

    consumo_por_insumo = (
        df_vendas
        .groupby("ingredient_id", as_index=False)
        .agg({"Quantidade Utilizada": "sum"})
    )

    # Filtrar apenas ingredientes ativos
    if "active" in ingredients.columns:
        ingredients_ativos = ingredients[ingredients["active"] == True]
    else:
        ingredients_ativos = ingredients

    consumo_por_insumo = pd.merge(
        consumo_por_insumo,
        ingredients_ativos[["id", "name", "unit"]].rename(columns={"id": "ingredient_id"}),
        on="ingredient_id",
        how="left",
    )

    # Consumo mensal
    dias_periodo = max((end_date - start_date).days + 1, 1)
    meses_periodo = dias_periodo / 30.44
    consumo_por_insumo["Consumo Mensal"] = (
        consumo_por_insumo["Quantidade Utilizada"] / meses_periodo
    )

    # ── Estoque baseado em movimentações ─────────────────────────────────────
    if not stock_movements.empty:

        # Normalizar timezone do occurred_at (evita erro de comparação tz-aware vs tz-naive)
        stock_movements["occurred_at"] = (
            pd.to_datetime(stock_movements["occurred_at"], utc=True).dt.tz_convert(None)
        )

        def _safe_groupby_sum(
            df: pd.DataFrame, group_col: str, value_col: str
        ) -> pd.Series:
            """Garante que groupby sempre retorna uma Series, nunca um DataFrame."""
            if df.empty:
                return pd.Series(dtype=float, name=value_col)
            result = df.groupby(group_col)[value_col].sum()
            return result if isinstance(result, pd.Series) else result.squeeze()

        # Estoque inicial: movimentações ANTES do período (vetorizado, sem loop)
        mov_antes = stock_movements[stock_movements["occurred_at"] < start_date]
        entradas_antes = _safe_groupby_sum(
            mov_antes[mov_antes["movement_type"].isin([1, 2])], "ingredient_id", "quantity"
        )
        saidas_antes = _safe_groupby_sum(
            mov_antes[mov_antes["movement_type"] == 3], "ingredient_id", "quantity"
        )
        estoque_inicial_series = entradas_antes.subtract(saidas_antes, fill_value=0)

        # Para ingredientes sem movimentação anterior, usar current_stock como fallback
        for ing_id in consumo_por_insumo["ingredient_id"].unique():
            if ing_id not in estoque_inicial_series.index:
                row = ingredients_ativos[ingredients_ativos["id"] == ing_id]
                fallback = float(row["current_stock"].values[0]) if len(row) > 0 else 0.0
                estoque_inicial_series[ing_id] = fallback

        # Entradas e saídas DENTRO do período selecionado
        mov_periodo = stock_movements[
            (stock_movements["occurred_at"] >= start_date)
            & (stock_movements["occurred_at"] <= end_date)
        ]

        entradas = _safe_groupby_sum(
            mov_periodo[mov_periodo["movement_type"].isin([1, 2])],
            "ingredient_id",
            "quantity",
        )
        saidas = _safe_groupby_sum(
            mov_periodo[mov_periodo["movement_type"] == 3],
            "ingredient_id",
            "quantity",
        )

        consumo_por_insumo["Estoque Inicial"] = (
            consumo_por_insumo["ingredient_id"].map(estoque_inicial_series).fillna(0)
        )
        consumo_por_insumo["Entradas"] = (
            consumo_por_insumo["ingredient_id"].map(entradas).fillna(0)
        )
        consumo_por_insumo["Saidas"] = (
            consumo_por_insumo["ingredient_id"].map(saidas).fillna(0)
        )

        consumo_por_insumo["Estoque Final"] = (
            consumo_por_insumo["Estoque Inicial"]
            + consumo_por_insumo["Entradas"]
            - consumo_por_insumo["Saidas"]
            - consumo_por_insumo["Quantidade Utilizada"]
        )
        consumo_por_insumo["Estoque Médio"] = (
            consumo_por_insumo["Estoque Inicial"] + consumo_por_insumo["Estoque Final"]
        ) / 2
        consumo_por_insumo["Estoque Atual"] = consumo_por_insumo["Estoque Final"]

    else:
        # Sem movimentações: usar current_stock como referência
        consumo_por_insumo = pd.merge(
            consumo_por_insumo,
            ingredients_ativos[["id", "current_stock"]].rename(
                columns={"id": "ingredient_id"}
            ),
            on="ingredient_id",
            how="left",
        )
        consumo_por_insumo["Estoque Atual"] = consumo_por_insumo["current_stock"].fillna(0)
        consumo_por_insumo["Estoque Médio"] = consumo_por_insumo["Estoque Atual"]

    # Giro. Número de vezes ao mês que estoque se renova
    consumo_por_insumo["Giro"] = consumo_por_insumo.apply(
        lambda row: (
            row["Consumo Mensal"] / row["Estoque Médio"]
            if row["Estoque Médio"] > 0
            else 0
        ),
        axis=1,
    )

    # Cobertura (dias de estoque)
    consumo_por_insumo["Cobertura"] = consumo_por_insumo.apply(
        lambda row: (
            row["Estoque Atual"] / row["Consumo Mensal"] * 30
            if row["Consumo Mensal"] > 0
            else 999
        ),
        axis=1,
    )

    # Status baseado no giro
    def classificar_giro(giro: float) -> str:
        if giro > 2:
            return "Giro Alto"
        if giro < 0.5:
            return "Giro Baixo"
        return "Normal"

    consumo_por_insumo["Status"] = consumo_por_insumo["Giro"].apply(classificar_giro)

    # ── Formatar retorno──────
    retorno = consumo_por_insumo[
        ["name", "unit", "Consumo Mensal", "Estoque Atual", "Cobertura", "Giro", "Status"]
    ].copy()

    retorno = retorno.rename(columns={"name": "Insumo", "unit": "Unidade"})
    retorno = retorno.sort_values(by="Giro", ascending=False).reset_index(drop=True)

    retorno["Consumo Mensal"] = retorno["Consumo Mensal"].apply(lambda x: f"{x:.2f}")
    retorno["Estoque Atual"] = retorno["Estoque Atual"].apply(lambda x: f"{x:.2f}")
    retorno["Giro"] = retorno["Giro"].apply(lambda x: f"{x:.2f}x")
    retorno["Cobertura"] = retorno["Cobertura"].apply(
        lambda x: f"{int(x)} dias" if pd.notna(x) and x < 999 else "> 999 dias"
    )

    return retorno

def get_insumos_estoque_baixo(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """Retorna insumos com estoque abaixo do mínimo e cobertura estimada em dias."""
    ingredients = carregar_tabela("ingredients")
    recipes = carregar_tabela("recipes")
    recipe_items = carregar_tabela("recipe_items")
    sales = carregar_tabela("sales")
    sale_items = carregar_tabela("sale_items")

    ingredients["current_stock"] = pd.to_numeric(ingredients["current_stock"], errors="coerce").fillna(0)
    ingredients["minimum_stock"] = pd.to_numeric(ingredients["minimum_stock"], errors="coerce").fillna(0)
    ingredients["purchase_price"] = pd.to_numeric(ingredients["purchase_price"], errors="coerce").fillna(0)

    low_stock = ingredients[ingredients["current_stock"] < ingredients["minimum_stock"]].copy()
    if low_stock.empty:
        return pd.DataFrame(columns=["Insumo", "Unidade", "Dias", "Estoque Atual", "Consumo Mensal"])

    if start_date is None and end_date is None:
        end_date = pd.Timestamp.now().normalize()
        start_date = end_date - pd.Timedelta(days=29)
    elif start_date is None:
        end_date = pd.to_datetime(end_date)
        start_date = end_date - pd.Timedelta(days=29)
    elif end_date is None:
        start_date = pd.to_datetime(start_date)
        end_date = start_date + pd.Timedelta(days=29)
    else:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    sales["sold_at"] = pd.to_datetime(sales["sold_at"])
    if "status" in sales.columns:
        sales = sales[sales["status"] == 0]
    vendas_periodo = sales[(sales["sold_at"] >= start_date) & (sales["sold_at"] <= end_date)]

    sale_items = sale_items.rename(columns={"quantity": "qty_sold"})
    df_vendas = pd.merge(
        sale_items[["sale_id", "product_id", "qty_sold"]],
        vendas_periodo[["id"]],
        left_on="sale_id",
        right_on="id",
        how="inner",
    ).drop(columns=["id"])

    recipes = recipes.rename(columns={"id": "recipe_id"})
    df_vendas = pd.merge(
        df_vendas,
        recipes[["recipe_id", "product_id"]],
        on="product_id",
        how="inner",
    )

    recipe_items = recipe_items.rename(columns={"quantity": "qty_recipe"})
    df_vendas = pd.merge(
        df_vendas,
        recipe_items[["recipe_id", "ingredient_id", "qty_recipe"]],
        on="recipe_id",
        how="inner",
    )

    df_consumo = pd.merge(
        df_vendas,
        ingredients[["id", "name", "unit", "current_stock"]].rename(columns={"id": "ingredient_id"}),
        on="ingredient_id",
        how="right",
    )

    df_consumo["qty_sold"] = df_consumo["qty_sold"].fillna(0)
    df_consumo["qty_recipe"] = df_consumo["qty_recipe"].fillna(0)
    df_consumo["Consumo Mensal"] = df_consumo["qty_sold"] * df_consumo["qty_recipe"]

    consumo_por_insumo = (
        df_consumo
        .groupby(["ingredient_id", "name", "unit", "current_stock"], as_index=False)
        .agg({"Consumo Mensal": "sum"})
        .rename(columns={"name": "Insumo", "unit": "Unidade", "current_stock": "Estoque Atual"})
    )

    consumo_por_insumo = consumo_por_insumo.merge(
        low_stock[["id"]].rename(columns={"id": "ingredient_id"}),
        on="ingredient_id",
        how="right",
    )

    consumo_por_insumo["Consumo Mensal"] = consumo_por_insumo["Consumo Mensal"].fillna(0)
    consumo_por_insumo["Dias"] = consumo_por_insumo.apply(
        lambda row: int(np.floor((row["Estoque Atual"] / (row["Consumo Mensal"] / 30)) if row["Consumo Mensal"] > 0 else 0)),
        axis=1,
    )

    return consumo_por_insumo[["Insumo", "Unidade", "Dias", "Estoque Atual", "Consumo Mensal"]].sort_values(by="Dias")


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

    if start_date is not None: 
        df = df[df['sold_at'] >= start_date] 
    if end_date is not None: 
        df = df[df['sold_at'] <= end_date]

    ranking_categorias = df.groupby(['category_id', 'name_category']).agg(
    quantidade_vendida=('quantity', 'sum'),
    valor_total_vendas=('total_price', 'sum')
    ).reset_index().sort_values(by='valor_total_vendas', ascending=False)

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

    estilo_grafico_barras()

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

def get_faturamento_total(start_date=None, end_date=None) -> float:
    sales = carregar_vendas_periodo(start_date, end_date)
    return float(sales['total_amount'].sum())

def get_total_vendas(start_date=None, end_date=None) -> int:
    sales = carregar_vendas_periodo(start_date, end_date)
    return int(len(sales))

from datetime import datetime, timedelta

# Obtém a data e hora atual
now = datetime.now()

# Define o início do dia de hoje (00:00:00)
start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

# Define o final do dia de hoje (23:59:59.999999)
end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

print(carregar_vendas_periodo(start_date, end_date))

def get_dados_vendas_filtrados(start_date=None, end_date=None) -> pd.DataFrame:
    sales = carregar_vendas_periodo(start_date, end_date)
    sale_items = carregar_tabela('sale_items')
    return pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))


def get_ticket_medio(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Ticket Médio (Faturamento Total / Total de Vendas)."""
    faturamento = get_faturamento_total(start_date, end_date)
    total_vendas = get_total_vendas(start_date, end_date)
    
    if total_vendas == 0:
        return 0.0
        
    return faturamento / total_vendas


def get_custos_totais(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula os Custos Totais do período (Soma do valor gasto com insumos)."""
    df_consumo = get_consumo_insumos_por_periodo(start_date, end_date)
    if df_consumo.empty:
        return 0.0
    return float(df_consumo['Valor Gasto'].sum())


def get_lucro_total(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o Lucro Bruto Total do período baseado nos custos de receita."""
    # Reaproveita a lógica que você já criou na sua função original
    margem_df = get_margem_lucro_produtos(start_date, end_date)
    
    if margem_df.empty:
        return 0.0
        
    return float(margem_df['total_lucro'].sum())

def _calcular_custo_por_produto(
    products: pd.DataFrame,
    recipes: pd.DataFrame,
    recipe_items: pd.DataFrame,
    ingredients: pd.DataFrame,
) -> pd.DataFrame:
    """
    Helper interno: retorna df com custo de ingredientes por produto.
    Elimina a duplicação entre get_margem_lucro_produtos e get_lucro_por_periodo.
    """
    df = pd.merge(recipe_items, ingredients,
                  left_on='ingredient_id', right_on='id',
                  suffixes=('_recipe', '_ingredient'))
    df['custo_ingrediente'] = df['quantity'] * df['purchase_price']
    custo_por_receita = df.groupby('recipe_id')['custo_ingrediente'].sum().reset_index()

    df_custo = pd.merge(recipes, custo_por_receita, left_on='id', right_on='recipe_id')
    df_custo = pd.merge(products, df_custo, left_on='id', right_on='product_id',
                        suffixes=('_product', '_cost'))
    return df_custo


def get_lucro_por_periodo(start_date=None, end_date=None) -> pd.DataFrame:
    products      = carregar_tabela('products')
    recipes       = carregar_tabela('recipes')
    recipe_items  = carregar_tabela('recipe_items')
    ingredients   = carregar_tabela('ingredients')

    df_products_cost = _calcular_custo_por_produto(products, recipes, recipe_items, ingredients)  # ← aqui

    sales = carregar_vendas_periodo(start_date, end_date)
    sale_items = carregar_tabela('sale_items')
    # Filtrar vendas por período
    df_sales_filtered = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_sales_filtered['sold_at'] = pd.to_datetime(df_sales_filtered['sold_at'])

    if start_date is not None: 
        df_sales_filtered = df_sales_filtered[df_sales_filtered['sold_at'] >= start_date] 
    if end_date is not None: 
        df_sales_filtered = df_sales_filtered[df_sales_filtered['sold_at'] <= end_date]
    
    # Unir dados de custo com vendas
    # Alterado para 'left' para garantir que vendas sem receita cadastrada ainda apareçam na receita total
    df_final = pd.merge(df_sales_filtered, df_products_cost, left_on='product_id', right_on='id_product', how='left')

    # Calcular lucro por item
    df_final['custo_ingrediente'] = df_final['custo_ingrediente'].fillna(0)
    df_final['lucro_bruto_unitario'] = df_final['unit_price'] - df_final['custo_ingrediente']
    df_final['lucro_bruto_total'] = (df_final['unit_price'] - df_final['custo_ingrediente']) * df_final['quantity']

    # Retornar com colunas necessárias para o gráfico
    return df_final[['sold_at', 'total_price', 'lucro_bruto_total', 'quantity']]


def get_margem_lucro_produtos(start_date=None, end_date=None) -> pd.DataFrame:
    products      = carregar_tabela('products')
    recipes       = carregar_tabela('recipes')
    recipe_items  = carregar_tabela('recipe_items')
    ingredients   = carregar_tabela('ingredients')

    df_products_cost = _calcular_custo_por_produto(products, recipes, recipe_items, ingredients)  # ← aqui

    df_sales = carregar_vendas_periodo(start_date, end_date)
    sale_items = carregar_tabela('sale_items')
    df_sales_filtered = pd.merge(sale_items, df_sales, left_on='sale_id', right_on='id',
                                  suffixes=('_item', '_sale'))
    df_sales_filtered['sold_at'] = pd.to_datetime(df_sales_filtered['sold_at'])

    if start_date is not None:
        df_sales_filtered = df_sales_filtered[df_sales_filtered['sold_at'] >= start_date]
    if end_date is not None:
        df_sales_filtered = df_sales_filtered[df_sales_filtered['sold_at'] <= end_date]

    # Unir dados de custo com dados de vendas filtrados
    df_final = pd.merge(df_sales_filtered, df_products_cost, left_on='product_id', right_on='id_product', how='left')
    df_final['custo_ingrediente'] = df_final['custo_ingrediente'].fillna(0)
    df_final['lucro_bruto_unitario'] = df_final['unit_price'] - df_final['custo_ingrediente']
    df_final['lucro_bruto_total'] = df_final['lucro_bruto_unitario'] * df_final['quantity']
    
    # ✅ Novo: coluna de custo total calculada antes do groupby
    df_final['custo_total'] = df_final['custo_ingrediente'] * df_final['quantity']

    margem_lucro = df_final.groupby(['product_id_x', 'name_product']).agg(
        total_vendas=('total_price', 'sum'),
        total_custo=('custo_total', 'sum'),        # ← antes era a lambda problemática
        total_lucro=('lucro_bruto_total', 'sum')
    ).reset_index()
    
    margem_lucro['margem_percentual'] = (margem_lucro['total_lucro'] / margem_lucro['total_vendas']) * 100

    margem_lucro.insert(0, 'Posição', range(1, len(margem_lucro) + 1))
    return margem_lucro
   

def get_margem_lucro_geral(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula a Margem de Lucro Geral em % do período (Lucro Total / Faturamento Total * 100)."""
    faturamento = get_faturamento_total(start_date, end_date)
    lucro = get_lucro_total(start_date, end_date)
    
    if faturamento == 0:
        return 0.0
        
    return (lucro / faturamento) * 100


def get_vendas_medias_diarias(start_date: datetime = None, end_date: datetime = None) -> float:
    """Calcula o faturamento médio por dia com base nos dias que tiveram vendas."""
    sales = carregar_tabela('sales')         
    sales['sold_at'] = pd.to_datetime(sales['sold_at']) 

    if start_date is not None:
        sales = sales[sales['sold_at'] >= start_date]
    if end_date is not None:
        sales = sales[sales['sold_at'] <= end_date]

    if sales.empty:
        return 0.0

    faturamento_por_dia = sales.groupby(sales['sold_at'].dt.date)['total_amount'].sum()  # ← era 'total_price'
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
    
    if start_date is not None: 
        sales = sales[sales['sold_at'] >= start_date] 
    if end_date is not None: 
        sales = sales[sales['sold_at'] <= end_date]
    
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

def get_vendas_por_dia_semana(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Gera um DataFrame agrupando as unidades vendidas por dia da semana no período 
    selecionado e calcula a variação percentual em relação ao período anterior.
    """
    # 1. Definir o período anterior de mesma duração para comparação
    duracao = end_date - start_date
    prev_start_date = start_date - duracao
    prev_end_date = start_date - timedelta(seconds=1)

    # 2. Carregar dados e associar itens às datas de venda
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    df_vendas = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_vendas['sold_at'] = pd.to_datetime(df_vendas['sold_at'])

    # 3. Filtrar dados dos dois períodos
    df_atual = df_vendas[(df_vendas['sold_at'] >= start_date) & (df_vendas['sold_at'] <= end_date)].copy()
    df_anterior = df_vendas[(df_vendas['sold_at'] >= prev_start_date) & (df_vendas['sold_at'] <= prev_end_date)].copy()

    # 4. Função auxiliar para agrupar por dia da semana (0=Segunda, 6=Domingo)
    def totalizar_por_dia(df):
        if df.empty:
            return pd.DataFrame(columns=['dia_num', 'quantity'])
        df['dia_num'] = df['sold_at'].dt.dayofweek
        return df.groupby('dia_num')['quantity'].sum().reset_index()

    atual_agrupado = totalizar_por_dia(df_atual)
    anterior_agrupado = totalizar_por_dia(df_anterior)

    # 5. Construir base com todos os dias da semana para garantir 7 linhas
    dias_nomes = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
    df_final = pd.DataFrame({'dia_num': range(7)})
    df_final = df_final.merge(atual_agrupado, on='dia_num', how='left').fillna(0)
    df_final = df_final.merge(anterior_agrupado, on='dia_num', how='left', suffixes=('', '_prev')).fillna(0)

    # 6. Calcular a média móvel de 3 dias e a variação percentual
    df_final['Média Móvel (3 dias)'] = df_final['quantity'].rolling(window=3, min_periods=1).mean().round(2)

    def calc_variacao(row):
        if row['quantity_prev'] == 0:
            return 100.0 if row['quantity'] > 0 else 0.0
        return ((row['quantity'] - row['quantity_prev']) / row['quantity_prev']) * 100

    df_final['Variação (%)'] = df_final.apply(calc_variacao, axis=1)
    df_final['Dia da Semana'] = df_final['dia_num'].map(dias_nomes)
    
    return df_final.rename(columns={'quantity': 'Total de Vendas'})[
        ['Dia da Semana', 'Total de Vendas', 'Média Móvel (3 dias)', 'Variação (%)']
    ]

def get_vendas_por_mes(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Gera um DataFrame agrupando as unidades vendidas por mês no período
    selecionado e calcula a variação percentual em relação ao período anterior,
    incluindo a média móvel de 3 meses.
    """
    # 1. Definir o período anterior como exatamente 12 meses atrás para comparação Year-over-Year
    prev_start_date = start_date - relativedelta(years=1)
    prev_end_date = end_date - relativedelta(years=1)

    # 2. Carregar dados e associar itens às datas de venda
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    df_vendas = pd.merge(sale_items, sales, left_on='sale_id', right_on='id', suffixes=('_item', '_sale'))
    df_vendas['sold_at'] = pd.to_datetime(df_vendas['sold_at'])

    # 3. Filtrar dados dos dois períodos
    df_atual = df_vendas[(df_vendas['sold_at'] >= start_date) & (df_vendas['sold_at'] <= end_date)].copy()
    df_anterior = df_vendas[(df_vendas['sold_at'] >= prev_start_date) & (df_vendas['sold_at'] <= prev_end_date)].copy()

    # 4. Função auxiliar para agrupar por mês e ano (formato YYYY-MM)
    def totalizar_por_mes(df):
        if df.empty:
            return pd.DataFrame(columns=['mes_ano', 'mes_num', 'quantity', 'total_price'])
        df['mes_ano'] = df['sold_at'].dt.strftime('%Y-%m')
        df['mes_num'] = df['sold_at'].dt.month
        return df.groupby(['mes_ano', 'mes_num']).agg(
            quantity=('quantity', 'sum'),
            total_price=('total_price', 'sum')
        ).reset_index()
    
    atual_agrupado = totalizar_por_mes(df_atual)
    anterior_agrupado = totalizar_por_mes(df_anterior)

    # 5. Construir base com os meses do período atual para garantir continuidade
    all_months_range = pd.date_range(start=start_date.replace(day=1), end=end_date, freq='MS')
    df_final = pd.DataFrame({
        'mes_ano': all_months_range.strftime('%Y-%m'),
        'mes_num': all_months_range.month
    }).sort_values('mes_ano')

    df_final = df_final.merge(atual_agrupado, on=['mes_ano', 'mes_num'], how='left').fillna(0)
    
    # Merge com o período anterior baseado no número do mês (Ex: Maio 2024 vs Maio 2023)
    df_final = df_final.merge(
        anterior_agrupado[['mes_num', 'quantity', 'total_price']], 
        on='mes_num', 
        how='left', 
        suffixes=('', '_prev')
    ).fillna(0)

    # Garantir que as colunas de quantidade são numéricas
    df_final['quantity'] = pd.to_numeric(df_final['quantity'])
    df_final['quantity_prev'] = pd.to_numeric(df_final['quantity_prev'])
    df_final['total_price'] = pd.to_numeric(df_final['total_price'])
    df_final['total_price_prev'] = pd.to_numeric(df_final['total_price_prev'])

    # 6. Calcular a média móvel de 3 meses e a variação percentual
    df_final['Média Móvel (3 meses)'] = df_final['quantity'].rolling(window=3, min_periods=1).mean().round(2)

    # Calcular a variação percentual de unidades vendidas
    def calc_variacao_unidades(row):
        if row['quantity_prev'] == 0:
            return 100.0 if row['quantity'] > 0 else 0.0
        return ((row['quantity'] - row['quantity_prev']) / row['quantity_prev']) * 100
    df_final['Variação (%)'] = df_final.apply(calc_variacao_unidades, axis=1).round(2)

    # Calcular o crescimento percentual da receita
    def calc_crescimento_receita(row):
        if row['total_price_prev'] == 0:
            return 100.0 if row['total_price'] > 0 else 0.0
        return ((row['total_price'] - row['total_price_prev']) / row['total_price_prev']) * 100
    df_final['Crescimento (%)'] = df_final.apply(calc_crescimento_receita, axis=1).round(2)

    # Calcular a tendência (seta)
    df_final['Tendência'] = df_final['Crescimento (%)'].apply(lambda x: '▲' if x > 0 else ('▼' if x < 0 else '—'))

    return df_final.rename(columns={'mes_ano': 'Mês', 'quantity': 'Total de Vendas', 'total_price': 'Receita'})[
        ['Mês', 'Receita', 'Crescimento (%)', 'Tendência', 'Total de Vendas', 'Média Móvel (3 meses)', 'Variação (%)']
    ]

def get_vendas_por_pagamento(start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
    """
    Gera um DataFrame agrupando as vendas por forma de pagamento no período selecionado.
    Retorna as colunas: Forma de Pagamento, Total Vendas, Faturamento e % do Total.
    """
    sales = carregar_tabela('sales')
    sales['sold_at'] = pd.to_datetime(sales['sold_at'])
    
    if start_date is not None: 
        sales = sales[sales['sold_at'] >= start_date] 
    if end_date is not None: 
        sales = sales[sales['sold_at'] <= end_date]
         
    if sales.empty:
        return pd.DataFrame(columns=['Forma de Pagamento', 'Total Vendas', 'Faturamento', 'Porcentagem do Total'])

    # Agrupamento por forma de pagamento (assumindo a coluna 'payment_method')
    df_agrupado = sales.groupby('payment_method').agg(
        total_vendas=('id', 'count'),
        faturamento=('total_amount', 'sum')
    ).reset_index()

    faturamento_total = df_agrupado['faturamento'].sum()
    
    if faturamento_total > 0:
        df_agrupado['pct_total'] = (df_agrupado['faturamento'] / faturamento_total) * 100
    else:
        df_agrupado['pct_total'] = 0.0

    df_final = df_agrupado.rename(columns={
        'payment_method': 'Forma de Pagamento',
        'total_vendas': 'Total Vendas',
        'faturamento': 'Faturamento',
        'pct_total': 'Porcentagem do Total'
    }).sort_values(by='Faturamento', ascending=False).reset_index(drop=True)
    
    df_final['Forma de Pagamento'] = df_final['Forma de Pagamento'].apply(get_payment_name)

    return df_final

def get_produtos_vendidos_juntos(start_date: datetime = None, end_date: datetime = None, top_n: int = 10) -> pd.DataFrame:
    """
    Detecta produtos que são vendidos juntos com maior frequência (Market Basket Analysis).
    Retorna um DataFrame com os pares de produtos e a contagem de ocorrências.
    """
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    products = carregar_tabela('products')

    # Filtro de período
    sales['sold_at'] = pd.to_datetime(sales['sold_at'])

    if start_date is not None: 
        sales = sales[sales['sold_at'] >= start_date] 
    if end_date is not None: 
        sales = sales[sales['sold_at'] <= end_date]

    if sales.empty:
        return pd.DataFrame(columns=['Produto A', 'Produto B', 'Frequência'])

    # Filtrar itens das vendas que estão no período selecionado
    df_vendas = pd.merge(sale_items[['sale_id', 'product_id']], sales[['id']], left_on='sale_id', right_on='id')

    # Self-join para encontrar pares de produtos na mesma transação
    # O critério 'product_id_a < product_id_b' serve para:
    # 1. Não parear o produto com ele mesmo (Ex: Café e Café)
    # 2. Não contar o mesmo par duas vezes em ordens diferentes (Ex: Café+Leite e Leite+Café)
    df_pares = pd.merge(
        df_vendas[['sale_id', 'product_id']], 
        df_vendas[['sale_id', 'product_id']], 
        on='sale_id', 
        suffixes=('_a', '_b')
    )
    df_pares = df_pares[df_pares['product_id_a'] < df_pares['product_id_b']]

    # Agrupar e contar frequências
    frequencia = df_pares.groupby(['product_id_a', 'product_id_b']).size().reset_index(name='Frequência')

    # Mapear os nomes dos produtos
    nomes_map = products.set_index('id')['name'].to_dict()
    frequencia['Produto A'] = frequencia['product_id_a'].map(nomes_map)
    frequencia['Produto B'] = frequencia['product_id_b'].map(nomes_map)
    frequencia['Porcentagem do Total'] = (frequencia['Frequência'] / frequencia['Frequência'].sum()) * 100
    
    return frequencia[['Produto A', 'Produto B', 'Frequência', 'Porcentagem do Total']].sort_values(by='Frequência', ascending=False).head(top_n).reset_index(drop=True)


def get_previsao_demanda_vendas(product_id: int = None, meses_previsao: int = 6) -> pd.DataFrame:
    """
    Calcula a taxa média de crescimento e prevê demanda (quantidade) e vendas (faturamento)
    para os próximos meses baseando-se no histórico.
    """
    sales = carregar_tabela('sales')
    sale_items = carregar_tabela('sale_items')
    
    # Unificar dados
    df = pd.merge(sale_items, sales, left_on='sale_id', right_on='id')
    df['sold_at'] = pd.to_datetime(df['sold_at'])
    
    # Filtro opcional por produto
    if product_id:
        df = df[df['product_id'] == product_id]
        
    if df.empty:
        return pd.DataFrame(columns=['Mês', 'Previsão de Demanda', 'Previsão de Vendas'])
        
    # Agrupar por mês para calcular as taxas de crescimento
    df_mensal = df.groupby(df['sold_at'].dt.to_period('M')).agg({
        'quantity': 'sum',
        'total_price': 'sum'
    }).reset_index()
    
    df_mensal['mes_referencia'] = df_mensal['sold_at'].dt.to_timestamp()
    
    if len(df_mensal) < 2:
        return pd.DataFrame(columns=['Mês', 'Previsão de Demanda', 'Previsão de Vendas'])

    # 1. Calcular Taxas Médias de Crescimento
    # pct_change calcula (atual - anterior) / anterior
    df_mensal['taxa_qty'] = df_mensal['quantity'].pct_change()
    df_mensal['taxa_rev'] = df_mensal['total_price'].pct_change()
    
    taxa_media_qty = df_mensal['taxa_qty'].mean()
    taxa_media_rev = df_mensal['taxa_rev'].mean()
    
    # 2. Gerar Previsões usando a fórmula: ultimo * (1 + taxa)^n
    ultimo_mes_qty = df_mensal['quantity'].iloc[-1]
    ultimo_mes_rev = df_mensal['total_price'].iloc[-1]
    ultima_data = df_mensal['mes_referencia'].iloc[-1]
    
    previsoes = []
    for i in range(1, meses_previsao + 1):
        data_futura = (ultima_data + relativedelta(months=i)).strftime("%Y-%m")
        pred_qty = ultimo_mes_qty * ((1 + taxa_media_qty) ** i)
        pred_rev = ultimo_mes_rev * ((1 + taxa_media_rev) ** i)
        
        previsoes.append({
            'Mês': data_futura,
            'Previsão de Demanda': round(max(0, pred_qty), 2),
            'Previsão de Vendas': round(max(0, pred_rev), 2)
        })
        
    return pd.DataFrame(previsoes)
