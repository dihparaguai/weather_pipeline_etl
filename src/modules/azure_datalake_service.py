import os
from azure.storage.filedatalake import DataLakeServiceClient
from loguru import logger
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

class AzureDatalakeService:
    """
    Controla conexões com o Azure Data Lake Storage Gen2 usando DataLakeServiceClient.
    """
    
    def __init__(self):
        logger.info("Instanciando a classe AzureDatalakeService...")
        # Credenciais extraídas do .env
        self.conn_str = os.getenv("AZURE_DATALAKE_CONN_STR")
        
        self.client = self._create_client()
        logger.info("Classe AzureDatalakeService instanciada com sucesso!!!")

    def _create_client(self):
        """
        Gera o Cliente do DataLakeServiceClient para conexão.
        """
        logger.info("Conectando ao Azure Data Lake Storage Gen2...")
        
        try:
            logger.info("Testando conexão com o Azure Data Lake Storage Gen2...")
            # Instancia o cliente
            client = DataLakeServiceClient.from_connection_string(conn_str=self.conn_str)
            # Lista os containers para validar a conexão
            containers = client.list_file_systems()
            logger.debug(f"Containers encontrados: {[c.name for c in containers]}")
            logger.info("Conexão estabelecida com sucesso!!!")
            return client
        except Exception as e:
            logger.error(f"Falha ao conectar ao Azure Data Lake Storage Gen2: {e}")
            raise

    def upload_file_to_datalake(self, container_name: str, layer_folder: str, cloud_and_local_file_path_name_dict: dict):
        """
        Faz o upload de um arquivo para o Azure Data Lake Storage Gen2.
        """
        logger.info("Iniciando upload do arquivo...")

        # Obtém o caminho absoluto da raiz do projeto
        base_dir = os.path.dirname(os.path.abspath(__file__))

        logger.debug(f"Container: {container_name}, Pasta Camada: {layer_folder}")
        
        try:
            container_client = self.client.get_file_system_client(container_name)

            for cloud_file_path_name, local_file_path_name in cloud_and_local_file_path_name_dict.items():
                logger.debug(f"Caminho do arquivo na cloud: {cloud_file_path_name}, Caminho do arquivo local: {local_file_path_name}")
                

                file_client = container_client.get_file_client(f"{layer_folder}/{cloud_file_path_name}")
                with open(local_file_path_name, "rb") as f:
                    file_client.upload_data(f, overwrite=True)

            logger.info("Upload realizado com sucesso!!!")
            logger.debug(f"Total de arquivos adicionados: {len(cloud_and_local_file_path_name_dict.items())}")
        except Exception as e:
            logger.error(f"Falha ao realizar upload do arquivo: {e}")
            raise