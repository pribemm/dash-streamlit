import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

_database_url = os.getenv("DATABASE_URL")
if not _database_url:
    raise EnvironmentError("Variável DATABASE_URL não encontrada. Configure o arquivo .env")

engine = create_engine(_database_url)


def carregar_tabela(nome_tabela: str) -> pd.DataFrame:
    """Carrega uma tabela do banco de dados para um DataFrame do Pandas."""
    query = f"SELECT * FROM public.{nome_tabela};"
    return pd.read_sql(query, engine)