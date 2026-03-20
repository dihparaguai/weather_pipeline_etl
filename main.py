from loguru import logger
from src.jobs.extraction import run_extraction

def main():
    logger.info("=== Iniciando Pipeline ETL ===")
    
    # Etapa 1: Extração (Extract)
    weather_data = run_extraction()
    
    # Futuramente: Etapa 2 (Transformação) e Etapa 3 (Carga no Postgres)
    
    logger.info("=== Pipeline Finalizado ===")

if __name__ == "__main__":
    main()
