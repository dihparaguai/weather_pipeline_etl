import os
import json
import pyarrow
import pandas as pd
from loguru import logger
from datetime import date, datetime
from src.modules.azure_datalake_service import AzureDatalakeService
from src.modules import file_incremental_filtering as fif


datetime_columns_to_cast = ['datetime', 'nascer_do_sol', 'por_do_sol']

columns_to_rename_and_keep = {'dt': 'datetime', 'name': 'cidade', 'coord.lon': 'longitude', 'coord.lat': 'latitude', 'main.temp': 'temperatura', 'main.feels_like': 'sensacao_termica', 'main.temp_min': 'temperatura_minima', 'main.temp_max': 'temperatura_maxima', 'main.humidity': 'umidade', 'sys.country': 'pais', 'sys.sunrise': 'nascer_do_sol', 'sys.sunset': 'por_do_sol'}


def create_dataframe(bronze_files_path: str) -> pd.DataFrame:
    """
    Lê o JSON do caminho fornecido em disco e converte em um DataFrame.
    """
    logger.info(f"Lendo e serializando dados da pasta: {bronze_files_path}...")
    
    json_files_list = [f for f in os.listdir(bronze_files_path) if f.endswith(".json")]

    df_list = []

    for file in json_files_list:
        path_name = os.path.join(bronze_files_path, file)

        logger.debug(f"Lendo e serializando dados do JSON: {path_name}.")
        try:
            # Lê o arquivo JSON
            with open(path_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Normaliza o JSON em um DataFrame
            df = pd.json_normalize(data)
            df_list.append(df)
            logger.debug(f"DataFrame de {file} criado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao criar o DataFrame: {e}")
            raise
    
    # Concatena todos os DataFrames em um só, reorganiza os indices
    logger.info("Concatenando todos os DataFrames em um só.")
    df_concat = pd.concat(df_list, ignore_index=True)
    
    logger.info(f"DataFrame concatenado criado com sucesso!")
    return df_concat

def keep_columns(df: pd.DataFrame, columns_to_keep: list) -> pd.DataFrame:
    """
    Remove as colunas desnecessárias do DataFrame.
    """
    logger.info(f"Mantendo apenas as colunas necessárias...")
    
    # Verifica se as colunas existem no DataFrame
    columns_exists = [col for col in columns_to_keep if col in df.columns]
    
    # Filtra o DataFrame mantendo apenas as colunas que existem
    if columns_exists:
        df_filtered = df.filter(items=columns_to_keep)
        
        # Colunas que não foram encontradas
        columns_not_found = [col for col in columns_to_keep if col not in df.columns]
        if columns_not_found:
            logger.warning(f"Colunas não encontradas no DataFrame: {columns_not_found}")
            
        logger.info(f"Colunas mantidas com sucesso!")
        return df_filtered
    else:
        logger.error(f"Nenhuma coluna para manter foi encontrada no DataFrame.")
        return pd.DataFrame()

def rename_columns(df: pd.DataFrame, columns_to_rename: dict) -> pd.DataFrame:
    """
    Renomeia as colunas para melhor legibilidade.
    """
    logger.info("Renomeando as colunas...")
    
    df = df.rename(columns=columns_to_rename)
    
    logger.info(f"Colunas renomeadas com sucesso!")
    return df

def normalize_column(df: pd.DataFrame, column_name: str = 'weather') -> pd.DataFrame:
    """
    Explode a coluna recebida (lista de dicionários) em colunas separadas.
    """
    logger.info(f"Explodindo a coluna '{column_name}'...")
    
    try:
        if column_name not in df.columns:
            logger.warning(f"Coluna '{column_name}' não encontrada no DataFrame.")
            return df

        # Retira o primeiro item da lista interna de dicts e joga num DataFrame normalizado
        df_column_list_normalized = pd.json_normalize(df[column_name].apply(lambda x: x[0]))

        # Renomeia as colunas adicionando o prefixo 'weather_'
        df_column_list_renamed = df_column_list_normalized.add_prefix(f'{column_name}_')
        
        # Junta na tabela matriz horizontalmente (axis=1) e apaga a que continha a array
        df = pd.concat([df, df_column_list_renamed], axis=1)
        df = df.drop(columns=[column_name], errors='ignore')
        
        logger.info(f"Colunas de {column_name} explodidas com sucesso!")
        logger.debug(f"Colunas explodidas: {df_column_list_renamed.columns.tolist()}")
        return df
    
    except Exception as e:
        logger.error(f"Erro na explosão JSON do array '{column_name}': {e}")
        raise

def cast_datetime_columns(df: pd.DataFrame, datetime_columns: list, timezone: str = 'America/Sao_Paulo') -> pd.DataFrame:
    """
    Converte uma lista de colunas (unix timestamp/segundos) para datetime no fuso horário local.
    """
    logger.info(f"Convertendo colunas de unix timestamp para datetime...")
    
    for col in datetime_columns:
        if col in df.columns:
            logger.debug(f"Convertendo a coluna: {col}")
            # Converte de segundos (timestamp unit='s') para UTC e ajusta para o fuso horário
            df[col] = pd.to_datetime(df[col], unit='s', utc=True).dt.tz_convert(timezone)
        else:
            logger.warning(f"Coluna {col} não encontrada no DataFrame.")
    
    logger.info(f"Colunas de unix timestamp convertidas para datetime com sucesso!")
    return df

def save_to_silver_parquet(df: pd.DataFrame, silver_folder_path: str, target_date: str):
    """
    Exporta o DataFrame transformado para um arquivo Parquet na camada Silver.
    """
    logger.info(f"Salvando dados processados na camada Silver...")
    
    os.makedirs(silver_folder_path, exist_ok=True)

    file_name = f'{target_date}.parquet'
    file_path = os.path.join(silver_folder_path, file_name)
    
    df.to_parquet(file_path, engine='pyarrow', index=False)
    
    logger.info(f"Dados salvos com sucesso na camada Silver!")

def upload_silver_files_to_datalake(silver_folder_path: str):
    """
    Faz o upload dos arquivos para camada Silver do Azure Data Lake Storage.
    """
    logger.info("Iniciando o upload dos arquivos para a camada Silver do Azure Data Lake Storage...")

    container_name='weather'
    layer_folder='silver'

    az_dl = AzureDatalakeService()

    data_lake_partition_list = az_dl.get_partitions_from_layer_folder(
        container_name=container_name,
        layer_folder=layer_folder
    )

    max_date_from_datalake_partitions = fif.get_max_date_from_datalake_partitions(data_lake_partition_list)
    parquet_file_path_list = fif.filter_incremental_silver_files(silver_folder_path, max_date_from_datalake_partitions)

    cloud_and_local_file_path_name_dict = {}
    for parquet_file_path in parquet_file_path_list:
        parquet_file_name = parquet_file_path.split('/')[-1] # from "./silver/20221020.parquet" to "20221020.parquet"
        partition_date_file = parquet_file_name.split('.')[0] # from "20221020.parquet" to "20221020"
        partition_date_file_formated = f"{partition_date_file[:4]}/{partition_date_file[4:6]}/{partition_date_file[6:]}" # from "20221020" to "2022/10/20"
        cloud_and_local_file_path_name_dict[f"{partition_date_file_formated}/{parquet_file_name}"] = parquet_file_path

    az_dl.upload_file_to_datalake(
        container_name=container_name,
        layer_folder=layer_folder,
        cloud_and_local_file_path_name_dict=cloud_and_local_file_path_name_dict
    )
    logger.info("Upload realizado com sucesso!!!")

def run_transform(bronze_folder_path: str, silver_folder_path: str) -> pd.DataFrame:
    """
    Executa as funções de transformação em sequência.
    """
    logger.info(f"=== Iniciando etapa de Transformação dos dados da API Weather... ===")

    max_date_silver = fif.get_max_date_from_silver(silver_folder_path)
    valid_partitions = fif.filter_incremental_bronze_partitions(bronze_folder_path, max_date_silver)

    for partition_path in valid_partitions:
        target_date = partition_path.split('/')[-1]
        df = create_dataframe(partition_path)
        df = normalize_column(df, column_name='weather')
        df = keep_columns(df, columns_to_keep=list(columns_to_rename_and_keep.keys()))
        df = rename_columns(df, columns_to_rename=columns_to_rename_and_keep)
        df = cast_datetime_columns(df, datetime_columns=datetime_columns_to_cast)
        save_to_silver_parquet(df, silver_folder_path=silver_folder_path, target_date=target_date)

    upload_silver_files_to_datalake(silver_folder_path=silver_folder_path)
    
    logger.info(f"=== Etapa de Transformação dos dados da API Weather executada com sucesso!!! ===")
