import os
import requests
from dotenv import load_dotenv
from loguru import logger
from datetime import date

# Carrega as variáveis do arquivo .env
load_dotenv()

def download_weather_data(target_date: date, city_name: str = "Sao Paulo,BR") -> dict:
    """
    Busca os dados de clima da OpenWeatherMap API para a cidade especificada.
    """
    api_key = os.getenv("WEATHER_API_KEY")
    
    # Interrompe o fluxo caso a chave de autenticação esteja ausente
    if not api_key:
        logger.error("A variável WEATHER_API_KEY não foi encontrada (verifique seu .env).")
        raise ValueError("A variável WEATHER_API_KEY não foi encontrada (verifique seu .env).")

    # 'q' = cidade alvo | 'units=metric' = formato em graus Celsius | 'start_date' and 'end_date' = data alvo | 'appid' = chave de autenticação
    # OBS: A api openweather não aceita o parâmetro 'start_date' e 'end_date' para o endpoint 'weather', apenas para 'onecall' ou 'history', mas esses endpoints não são gratuitos
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&start_date={target_date}&end_date={target_date}&units=metric&appid={api_key}"
    
    # Corta a string no log para não expor a chave de acesso (api_key)
    logger.debug(f"Efetuando requisição GET para {url.split('&appid=')[0]}&appid=***")
    
    try:
        response = requests.get(url)
        
        # Emite um alerta se o retorno da API não for o sucesso padrão HTTP 200
        if response.status_code != 200:
            logger.warning(f"A API retornou um status code inesperado ({response.status_code}).")
        
        # Transforma os dados limpos recém resgatados em formato estruturado (JSON)
        return response.json()
    except Exception as e:
        logger.error(f"Falha na comunicação com a API: {e}")
        raise
