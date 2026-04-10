import os
import json
import pandas as pd
from typing import List
from loguru import logger
import pyarrow
from datetime import date


datetime_columns_to_cast = ['datetime', 'nascer_do_sol', 'por_do_sol']

columns_to_drop = ['base', 'visibility', 'timezone', 'id', 'main.pressure', 'main.sea_level', 'main.grnd_level', 'wind.speed', 'wind.deg', 'clouds.all']

columns_to_rename = {'dt': 'datetime', 'name': 'cidade', 'coord.lon': 'longitude', 'coord.lat': 'latitude', 'main.temp': 'temperatura', 'main.feels_like': 'sensacao_termica', 'main.temp_min': 'temperatura_minima', 'main.temp_max': 'temperatura_maxima', 'main.humidity': 'umidade', 'sys.country': 'pais', 'sys.sunrise': 'nascer_do_sol', 'sys.sunset': 'por_do_sol'}


def create_dataframe(bronze_files_path: str) -> pd.DataFrame:
    """
    Lê o JSON do caminho fornecido em disco e converte em um DataFrame.
    """
    json_files_list = [f for f in os.listdir(bronze_files_path) if f.endswith(".json")]

    df_list = []

    logger.info(f"Lendo e serializando dados da pasta: {bronze_files_path}")
    for file in json_files_list:
        path_name = os.path.join(bronze_files_path, file)

        logger.debug(f"Lendo e serializando dados do JSON: {path_name}")
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
    
    logger.info(f"DataFrame criado com sucesso.")
    return df_concat

def drop_columns(df: pd.DataFrame, columns_to_drop: List[str]) -> pd.DataFrame:
    """
    Remove as colunas desnecessárias do DataFrame.
    """
    logger.info(f"Removendo as colunas.")
    df = df.drop(columns=columns_to_drop)
    logger.info(f"Colunas removidas com sucesso.")
    return df

def rename_columns(df: pd.DataFrame, columns_to_rename: dict) -> pd.DataFrame:
    """
    Renomeia as colunas para melhor legibilidade.
    """
    logger.info("Renomeando as colunas.")
    df = df.rename(columns=columns_to_rename)
    logger.info(f"Colunas renomeadas com sucesso.")
    return df

def normalize_column(df: pd.DataFrame, column_name: str = 'weather') -> pd.DataFrame:
    """
    Normaliza a coluna recebida, que é uma lista de dicionários
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
        
        logger.info(f"Colunas de {column_name} normalizadas com sucesso.")
        return df
    except Exception as e:
        logger.error(f"Erro na normalização JSON do array '{column_name}': {e}")
        raise

def cast_datetime_columns(df: pd.DataFrame, datetime_columns: List[str], timezone: str = 'America/Sao_Paulo') -> pd.DataFrame:
    """
    Converte uma lista de colunas (unix timestamp/segundos) para datetime no fuso horário local.
    """
    logger.info(f"Ajustando a coluna em segundos (UTC) para a TimeZone: {timezone}.")
    for col in datetime_columns:
        if col in df.columns:
            logger.debug(f"Convertendo a coluna: {col}")
            # Converte de segundos (timestamp unit='s') para UTC e ajusta para o fuso horário
            df[col] = pd.to_datetime(df[col], unit='s', utc=True).dt.tz_convert(timezone)
        else:
            logger.warning(f"Coluna '{col}' mapeada para formatação de Data/Hora não existe no DF.")
    logger.info(f"Colunas de Data/Hora convertidas com sucesso.")
    return df

def save_to_silver_parquet(df: pd.DataFrame, silver_folder_path: str, target_date: str) -> str:
    """
    Exporta o DataFrame transformado para um arquivo Parquet na camada Silver.
    """

    os.makedirs(silver_folder_path, exist_ok=True)

    file_name = f'{target_date}.parquet'
    file_path = os.path.join(silver_folder_path, file_name)
    
    logger.info(f"Salvando dados processados na camada Silver: {file_path}")
    df.to_parquet(file_path, engine='pyarrow', index=False)
    logger.info(f"Dados salvos com sucesso na camada Silver.")
    return file_path

def run_transform(bronze_file_path: str, silver_folder_path: str = './data/silver') -> pd.DataFrame:
    """
    Executa as  funções de transformação em sequência.
    """
    logger.info(f"=== Iniciando transformação dos dados... ===")

    target_date = bronze_file_path.split('/')[-1]
    
    df = create_dataframe(bronze_file_path)
    df = normalize_column(df, column_name='weather')
    df = drop_columns(df, columns_to_drop=columns_to_drop)
    df = rename_columns(df, columns_to_rename=columns_to_rename)
    df = cast_datetime_columns(df, datetime_columns=datetime_columns_to_cast)
    silver_file_path = save_to_silver_parquet(df, silver_folder_path=silver_folder_path, target_date=target_date)
    
    logger.info(f"=== Transformação Executada com Sucesso! ===")
    return silver_file_path
