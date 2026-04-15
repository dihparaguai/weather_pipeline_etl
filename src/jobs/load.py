import os
import pandas as pd
from loguru import logger
from src.modules.postgres_utils import PostgresUtils
from sqlalchemy import text, inspect
from datetime import date, datetime

def get_max_date_from_db(db_engine, table_name: str, column_name: str) -> datetime.date:
    """
    Busca a data mais recente armazenada na tabela alvo.
    """
    logger.info("Buscando a data mais recente na tabela alvo...")
    # Inspeciona o schema do banco de dados
    inspector = inspect(db_engine)
    
    # Verifica se a tabela existe usando o Inspetor
    if not inspector.has_table(table_name):
        logger.error(f"A tabela '{table_name}' não foi encontrada!")
        raise ValueError(f"A tabela '{table_name}' não foi encontrada!")
        
    # Verifica se a coluna existe usando o Inspetor
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    logger.debug(f"Colunas encontradas na tabela '{table_name}': {columns}")
    if column_name not in columns:
        logger.error(f"A coluna '{column_name}' não foi encontrada na tabela '{table_name}'!")
        raise ValueError(f"A tabela '{table_name}' existe, mas a coluna'{column_name}' não foi encontrada!")
        
    # Executa a extração da data máxima
    query_str = f"SELECT MAX({column_name}) AS max_date FROM {table_name}"
    max_date_db = pd.read_sql(text(query_str), con=db_engine)
    max_date_df = max_date_db['max_date'].iloc[0]
    
    # Verifica se a data máxima é nula
    if pd.notnull(max_date_df):
        max_date = pd.to_datetime(max_date_df).date()
        logger.info(f"Data máxima encontrada: {max_date} {type(max_date)}")
        return max_date
    else:
        logger.info(f"A coluna '{column_name}' da tabela '{table_name}' está vazia.")
        return None

def run_load(silver_file_path: str, table_name: str = 'tb_weather_data'):
    """
    Lê o Parquet estruturado da camada Silver e persiste na camada Gold/DWH.
    """
    logger.info(f"=== Iniciando a etapa de Carga no PostgreSQL o arquivo: {silver_file_path} ===")
    
    try:
        logger.info(f"Carregando o DataFrame a partir de: {silver_file_path}")
        # Transforma o arquivo Parquet em um DataFrame
        df = pd.read_parquet(silver_file_path, engine='pyarrow')

        # Abre a porta com o banco via SQLAlchemy usando as credenciais do .env
        db_connection = PostgresUtils()
        
        logger.info(f"Inserindo {len(df)} registros diretamente na tabela postgres '{table_name}'")
        # Injeta o DataFrame no PostegreSQL. Usa 'append' para apenas adicionar sem apagar os dias anteriores
        df.to_sql(name=table_name, con=db_connection.engine, if_exists='append', index=False)
        
        logger.info("=== Carga finalizada com sucesso! Dados seguros no banco. ===")
        
    except Exception as e:
        logger.error(f"Falha durante a injeção de dados no PostgreSQL: {e}")
        raise
