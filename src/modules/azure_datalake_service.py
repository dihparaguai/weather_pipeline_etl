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

AzureDatalakeService()