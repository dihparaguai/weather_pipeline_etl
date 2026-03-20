import json
import os
from datetime import datetime
from loguru import logger
from src.modules.weather_api import fetch_weather_data

def run_extraction(city_name: str = "Sao Paulo,BR") -> dict:
    """
    Job de extração que chama a API e salva os dados brutos na pasta 'data/'.
    """
    logger.info("Iniciando a extração dos dados...")
    
    try:
        logger.debug(f"Chamando a função fetch_weather_data com a cidade: '{city_name}'")
        data = fetch_weather_data(city_name)
        
        # Garante que a pasta 'data' exista para não quebrar caso seja apagada
        os.makedirs("data", exist_ok=True)
        
        # Monta o nome do arquivo com a data e hora atual
        filename = f"raw_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join("data", filename)
        
        # Salva o dicionário JSON inteiro no arquivo
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Dados salvos com sucesso no arquivo: {filepath}")
        return data
    except Exception as e:
        raise Exception(f"Erro durante a extração: {e}")
