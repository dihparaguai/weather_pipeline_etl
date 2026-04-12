import pandas as pd
import pytest

from src.jobs.load import get_max_date_from_db

# Classe para simular a engine do SQLAlchemy
class FakeEngine:
    pass

def test_get_max_date_from_db_returns_date_when_valid(monkeypatch):
    """
    CENÁRIO: Valida se a função retorna a data máxima corretamente.
    """
    # Arrange: Configuração dos Mocks
    def mock_read_sql_valid(query, con):
        """Retorna um DataFrame simulando consumo do SQL."""
        return pd.DataFrame({'max_date': ['2026-04-12 10:00:00']})

    class MockInspector:
        """Simula o sqlalchemy.inspect para simular a existência do schema no banco."""
        def has_table(self, table_name):
            return True 
        def get_columns(self, table_name):
            return [{'name': 'datetime'}] 

    # Injeção das dependências simuladas em tempo de execução
    monkeypatch.setattr("src.jobs.load.pd.read_sql", mock_read_sql_valid)
    monkeypatch.setattr("src.jobs.load.inspect", lambda engine: MockInspector())

    # Act: Execução
    result = get_max_date_from_db(db_engine=FakeEngine(), table_name='tb_weather_data', column_name='datetime')

    # Assert: Validação
    assert result is not None
    assert str(result) == '2026-04-12'
