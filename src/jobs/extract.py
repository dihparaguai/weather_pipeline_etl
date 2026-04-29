import json
import os
from datetime import datetime, date
from loguru import logger
from src.modules.weather_api import download_weather_data
from src.modules.azure_datalake_service import AzureDatalakeService
from src.modules import file_incremental_filtering as fif

def upload_bronze_files_to_datalake(partition_folder_list: list):
    """
    Faz o upload dos arquivos para camada Bronze do Azure Data Lake Storage.
    """
    logger.info("Iniciando o upload dos arquivos para a camada Bronze do Azure Data Lake Storage...")
    azure_datalake_service = AzureDatalakeService()
    cloud_and_local_file_path_name_dict = {}

    for partition_folder in partition_folder_list:
        file_list = [file_name for file_name in os.listdir(partition_folder) if file_name.endswith('.json')]  
        logger.debug(f"Encontrados {len(file_list)} arquivos na partição {partition_folder}.")
        
        if not file_list:
            logger.info(f"Nenhum arquivo encontrado na partição {partition_folder}.")
            continue # Pula para a próxima partição
        
        for file_name in file_list:
            local_file_path_name = os.path.join(partition_folder, file_name)
            partition_date_folder = partition_folder.split('/')[-1]
            partition_date_folder_formated = f"{partition_date_folder[:4]}/{partition_date_folder[4:6]}/{partition_date_folder[6:]}"
            cloud_and_local_file_path_name_dict[f"{partition_date_folder_formated}/{file_name}"] = local_file_path_name

    azure_datalake_service.upload_file_to_datalake(
        container_name='weather',
        layer_folder='bronze',
        cloud_and_local_file_path_name_dict=cloud_and_local_file_path_name_dict
    )

def run_extract(cities_names_list: list, bronze_folder_path: str, target_date: datetime.date = None) -> str:
    """
    Chama a API e salva os dados brutos na camada Bronze.
    """
    logger.info("Iniciando a extração dos dados...")

    if target_date is None:
        target_date = date.today()
    
    # Cria subpasta com a data de extração
    folder_bronze_path_partitioned = os.path.join(bronze_folder_path, target_date.strftime('%Y%m%d'))
    
    os.makedirs(folder_bronze_path_partitioned, exist_ok=True)

    for city_name in cities_names_list:
        try:
            logger.debug(f"Chamando a função download_weather_data com a cidade: '{city_name}'")
            
            data = download_weather_data(target_date, city_name)
            
            city_name_formatted = city_name.replace(",", "_").replace(" ", "_")
            
            # Monta o nome do arquivo da cidade
            file_name = f"{city_name_formatted}.json"
            file_path = os.path.join(folder_bronze_path_partitioned, file_name)
            
            # Salva o dicionário JSON inteiro no arquivo
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            logger.debug(f"Dados salvos com sucesso no arquivo: {file_path}")
        except Exception as e:
            raise Exception(f"Erro durante a extração: {e}")

    logger.info("=== Extração concluída com sucesso! ===")

    return folder_bronze_path_partitioned
