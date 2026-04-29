import os
from loguru import logger
from datetime import datetime, date

def get_max_date_from_bronze(bronze_folder_path: str) -> datetime.date:
    """
    Inspeciona a camada Bronze e busca a maior data já processada.
    """
    # Busca a data da última ingestão em Bronze
    logger.info("Buscando a data da última ingestão em Bronze...")
    if not os.path.exists(bronze_folder_path):
        logger.warning(f"O diretório {bronze_folder_path} não existe.")
        return None
    
    # Lista as partições (pastas) na camada Bronze
    folder_list = [f for f in os.listdir(bronze_folder_path) if os.path.isdir(os.path.join(bronze_folder_path, f))] 
    if not folder_list:
        logger.warning(f"Nenhuma partição encontrada na camada Bronze.")
        return None

    # Extrai a data de cada partição (pasta) e armazena em uma lista
    dates = []
    for f in folder_list:
        try:
            parsed_date = datetime.strptime(f, '%Y%m%d').date()
            dates.append(parsed_date)
            logger.debug(f"Data {parsed_date} adicionada à lista de datas.")
        except ValueError:
            logger.error(f"Erro ao converter a data {f}.")
            pass

    # Verifica se a lista de datas não está vazia
    if not dates:
        logger.warning(f"Nenhuma data foi encontrada na camada Bronze.")
        return None
        
    # Busca a data máxima na lista de datas
    max_date = max(dates)
    logger.info(f"Última data encontrada em Bronze com sucesso!!!")
    logger.debug(f"Última data encontrada em Bronze: {max_date}")
    return max_date

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
    logger.info(f"Última data encontrada em Silver com sucesso!!!")
    logger.debug(f"Última data encontrada em Silver: {max_date}")
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

def filter_incremental_silver_files(silver_folder_path: str, max_date: datetime.date) -> list:
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
