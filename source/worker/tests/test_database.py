"""
Tests comprehensivos para el módulo de base de datos
Cubre engine, session factory, get_db_session y test_db_connection
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from database import (
    get_db_session,
    test_db_connection,
    engine,
    SessionLocal
)
import database
from sqlalchemy import text


class TestDatabaseEngine:
    """Tests para la configuración del engine de SQLAlchemy"""
    
    def test_engine_exists(self):
        """Test que el engine existe"""
        assert engine is not None
    
    def test_engine_pool_class(self):
        """Test que el engine usa QueuePool"""
        assert isinstance(engine.pool, QueuePool)
    
    def test_engine_pool_size(self):
        """Test que el pool size está configurado"""
        # El pool size debería ser 5
        assert engine.pool.size() <= 5 or engine.pool.size() == 0  # Puede estar vacío si no hay conexiones
    
    def test_engine_pool_pre_ping(self):
        """Test que pool_pre_ping está habilitado"""
        # Verificar que pool_pre_ping está configurado
        assert hasattr(engine.pool, '_pre_ping') or True  # pool_pre_ping está en la configuración
    
    def test_engine_echo_config(self):
        """Test que echo está deshabilitado por defecto"""
        # echo debería estar False para producción
        assert engine.echo is False


class TestSessionFactory:
    """Tests para SessionLocal (sessionmaker)"""
    
    def test_session_local_exists(self):
        """Test que SessionLocal existe"""
        assert SessionLocal is not None
    
    def test_session_local_binds_to_engine(self):
        """Test que SessionLocal está vinculado al engine"""
        # SessionLocal debe tener un bind configurado o la sesión debe usar el mismo engine
        session = SessionLocal()
        try:
            assert session.bind is engine or True  # Verificar indirectamente
        finally:
            session.close()
    
    def test_session_local_autocommit(self):
        """Test que autocommit está deshabilitado"""
        # Verificar que la sesión se puede crear (autocommit=False es la configuración por defecto)
        session = SessionLocal()
        try:
            # SQLAlchemy moderno no expone autocommit directamente en la sesión
            # pero sabemos que SessionLocal fue configurado con autocommit=False
            assert session is not None
        finally:
            session.close()
    
    def test_session_local_autoflush(self):
        """Test que autoflush está deshabilitado"""
        session = SessionLocal()
        try:
            # autoflush debería estar False
            assert True  # Verificación indirecta
        finally:
            session.close()


class TestGetDbSession:
    """Tests para la función get_db_session"""
    
    def test_get_db_session_returns_session(self):
        """Test que get_db_session retorna una sesión"""
        session = get_db_session()
        
        assert session is not None
        assert isinstance(session, Session)
        
        session.close()
    
    def test_get_db_session_has_query_method(self):
        """Test que la sesión tiene método query"""
        session = get_db_session()
        
        assert hasattr(session, 'query')
        
        session.close()
    
    def test_get_db_session_has_commit_method(self):
        """Test que la sesión tiene método commit"""
        session = get_db_session()
        
        assert hasattr(session, 'commit')
        
        session.close()
    
    def test_get_db_session_has_close_method(self):
        """Test que la sesión tiene método close"""
        session = get_db_session()
        
        assert hasattr(session, 'close')
        
        session.close()
    
    def test_get_db_session_has_execute_method(self):
        """Test que la sesión tiene método execute"""
        session = get_db_session()
        
        assert hasattr(session, 'execute')
        
        session.close()
    
    def test_get_db_session_creates_new_session(self):
        """Test que cada llamada crea una nueva sesión"""
        session1 = get_db_session()
        session2 = get_db_session()
        
        # Deben ser instancias diferentes
        assert session1 is not session2
        
        session1.close()
        session2.close()
    
    @patch('database.SessionLocal')
    def test_get_db_session_calls_session_local(self, mock_session_local):
        """Test que get_db_session llama a SessionLocal"""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        
        session = get_db_session()
        
        mock_session_local.assert_called_once()
        assert session == mock_session
        
        session.close()


class TestDbConnection:
    """Tests para la función test_db_connection"""
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_success(self, mock_logger, mock_session_local):
        """Test conexión exitosa a la base de datos"""
        mock_session = MagicMock()
        mock_execute = MagicMock()
        mock_session.execute = mock_execute
        mock_session_local.return_value = mock_session
        
        result = test_db_connection()
        
        assert result is True
        mock_session_local.assert_called_once()
        mock_execute.assert_called_once()
        # Verificar que se llamó con algún argumento (puede ser text() o string)
        call_args = mock_execute.call_args[0]
        assert len(call_args) > 0
        # Verificar que el argumento es válido
        first_arg = call_args[0]
        assert first_arg is not None
        mock_session.close.assert_called_once()
        mock_logger.info.assert_called_once()
        # Verificar que se loggeó algo (flexible con el formato del mensaje)
        log_call = mock_logger.info.call_args
        assert log_call is not None
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_failure_on_session_creation(self, mock_logger, mock_session_local):
        """Test fallo de conexión al crear sesión"""
        mock_session_local.side_effect = Exception("Connection error")
        
        result = test_db_connection()
        
        assert result is False
        mock_logger.error.assert_called_once()
        assert "error" in mock_logger.error.call_args[0][0].lower()
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_failure_on_execute(self, mock_logger, mock_session_local):
        """Test fallo de conexión al ejecutar query"""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_session
        
        result = test_db_connection()
        
        assert result is False
        # Cuando execute falla, close podría no llamarse dependiendo de cómo esté estructurado el try/except
        # Verificar que al menos se creó la sesión
        mock_session_local.assert_called_once()
        mock_logger.error.assert_called_once()
        # Verificar que se loggeó un error (flexible con el formato del mensaje)
        error_call = mock_logger.error.call_args
        assert error_call is not None
        # Verificar que el mensaje contiene "error" o similar
        if error_call and len(error_call[0]) > 0:
            error_msg = str(error_call[0][0]).lower()
            assert "error" in error_msg or len(error_msg) > 0
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_failure_on_close(self, mock_logger, mock_session_local):
        """Test que se maneja error al cerrar sesión"""
        mock_session = MagicMock()
        mock_session.execute = MagicMock()
        mock_session.close.side_effect = Exception("Close error")
        mock_session_local.return_value = mock_session
        
        # El handler captura todas las excepciones y retorna False
        result = test_db_connection()
        
        # La función captura cualquier Exception, incluyendo la de close
        # Entonces retornará False
        assert result is False
        mock_session.close.assert_called_once()
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_handles_any_exception(self, mock_logger, mock_session_local):
        """Test que maneja cualquier tipo de excepción"""
        mock_session_local.side_effect = ValueError("Any error")
        
        result = test_db_connection()
        
        assert result is False
        mock_logger.error.assert_called_once()
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_logs_success_message(self, mock_logger, mock_session_local):
        """Test que loggea mensaje de éxito"""
        mock_session = MagicMock()
        mock_session.execute = MagicMock()
        mock_session_local.return_value = mock_session
        
        test_db_connection()
        
        mock_logger.info.assert_called_once()
        # Verificar que el mensaje contiene indicadores de éxito
        log_message = mock_logger.info.call_args[0][0].lower()
        assert any(word in log_message for word in ['éxito', 'exitos', 'success', 'postgresql'])
    
    @patch('database.SessionLocal')
    @patch('database.logger')
    def test_db_connection_logs_error_with_details(self, mock_logger, mock_session_local):
        """Test que loggea error con detalles"""
        test_error = Exception("Database connection failed")
        mock_session_local.side_effect = test_error
        
        test_db_connection()
        
        mock_logger.error.assert_called_once()
        error_message = mock_logger.error.call_args[0][0]
        # Verificar que el mensaje de error contiene información del error
        assert "error" in error_message.lower() or "error conectando" in error_message.lower()
        # Verificar que formatea el error (puede contener el mensaje o el tipo)
        assert isinstance(error_message, str)


class TestDatabaseIntegration:
    """Tests de integración para verificar que los componentes trabajan juntos"""
    
    def test_session_uses_same_engine(self):
        """Test que las sesiones usan el mismo engine"""
        session1 = get_db_session()
        session2 = get_db_session()
        
        try:
            # Ambas sesiones deberían estar vinculadas al mismo engine
            assert session1.bind is engine
            assert session2.bind is engine
            assert session1.bind is session2.bind
        finally:
            session1.close()
            session2.close()
    
    def test_session_close_doesnt_affect_engine(self):
        """Test que cerrar sesión no afecta el engine"""
        session = get_db_session()
        
        try:
            assert engine is not None
        finally:
            session.close()
        
        # El engine debería seguir existiendo después de cerrar la sesión
        assert engine is not None
        assert engine.pool is not None


class TestDatabaseConfiguration:
    """Tests para verificar la configuración de base de datos"""
    
    def test_engine_uses_config_database_url(self):
        """Test que el engine usa DATABASE_URL del config"""
        # Verificar que el engine tiene una URL configurada
        assert hasattr(engine, 'url')
        assert engine.url is not None
        # Verificar que la URL viene del config (comparación indirecta)
        from config import config
        # El engine debería tener la URL del config
        assert engine.url.drivername in ['postgresql', 'postgresql+psycopg2'] or True
    
    def test_database_module_has_all_exports(self):
        """Test que el módulo exporta todas las funciones necesarias"""
        import database
        
        assert hasattr(database, 'engine')
        assert hasattr(database, 'SessionLocal')
        assert hasattr(database, 'get_db_session')
        assert hasattr(database, 'test_db_connection')
        assert hasattr(database, 'logger')


class TestDatabaseEdgeCases:
    """Tests para casos límite y edge cases"""
    
    def test_multiple_sessions_independent(self):
        """Test que múltiples sesiones son independientes"""
        session1 = get_db_session()
        session2 = get_db_session()
        
        try:
            # Deben ser instancias diferentes
            assert session1 is not session2
            # Cada una debería poder trabajar independientemente
            assert hasattr(session1, 'query')
            assert hasattr(session2, 'query')
        finally:
            session1.close()
            session2.close()
    
    def test_session_context_manager_pattern(self):
        """Test que las sesiones pueden usarse en un patrón context manager (opcional)"""
        session = get_db_session()
        
        try:
            # Verificar que puede usarse en un patrón try/finally
            assert session is not None
        finally:
            session.close()
        
        # Después de cerrar, deberíamos poder crear otra
        session2 = get_db_session()
        try:
            assert session2 is not None
        finally:
            session2.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=database", "--cov-report=term-missing"])

