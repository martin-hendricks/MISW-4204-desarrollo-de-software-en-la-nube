"""
Tests unitarios para las tareas de Celery
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from tasks.video_processor import process_video, handle_failed_video
from models import Video


class TestProcessVideoTask:
    """Tests para la tarea process_video"""
    
    @pytest.fixture
    def mock_video(self):
        """Fixture con un video de ejemplo"""
        video = Mock(spec=Video)
        video.id = 123
        video.user_id = 1
        video.title = "Test Video"
        video.status = "uploaded"
        video.original_path = "/app/uploads/original/123.mp4"
        video.processed_path = None
        video.uploaded_at = datetime.utcnow()
        return video
    
    @pytest.fixture
    def mock_db_session(self, mock_video):
        """Fixture con sesión de BD mockeada"""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = mock_video
        return session
    
    @patch('tasks.video_processor.get_db_session')
    @patch('tasks.video_processor.video_processor')
    @patch('os.path.exists', return_value=True)
    def test_process_video_success(
        self,
        mock_exists,
        mock_processor,
        mock_get_db,
        mock_db_session,
        mock_video
    ):
        """Test procesamiento de video exitoso"""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_processor.process_video.return_value = "/app/uploads/processed/123.mp4"
        mock_processor.validate_video.return_value = True
        mock_processor.get_video_info.return_value = {'duration': 30}
        
        # Mock de self.request en la tarea
        with patch('tasks.video_processor.process_video.request') as mock_request:
            mock_request.id = 'task-123'
            mock_request.retries = 0
            
            # Ejecutar tarea (sin .delay() para testing)
            result = process_video.apply(args=[123])
        
        # Verificaciones
        assert result.successful()
        assert mock_video.status == "processed"
        assert mock_video.processed_path == "/app/uploads/processed/123.mp4"
    
    @patch('tasks.video_processor.get_db_session')
    def test_process_video_not_found(self, mock_get_db):
        """Test cuando el video no existe en BD"""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = session
        
        # Ejecutar y esperar error
        with pytest.raises(Exception):
            process_video.apply(args=[999])
    
    @patch('tasks.video_processor.get_db_session')
    @patch('os.path.exists', return_value=False)
    def test_process_video_file_not_found(
        self,
        mock_exists,
        mock_get_db,
        mock_db_session,
        mock_video
    ):
        """Test cuando el archivo original no existe"""
        mock_get_db.return_value = mock_db_session
        
        # Ejecutar y esperar error
        with pytest.raises(Exception):
            process_video.apply(args=[123])
    
    @patch('tasks.video_processor.get_db_session')
    def test_handle_failed_video(self, mock_get_db, mock_db_session, mock_video):
        """Test manejo de videos fallidos en DLQ"""
        mock_get_db.return_value = mock_db_session
        
        # Ejecutar tarea de DLQ
        handle_failed_video.apply(args=[123, "Test error", "task-abc"])
        
        # Verificar que se marcó como fallido
        assert mock_video.status == "failed"
        assert "Test error" in mock_video.error_message


class TestTaskRetries:
    """Tests para el sistema de reintentos"""
    
    def test_task_configured_with_retries(self):
        """Test que la tarea tiene configurado el sistema de reintentos"""
        assert process_video.max_retries == 3
        assert process_video.autoretry_for == (Exception,)
    
    def test_task_has_backoff(self):
        """Test que la tarea tiene backoff exponencial"""
        # Verificar configuración
        assert hasattr(process_video, 'retry_backoff')
        assert hasattr(process_video, 'retry_backoff_max')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

