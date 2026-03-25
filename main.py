import os
from loguru import logger
from src.jobs.extract import run_extract
from src.jobs.transform import run_transform

def main():
    logger.info("=== Iniciando Pipeline ETL ===")
    
    # Etapa 1: Extração (Extract)
    bronze_file_path = run_extract()
    logger.info(f"Extração Bronze concluída. Arquivo gerado: {bronze_file_path}")
    
    # Etapa 2: Transformação (Transform)
    silver_file_path = run_transform(bronze_file_path)
    logger.info("Transformação Silver concluída.")
    
    logger.info("=== Pipeline Finalizado ===")

if __name__ == "__main__":
    main()
