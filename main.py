import os
from loguru import logger
from src.jobs.extract import run_extract
from src.jobs.transform import run_transform
from src.jobs.load import run_load
from datetime import date

def main():
    logger.info("=== Iniciando Pipeline ETL ===")
    
    cities_names_list = [
        'Sao Paulo,BR', 'Rio de Janeiro,BR', 'Belo Horizonte,BR', 'Curitiba,BR', 
        'Porto Alegre,BR', 'Recife,BR', 'Salvador,BR', 'Fortaleza,BR', 
        'Brasilia,BR', 'Manaus,BR', 'Belem,BR', 'Goiania,BR', 
        'Campo Grande,BR', 'Florianopolis,BR', 'Vitoria,BR', 'Sao Luis,BR', 
        'Teresina,BR', 'Natal,BR', 'Joao Pessoa,BR', 'Maceio,BR',
        'Cuiaba,BR', 'Porto Velho,BR', 'Boa Vista,BR', 'Aracaju,BR',
        'Palmas,BR', 'Macapa,BR', 'Rio Branco,BR'
    ]

    target_date = date.today()

    # Etapa 1: Extração (Extract)
    bronze_folder_path = run_extract(cities_names_list=cities_names_list, bronze_folder_path='./data/bronze', target_date=target_date)
    logger.info(f"Extração Bronze concluída.")
    
    # Etapa 2: Transformação (Transform)
    silver_folder_path = run_transform(bronze_file_path=bronze_folder_path, silver_folder_path='./data/silver')
    logger.info("Transformação Silver concluída.")
    
    # Etapa 3: Carga (Load)
    run_load(silver_folder_path='./data/silver', table_name='tb_weather_data')
    logger.info("Carga Gold concluída.")
    
    logger.info("=== Pipeline Finalizado ===")

if __name__ == "__main__":
    main()
