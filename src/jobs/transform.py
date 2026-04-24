import os
import json
import pandas as pd
from typing import List
from loguru import logger
import pyarrow
from datetime import date, datetime


datetime_columns_to_cast = ['datetime', 'nascer_do_sol', 'por_do_sol']

columns_to_drop = ['base', 'visibility', 'timezone', 'id', 'main.pressure', 'main.sea_level', 'main.grnd_level', 'wind.speed', 'wind.deg', 'clouds.all']

columns_to_rename = {'dt': 'datetime', 'name': 'cidade', 'coord.lon': 'longitude', 'coord.lat': 'latitude', 'main.temp': 'temperatura', 'main.feels_like': 'sensacao_termica', 'main.temp_min': 'temperatura_minima', 'main.temp_max': 'temperatura_maxima', 'main.humidity': 'umidade', 'sys.country': 'pais', 'sys.sunrise': 'nascer_do_sol', 'sys.sunset': 'por_do_sol'}


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

def drop_columns(df: pd.DataFrame, columns_to_drop: List[str]) -> pd.DataFrame:
    """
    Remove as colunas desnecessárias do DataFrame.
    """
    logger.info(f"Removendo as colunas...")
    
    df = df.drop(columns=columns_to_drop)
    
    logger.info(f"Colunas removidas com sucesso!")
    return df

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
        return df
    
    except Exception as e:
        logger.error(f"Erro na explosão JSON do array '{column_name}': {e}")
        raise

def cast_datetime_columns(df: pd.DataFrame, datetime_columns: List[str], timezone: str = 'America/Sao_Paulo') -> pd.DataFrame:
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

def save_to_silver_parquet(df: pd.DataFrame, silver_folder_path: str, target_date: str) -> str:
    """
    Exporta o DataFrame transformado para um arquivo Parquet na camada Silver.
    """
    logger.info(f"Salvando dados processados na camada Silver: {file_path}...")
    
    os.makedirs(silver_folder_path, exist_ok=True)

    file_name = f'{target_date}.parquet'
    file_path = os.path.join(silver_folder_path, file_name)
    
    df.to_parquet(file_path, engine='pyarrow', index=False)
    
    logger.info(f"Dados salvos com sucesso na camada Silver!")
    return file_path

def get_max_date_from_silver(silver_folder_path: str) -> datetime.date:
    """
    Inspeciona a camada Silver e busca a maior data já processada.
    """
    # Busca a data da última transformação em Silver
    logger.info("Buscando a data da última transformação em Silver...")
    if not os.path.exists(silver_folder_path):
        logger.warning(f"O diretório {silver_folder_path} não existe.")
        return None
    
    # Lista os arquivos Parquet na camada Silver
    parquet_list = [p for p in os.listdir(silver_folder_path) if p.endswith('.parquet')]
    if not parquet_list:
        logger.warning(f"Nenhum arquivo Parquet foi localizado na camada Silver.")
        return None

    # Extrai a data de cada arquivo e armazena em uma lista
    dates = []
    for p in parquet_list:
        date_str = p.split('.')[0]
        try:
            parsed_date = datetime.strptime(date_str, '%Y%m%d').date()
            dates.append(parsed_date)
            logger.debug(f"Data {parsed_date} adicionada à lista de datas.")
        except ValueError:
            logger.error(f"Erro ao converter a data {date_str}.")
            pass

    # Verifica se a lista de datas não está vazia
    if not dates:
        logger.warning(f"Nenhuma data foi encontrada na camada Silver.")
        return None
        
    # Busca a data máxima na lista de datas
    max_date = max(dates)
    logger.info(f"Última data encontrada em Silver com sucesso: {max_date} !!!")
    return max_date

def filter_incremental_bronze_partitions(bronze_folder_path: str, max_date: datetime.date) -> list:
    """
    Inspeciona a camada Bronze para identificar quais partições (pastas) não foram processadas.
    """
    # Busca as partições (pastas) na camada Bronze
    logger.info("Filtrando as novas partições (pastas) disponíveis em Bronze...")
    if not os.path.exists(bronze_folder_path):
        logger.warning(f"O diretório {bronze_folder_path} não existe.")
        return []

    # Lista as partições (pastas) na camada Bronze (e verifica se é um diretório)
    folder_list = [f for f in os.listdir(bronze_folder_path) if os.path.isdir(os.path.join(bronze_folder_path, f))] 
    if not folder_list:
        logger.info("Nenhuma partição encontrada na camada Bronze.")
        return []

    # Se não houver data máxima no banco de dados, retorna todas as partições (pastas)
    if max_date is None:
        logger.info("Não há dados na camada Silver.")
        return [os.path.join(bronze_folder_path, f) for f in folder_list]

    # Verifica se a data de cada partição (pasta) é maior que a data máxima encontrada
    valid_folders = []
    for f in folder_list:
        try:
            folder_date = datetime.strptime(f, '%Y%m%d').date()
            if folder_date > max_date:
                valid_folders.append(os.path.join(bronze_folder_path, f))
                logger.debug(f"Partição {f} adicionada à lista de partições a serem processadas.")
        except ValueError:
            logger.error(f"Erro ao converter a data {f}.")
            pass
            
    logger.info("Filtro de partições (pastas) novas concluído com sucesso!!!")
    return sorted(valid_folders)

def run_transform(bronze_file_path: str, silver_folder_path: str) -> pd.DataFrame:
    """
    Executa as funções de transformação em sequência.
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
