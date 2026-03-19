import os
import requests
from dotenv import load_dotenv
from loguru import logger

# Carrega variáveis do .env
load_dotenv()

def fetch_weather_data(city_name: str = "Sao Paulo,BR") -> dict:
    """
    Busca os dados de clima da OpenWeatherMap API para a cidade especificada.
    """
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        logger.error("A variável WEATHER_API_KEY não foi encontrada (verifique seu .env).")
        raise ValueError("A variável WEATHER_API_KEY não foi encontrada (verifique seu .env).")
        
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={api_key}"
    
    logger.debug(f"Efetuando requisição GET para {url.split('&appid=')[0]}&appid=***")
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            logger.warning(f"A API retornou um status code inesperado ({response.status_code}).")
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Falha na comunicação com a API: {e}")
        raise
