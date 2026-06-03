import pandas as pd
import psycopg2

conexao = psycopg2.connect(
    host="localhost",
    database="db_marmitaria",
    user="postgres", 
    password="postgres",
    port="5432"
)

query = "SELECT * FROM ingredients;"

df = pd.read_sql_query(query, conexao)
print(df)

conexao.close()