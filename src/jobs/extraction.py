import json
import os
from datetime import datetime
from loguru import logger
from src.modules.weather_api import fetch_weather_data

def run_extraction(city_name: str = "Sao Paulo,BR") -> str:
    """
    Job de extração que chama a API e salva os dados brutos na pasta 'data/bronze'.
    """
    logger.info("Iniciando a extração dos dados...")
    
    try:
        logger.debug(f"Chamando a função fetch_weather_data com a cidade: '{city_name}'")
        data = fetch_weather_data(city_name)
        
        # Garante que a pasta 'data' exista para não quebrar caso seja apagada
        os.makedirs("data/bronze", exist_ok=True)
        
        city_name_formatted = city_name.replace(",", "_").replace(" ", "_")
        
        # Monta o nome do arquivo com a data e hora atual
        filename = f"{city_name_formatted}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join("data/bronze", filename)
        
        # Salva o dicionário JSON inteiro no arquivo
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Dados salvos com sucesso no arquivo: {filepath}")
        return filepath
    except Exception as e:
        raise Exception(f"Erro durante a extração: {e}")
