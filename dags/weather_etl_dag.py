from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from datetime import datetime, timedelta
from pendulum import today
from loguru import logger
import sys

# Adiciona o path raiz ao PYTHONPATH para que o Airflow consiga importar o código
sys.path.insert(0, "/opt/airflow")

logger.remove()  # Remove o handler padrão do Loguru
logger.add(sys.stdout, level="DEBUG")  # Adiciona um handler explícito para stdout

from src.jobs.extract import run_extract
from src.jobs.transform import run_transform
from src.jobs.load import run_load

cities_names_list = [
    'Sao Paulo,BR', 'Rio de Janeiro,BR', 'Belo Horizonte,BR', 'Curitiba,BR', 
    'Porto Alegre,BR', 'Recife,BR', 'Salvador,BR', 'Fortaleza,BR', 
    'Brasilia,BR', 'Manaus,BR', 'Belem,BR', 'Goiania,BR', 
    'Campo Grande,BR', 'Florianopolis,BR', 'Vitoria,BR', 'Sao Luis,BR', 
    'Teresina,BR', 'Natal,BR', 'Joao Pessoa,BR', 'Maceio,BR',
    'Cuiaba,BR', 'Porto Velho,BR', 'Boa Vista,BR', 'Aracaju,BR',
    'Palmas,BR', 'Macapa,BR', 'Rio Branco,BR'
]

default_args = {
    'owner': 'admin', # Proprietário do job
    'retries': 1, # Número de tentativas em caso de falha
    'retry_delay': timedelta(seconds=15), # Tempo de espera entre tentativas
}

@dag(
    dag_id='weather_pipeline_etl', # Identificador único da dag
    default_args=default_args,
    schedule='0 6 * * *', # Intervalo de execução = minuto 0, hora 6, todos os dias do mês, todos os meses, todos os dias da semana
    start_date=today("America/Sao_Paulo").subtract(days=0), # Data de início da DAG
    catchup=False, # Se True, executa todas as dags entre a data de início e a data atual
)
def weather_etl_pipeline():
    """
    DAG Orquestradora do Weather Pipeline ETL.
    Utiliza arquitetura TaskFlow API (@task).
    """
    
    @task
    def extract_task() -> None:
        context_date = get_current_context()['logical_date'] # Usa a data lógica da execução
        run_extract(cities_names_list=cities_names_list, bronze_folder_path='./data/bronze', target_date=context_date)

    @task
    def transform_task() -> None:
        run_transform(bronze_folder_path='./data/bronze', silver_folder_path='./data/silver')

    @task
    def load_task() -> None:
        run_load(silver_folder_path='./data/silver', table_name='tb_weather_data')

    # Encadeamento de Execução e Dependências (Extract >> Transform >> Load)
    extract_task() >> transform_task() >> load_task()

# Instancia a DAG e a disponibiliza para o Airflow
weather_etl_pipeline()
