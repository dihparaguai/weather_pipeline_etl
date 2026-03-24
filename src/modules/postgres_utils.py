import os
import pandas as pd
from sqlalchemy import create_engine
from loguru import logger
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

class PostgresUtils:
    """
    Controla conexões com o PostgreSQL usando SQLAlchemy para as cargas de dados.
    Esta classe assume que o Banco e o Usuário já foram devidamente criados previamente.
    """
    
    def __init__(self):
        # Credenciais Definitivas extraídas do .env
        self.user = os.getenv("PG_USER")
        self.password = os.getenv("PG_PASSWORD")
        self.host = os.getenv("PG_HOST")
        self.port = os.getenv("PG_PORT")
        self.dbname = os.getenv("PG_DB")
        
        # Inicia a Engine de cara
        self.engine = self._create_engine()

    def _create_engine(self):
        """
        Gera a Engine do SQLAlchemy para conexão.
        """
        logger.info(f"Conectando ao PostgreSQL '{self.dbname}' em {self.host}:{self.port} com usuário '{self.user}'")
        conn_str = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        logger.info(f"Conexão estabelecida com sucesso!")
        return create_engine(conn_str)
