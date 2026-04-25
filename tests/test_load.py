import pandas as pd
from datetime import date
import pytest

# Classe para simular a engine do SQLAlchemy
class FakeEngine:
    pass

# ================================================================
# Testes da função get_max_date_from_db
# ================================================================

from src.jobs.load import get_max_date_from_db

def test_get_max_date_from_db_returns_error_when_table_not_exists(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna erro quando a tabela não existir.
    """
    # Arrange
    class MockInspector:
        def has_table(self, table_name):
            return False
    
    # Injeção de dependências
    monkeypatch.setattr("src.jobs.load.inspect", lambda engine: MockInspector())
    
    # Act
    result = get_max_date_from_db(db_engine=FakeEngine(), table_name='tb_weather_data', column_name='datetime')

    # Assert
    assert result == None

def test_get_max_date_from_db_returns_error_when_column_not_exists(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna erro quando a coluna não existir.
    """

    # Arrange 
    class MockInspector:
        def has_table(self, table_name):
            return True
        def get_columns(self, table_name):
            return [{'name': 'date'}]
    
    monkeypatch.setattr("src.jobs.load.inspect", lambda engine: MockInspector())

    # Act
    result = get_max_date_from_db(db_engine=FakeEngine(), table_name='tb_weather_data', column_name='datetime')

    # Assert
    assert result == None    

def test_get_max_date_from_db_returns_date_when_exists(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna a data máxima corretamente.
    """
    # Arrange
    def mock_read_sql_valid(query, con):
        """Retorna um DataFrame simulando consumo do SQL."""
        return pd.DataFrame({'max_date': ['2026-04-12 10:00:00']})

    class MockInspector:
        """Simula o sqlalchemy.inspect para simular a existência do schema no banco."""
        def has_table(self, table_name):
            return True 
        def get_columns(self, table_name):
            return [{'name': 'datetime'}] 

    monkeypatch.setattr("src.jobs.load.pd.read_sql", mock_read_sql_valid)
    monkeypatch.setattr("src.jobs.load.inspect", lambda engine: MockInspector())

    # Act
    result = get_max_date_from_db(db_engine=FakeEngine(), table_name='tb_weather_data', column_name='datetime')

    # Assert
    assert str(result) == '2026-04-12'

def test_get_max_date_from_db_returns_none_when_table_empty(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna None quando a query SQL iterar tabela vazia.
    """
    # Arrange
    def mock_read_sql_empty(query, con):
        return pd.DataFrame({'max_date': [None]})

    class MockInspector:
        def has_table(self, table_name):
            return True
        def get_columns(self, table_name):
            return [{'name': 'datetime'}]

    monkeypatch.setattr("src.jobs.load.pd.read_sql", mock_read_sql_empty)
    monkeypatch.setattr("src.jobs.load.inspect", lambda engine: MockInspector())

    # Act
    result = get_max_date_from_db(db_engine=FakeEngine(), table_name='tb_weather_data', column_name='datetime')

    # Assert
    assert result is None

# ================================================================
# Testes da função filter_incremental_file
# ================================================================

from src.jobs.load import filter_incremental_file

def test_filter_incremental_file_returns_empty_list_when_no_files(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna uma lista vazia quando não há arquivos na camada Silver.
    """
    # Arrange
    def mock_listdir(path):
        return []
    
    monkeypatch.setattr("src.jobs.load.os.listdir", mock_listdir)
    
    # Act
    result = filter_incremental_file(silver_folder_path="/path/silver", max_date=None)
    
    # Assert
    assert result == []

def test_filter_incremental_file_returns_all_files_when_no_max_date(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna todos os arquivos quando não há data máxima no banco.
    """
    # Arrange
    def mock_listdir(path):
        return ['20260412.parquet', '20260413.parquet']
    
    monkeypatch.setattr("src.jobs.load.os.listdir", mock_listdir)
    
    # Act
    result = filter_incremental_file(silver_folder_path="/path/silver", max_date=None)
    
    # Assert
    assert result == ['/path/silver/20260412.parquet', '/path/silver/20260413.parquet']

def test_filter_incremental_file_returns_incremental_files(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna apenas os arquivos com data maior que a data máxima no banco.
    """
    # Arrange
    def mock_listdir(path):
        return ['20260412.parquet', '20260413.parquet', '20260414.parquet']
    
    monkeypatch.setattr("src.jobs.load.os.listdir", mock_listdir)
    
    # Act
    result = filter_incremental_file(silver_folder_path="/path/silver", max_date=date(2026, 4, 13))
    
    # Assert
    assert result == ['/path/silver/20260414.parquet']

# ================================================================
# Testes da função concat_parquet_files
# ================================================================

from src.jobs.load import concat_parquet_files

def test_concat_parquet_files_returns_none_when_no_files(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna None quando não há arquivos na camada Silver.
    """
    # Act
    result = concat_parquet_files(parquet_file_path_list=[])
    
    # Assert
    assert result is None

def test_concat_parquet_files_returns_dataframe_concatenated(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna um DataFrame concatenado quando há arquivos na camada Silver.
    """
    # Arrange
    def mock_read_parquet(path, engine):
        return pd.DataFrame({'city': ['Sao Paulo'], 'temperature': [25.0]})
    
    monkeypatch.setattr("src.jobs.load.pd.read_parquet", mock_read_parquet)
    
    # Act
    result = concat_parquet_files(parquet_file_path_list=['/path/silver/20260412.parquet', '/path/silver/20260413.parquet'])
    
    # Assert
    assert result.equals(pd.DataFrame({'city': ['Sao Paulo', 'Sao Paulo'], 'temperature': [25.0, 25.0]}))
    
# ================================================================
# Testes da função save_to_db
# ================================================================

from src.jobs.load import save_to_db

def test_save_to_db_returns_none_when_no_data(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna None quando não há dados para adicionar no banco.
    """  
    # Act
    result = save_to_db(df=None, db_engine=FakeEngine(), table_name='tb_weather_data')
    
    # Assert
    assert result is None 
