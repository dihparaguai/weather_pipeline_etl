import json
import os
from datetime import datetime
from loguru import logger
from src.modules.weather_api import download_weather_data
from datetime import date

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
