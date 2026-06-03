import pandas as pd
from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/projeto_es")

# def carregar_tabela(nome_tabela):
#     query = f"SELECT * FROM {nome_tabela};"
#     return pd.read_sql(query, engine)

conn = psycopg2.connect(
    host="localhost",
    database="projeto_es",
    user="postgres",
    password="postgres",
    port="5432"
)

df = pd.read_sql("SELECT * FROM public.sales", conn)

print(df.head())

# print('----'*30)
# print(f'Tamanho da tabela sales: {len(carregar_tabela("sales"))}')

# print('---'*15 + 'Consultando diretamente com SQL' + '---'*15)
# print(pd.read_sql("SELECT * FROM information_schema.tables WHERE table_name = 'sales';", engine))