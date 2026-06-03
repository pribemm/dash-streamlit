import pandas as pd
from utils.get_data import carregar_tabela

# df_suppliers = carregar_tabela("suppliers")
# df_ingredients = carregar_tabela("ingredients")
# df_stock = carregar_tabela("stock_movements")
# df_products = carregar_tabela("products")
df_sales = carregar_tabela("sales")
# df_recipes = carregar_tabela("recipes")
# df_menus = carregar_tabela("menus")
# df_sales = carregar_tabela("sales")

# print(df_ingredients.current_stock.describe())

def consumo_insumo(df, periodo='mes', coluna_data='received_at', tipo_agrupamento='name'):
    """
    Filtra os insumos por período e conta a quantidade acumulada por tipo.
    
    Parâmetros:
    - df: DataFrame do Pandas contendo a tabela de estoque.
    - periodo: 'dia', 'mes' ou 'ano' para o agrupamento temporal.
    - coluna_data: A coluna de data usada para o filtro (ex: 'received_at').
    - tipo_agrupamento: 'name' para agrupar por ingrediente ou 'category_id' por categoria.
    """
    df_copy = df.copy()
    df_copy[coluna_data] = pd.to_datetime(df_copy[coluna_data])
    
    df_copy['current_stock'] = pd.to_numeric(df_copy['current_stock'], errors='coerce').fillna(0)
    
    if periodo == 'dia':
        df_copy['periodo_ref'] = df_copy[coluna_data].dt.to_period('D')
    elif periodo == 'mes':
        df_copy['periodo_ref'] = df_copy[coluna_data].dt.to_period('M')
    elif periodo == 'ano':
        df_copy['periodo_ref'] = df_copy[coluna_data].dt.to_period('Y')
    else:
        raise ValueError("Período inválido. Escolha entre 'dia', 'mes' ou 'ano'.")
        
    # 4. Agrupar por Período e pelo Tipo de Insumo, somando o estoque atual
    resultado = df_copy.groupby(['periodo_ref', tipo_agrupamento])['current_stock'].sum().reset_index()
    
    # Renomear colunas para ficar mais claro
    resultado.columns = ['Periodo', 'Insumo', 'Quantidade_Total']
    
    return resultado

print(df_sales)