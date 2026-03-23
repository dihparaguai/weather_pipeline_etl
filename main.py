from loguru import logger
from src.jobs.extraction import run_extraction
from src.jobs.transformation import run_transformation_pipeline

def main():
    logger.info("=== Iniciando Pipeline ETL ===")
    
    # Etapa 1: Extração (Extract)
    bronze_file_path = run_extraction()
    logger.info(f"Extração Bronze concluída. Arquivo gerado: {bronze_file_path}")
    
    # Etapa 2: Transformação (Transform)
    silver_file_path = run_transformation_pipeline(bronze_file_path)
    logger.info(f"Transformação Silver concluída. Arquivo gerado: {silver_file_path}")
    
    # Futuramente: Etapa 3 (Carga no Postgres)
    
    logger.info("=== Pipeline Finalizado ===")

if __name__ == "__main__":
    main()
