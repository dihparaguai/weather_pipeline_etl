from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from datetime import datetime, timedelta
from pendulum import today
from loguru import logger
import sys

sys.path.insert(0, "/opt/airflow")

logger.remove()  # Remove o handler padrão do Loguru
logger.add(sys.stdout, level="DEBUG")  # Adiciona um handler explícito para stdout



from src.jobs.extract import run_extract
from src.jobs.transform import run_transform
from src.jobs.load import run_load

default_args = {
    'owner': 'admin', # Proprietário do job
    'retries': 1, # Número de tentativas em caso de falha
    'retry_delay': timedelta(seconds=15), # Tempo de espera entre tentativas
}

@dag(
    dag_id='weather_pipeline_etl', # Identificador único da dag
    default_args=default_args,
    schedule='0 6 * * *', # Intervalo de execução = minuto 0, hora 6, todos os dias do mês, todos os meses, todos os dias da semana
    start_date=today("America/Sao_Paulo").subtract(days=30), # Data inicio = 30 dias atrás
    catchup=True, # Se True, executa todas as dags entre a data de início e a data atual
)
def weather_etl_pipeline():
    """
    DAG Orquestradora do Weather Pipeline ETL.
    Utiliza arquitetura TaskFlow API (@task).
    """
    
    @task
    def extract_task() -> str:
        context_date = get_current_context()['logical_date'] # Usa a data lógica da execução
        return run_extract(city_name="Sao Paulo,BR", target_date=context_date)

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
