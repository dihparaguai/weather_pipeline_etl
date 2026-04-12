import os
import pandas as pd
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
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
        self.password = quote_plus(os.getenv("PG_PASSWORD"))
        self.host = os.getenv("PG_HOST")
        self.port = os.getenv("PG_PORT")
        self.dbname = os.getenv("PG_DB")
        
        # Deixa a engine da classe pré-pronta para ser usada com o to_sql do Pandas
        self.engine = self._create_engine()

    def _create_engine(self):
        """
        Gera a Engine do SQLAlchemy para conexão.
        """
        logger.info(f"Conectando ao PostgreSQL '{self.dbname}' em {self.host}:{self.port} com usuário '{self.user}'")
        
        # Padrão nativo do SQLAlchemy
        conn_str = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
        logger.debug(f"String de conexão: {conn_str}")
        engine = create_engine(conn_str)
        
        try:
            with engine.connect() as conn:
                logger.debug(f"Testando conexão com o PostgreSQL")
                conn.execute(text("SELECT 1"))
            
        except Exception as e:
            logger.error(f"Falha ao conectar ao PostgreSQL: {e}")
            raise
        
        logger.info(f"Conexão estabelecida com sucesso!")
        return engine

PostgresUtils()