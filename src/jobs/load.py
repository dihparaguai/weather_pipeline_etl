import os
import pandas as pd
from loguru import logger
from src.modules.sqlalchemy_engine import SQLAlchemyEngine
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
        logger.error(f">> A tabela '{table_name}' não foi encontrada, será criada automaticamente.")
        return None
        
    # Verifica se a coluna existe usando o Inspetor
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    if column_name not in columns:
        logger.error(f">> A coluna '{column_name}' não foi encontrada na tabela '{table_name}'")
        logger.debug(f"Colunas encontradas na tabela '{table_name}': {columns}")
        return None
        
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

def filter_incremental_file(silver_folder_path: str, max_date: datetime.date) -> list:
    """
    Filtra os arquivos na camada Silver, retornando apenas os paths dos arquivos a serem incrementados no Banco.
    """
    logger.info("Buscando arquivos Parquet na camada Silver para incrementar...")
    parquet_file_path_list = [p for p in os.listdir(silver_folder_path) if p.endswith('.parquet')]

    # Se não houver arquivos na camada Silver, retorna uma lista vazia
    if not parquet_file_path_list:
        logger.info("Nenhum arquivo Parquet foi localizado na camada Silver.")
        return []

    # Se não houver data máxima no banco de dados, retorna todos os arquivos
    if max_date is None:
        logger.info("Não há dados no banco de dados. Retornando todos os arquivos.")
        return [os.path.join(silver_folder_path, p) for p in parquet_file_path_list]
    
    # Filtra os arquivos que são mais recentes que a data máxima no banco de dados
    parquet_file_path_list_to_increment = []
    for p in parquet_file_path_list:
        # Extrai a string ('20260412') sem ".parquet"
        file_date_str = p.split('.')[0] 
        
        file_date = datetime.strptime(file_date_str, '%Y%m%d').date()
        
        if file_date > max_date:
            parquet_file_path_list_to_increment.append(os.path.join(silver_folder_path, p))
            logger.debug(f"Arquivo {p} adicionado à lista de incremento.")
            
    logger.info(f"{len(parquet_file_path_list_to_increment)} arquivo(s) para incrementar.")
    return parquet_file_path_list_to_increment

def concat_parquet_files(parquet_file_path_list: list) -> pd.DataFrame:
    """
    Concatena os arquivos Parquet em um único DataFrame.
    """
    logger.info("Concatenando arquivos Parquet em um único DataFrame...")
    
    # Se não houver arquivos na camada Silver, retorna None
    if not parquet_file_path_list:
        logger.info("Nenhum arquivo Parquet foi localizado na camada Silver.")
        return None
    
    # Cria uma lista de DataFrames e concatena em um único DataFrame
    df_list = []
    for p in parquet_file_path_list:
        df_list.append(pd.read_parquet(p, engine='pyarrow'))
    
    logger.info(f"DataFrame concatenado com {len(df_list)} arquivos.")
    return pd.concat(df_list, ignore_index=True)

def save_to_db(db_engine, df: pd.DataFrame, table_name: str):
    """
    Adiciona os dados do DataFrame no banco de dados.
    """
    logger.info(f"Adicionando os dados do DataFrame na tabela '{table_name}'...")

    if df is None:
        logger.info("Nenhum dado para adicionar no banco de dados.")
        return

    try :
        # Usa 'append' do Pandas para apenas adicionar sem apagar os dias anteriores
        df.to_sql(name=table_name, con=db_engine, if_exists='append', index=False)
        logger.info("Dados adicionados com sucesso!!!")
    except Exception as e:
        logger.error(f">> Falha ao adicionar dados no banco de dados: {e}")
        raise

def run_load(silver_folder_path: str, table_name: str = 'tb_weather_data'):
    """
    Executa as funções de carga em sequência.
    """
    logger.info(f"=== Iniciando a etapa de Carga no PostgreSQL... ===")
    db_connection = SQLAlchemyEngine()
    db_engine = db_connection.engine

    max_date_db = get_max_date_from_db(db_engine, table_name, column_name='datetime')
    parquet_file_path_list = filter_incremental_file(silver_folder_path, max_date_db)
    df = concat_parquet_files(parquet_file_path_list)
    save_to_db(db_engine, df, table_name)

    db_engine.dispose()
    logger.info(f"=== Etapa de Carga no PostgreSQL executada com sucesso!!! ===")