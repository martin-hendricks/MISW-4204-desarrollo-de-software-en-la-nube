"""
Tests básicos para el módulo de base de datos
"""
import pytest
from unittest.mock import patch, MagicMock
from database import get_db_session
import database


class TestDatabase:
    """Tests básicos de base de datos"""
    
    def test_get_db_session(self):
        """Test obtener sesión de BD"""
        session = get_db_session()
        
        assert session is not None
        assert hasattr(session, 'query')
        assert hasattr(session, 'commit')
        
        session.close()
    
    @patch('database.SessionLocal')
    def test_db_connection_success(self, mock_session_local):
        """Test conexión exitosa"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        result = database.test_db_connection()
        
        assert result is True
        mock_session.execute.assert_called_once()
    
    @patch('database.SessionLocal')
    def test_db_connection_failure(self, mock_session_local):
        """Test fallo de conexión"""
        mock_session_local.side_effect = Exception("Connection error")
        
        result = database.test_db_connection()
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

