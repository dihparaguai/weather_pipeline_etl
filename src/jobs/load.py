import pandas as pd
from loguru import logger
from src.modules.postgres_utils import PostgresUtils

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
