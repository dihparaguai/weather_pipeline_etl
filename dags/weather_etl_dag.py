from airflow.decorators import dag, task
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/opt/airflow")

from src.jobs.extract import run_extract
from src.jobs.transform import run_transform
from src.jobs.load import run_load

default_args = {
    'owner': 'admin', # proprietário do job
    'retries': 1, # número de tentativas em caso de falha
    'retry_delay': timedelta(minutes=5), # tempo de espera entre tentativas
}

@dag(
    dag_id='weather_pipeline_etl', # identificador único da dag
    default_args=default_args,
    schedule='@daily', # intervalo de execução
    start_date=datetime(2024, 1, 1), # data de início da execução
    catchup=False, # se True, executa todas as dags entre a data de início e a data atual
)
def weather_etl_pipeline():
    """
    DAG Orquestradora do Weather Pipeline ETL.
    Utiliza arquitetura TaskFlow API (@task).
    """
    
    @task
    def extract_task() -> str:
        return run_extract(city_name="Sao Paulo,BR")

    @task
    def transform_task(bronze_path: str) -> str:
        return run_transform(bronze_path)

    @task
    def load_task(silver_path: str):
        run_load(silver_path)

    # Encadeamento de Execução e Dependências (Extract >> Transform >> Load)
    extract = extract_task()
    transform = transform_task(extract)
    load = load_task(transform)

    extract >> transform >> load

weather_etl_pipeline()
