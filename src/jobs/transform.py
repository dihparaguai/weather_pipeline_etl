import os
import json
import pandas as pd
from typing import List
from loguru import logger
import pyarrow


datetime_columns_to_cast = ['dt', 'sys_sunrise', 'sys_sunset']

def create_dataframe(bronze_files_path: str = './data/bronze') -> pd.DataFrame:
    """
    Lê o JSON do caminho fornecido em disco e converte em um DataFrame.
    """
    json_files_list = [f for f in os.listdir(bronze_files_path) if f.endswith(".json")]

    df_list = []

    for file in json_files_list:
        path_name = os.path.join(bronze_files_path, file)

        logger.info(f"Lendo e serializando dados do JSON: {path_name}")
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

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Substitui espaços e pontos (.) por underscores (_) em todos os nomes de colunas.
    """
    logger.info("Aplicando Regex para padronização das colunas no DataFrame.")
    # df.columns renomeia todas as colunas de uma vez quando é atribuído uma lista de mesmo tamanho
    df.columns = df.columns.str.replace(r'[\s\.]', '_', regex=True)
    logger.debug(f"Colunas renomeadas com sucesso.")
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

def save_to_silver_parquet(df: pd.DataFrame, bronze_file_path: str) -> str:
    """
    Exporta o DataFrame transformado para um arquivo Parquet na camada Silver.
    """
    os.makedirs("data/silver", exist_ok=True)

    # Pega o nome do arquivo base, troca a extensão e junta com o caminho da pasta
    silver_path = os.path.join("data/silver", bronze_file_path.replace('.json', '.parquet').split('/')[-1])
    
    logger.info(f"Salvando dados processados na camada Silver: {silver_path}")
    df.to_parquet(silver_path, engine='pyarrow', index=False)
    logger.info(f"Dados salvos com sucesso na camada Silver.")
    return silver_path

def run_transform(bronze_file_path: str) -> pd.DataFrame:
    """
    Executa as  funções de transformação em sequência.
    """
    logger.info(f"=== Iniciando fluxo completo de Transformação para: {bronze_file_path} ===")
    
    df = create_dataframe(bronze_file_path)
    df = normalize_column(df, column_name='weather')
    df = rename_columns(df)
    df = cast_datetime_columns(df, datetime_columns=datetime_columns_to_cast)
    silver_path = save_to_silver_parquet(df, bronze_file_path)
    
    logger.info(f"=== Transformação Executada com Sucesso! Parquet gerado: {silver_path} ===")
    return silver_path
