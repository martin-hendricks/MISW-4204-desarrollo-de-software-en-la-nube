"""
Tests unitarios básicos para las tareas de Celery
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from models import Video, VideoStatus
from utils.video_processing import VideoProcessingError
from tasks.video_processor import (
    handle_failed_video,
    process_video,
    cleanup_temp_files,
)


class TestProcessVideoTask:
    """Tests para la tarea process_video"""

    @pytest.fixture
    def mock_video(self):
        """Fixture con un video de ejemplo"""
        video = Mock(spec=Video)
        video.id = 123
        video.player_id = 1
        video.title = "Test Video"
        video.status = VideoStatus.uploaded
        video.original_url = "/api/videos/123/original"
        video.processed_url = None
        video.uploaded_at = datetime.now(timezone.utc)
        video.processed_at = None
        return video

    @pytest.fixture
    def mock_db_session(self, mock_video):
        """Fixture con sesión de BD mockeada"""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = mock_video
        return session

    @patch("tasks.video_processor.get_db_session")
    @patch("tasks.video_processor.video_processor")
    @patch("os.path.getsize")
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("os.remove")
    @patch("os.rename")
    def test_process_video_success(
        self, mock_rename, mock_remove, mock_makedirs, mock_exists, 
        mock_getsize, mock_processor, mock_get_db, mock_db_session, mock_video
    ):
        """Test procesamiento de video exitoso"""
        # Setup
        mock_get_db.return_value = mock_db_session
        
        # Mock de os.path.exists - devolver False para intro/outro
        def exists_side_effect(path):
            if 'intro.mp4' in path or 'outro.mp4' in path:
                return False  # No existen cortinillas
            return True  # Todos los demás archivos existen
        
        mock_exists.side_effect = exists_side_effect
        mock_getsize.return_value = 1024 * 1024  # 1MB file size
        mock_processor.process_video.return_value = "/app/uploads/processed/123.mp4"
        mock_processor.validate_video.return_value = True
        mock_processor.get_video_info.return_value = {"duration": 30, "width": 1280, "height": 720}

        # Ejecutar función directamente (sin sistema de tareas)
        result = process_video.run(123)

        # Verificaciones básicas
        assert result["status"] == "success"
        assert mock_video.status == VideoStatus.processed
        assert mock_video.processed_url == "http://localhost:80/api/videos/processed/123"
        mock_db_session.commit.assert_called_once()

    @patch("tasks.video_processor.get_db_session")
    @patch("os.path.exists", return_value=False)
    def test_process_video_file_not_found(
        self, mock_exists, mock_get_db, mock_db_session, mock_video
    ):
        """Test cuando el archivo original no existe"""
        mock_get_db.return_value = mock_db_session

        # Debe lanzar excepción
        with pytest.raises(VideoProcessingError):
            process_video.run(123)

    @patch("tasks.video_processor.get_db_session")
    def test_handle_failed_video(self, mock_get_db, mock_db_session, mock_video):
        """Test manejo de videos fallidos en DLQ"""
        mock_get_db.return_value = mock_db_session

        # Ejecutar función directamente
        handle_failed_video.run(123, "Test error", "task-abc")

        # Si no lanzó excepción, el test pasa
        assert True


class TestTaskConfiguration:
    """Tests para configuración de tareas"""

    def test_task_has_retries_configured(self):
        """Test que la tarea tiene reintentos configurados"""
        assert process_video.max_retries == 3
        assert process_video.autoretry_for == (Exception,)

    def test_task_has_timeouts(self):
        """Test que la tarea tiene timeouts configurados"""
        assert hasattr(process_video, "soft_time_limit")
        assert hasattr(process_video, "time_limit")


class TestCleanupTask:
    """Tests para limpieza de archivos temporales"""

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.path.getmtime")
    @patch("os.remove")
    @patch("time.time")
    def test_cleanup_removes_old_files(
        self, mock_time, mock_remove, mock_getmtime, mock_isfile, mock_listdir
    ):
        """Test que elimina archivos viejos"""
        current_time = 1000000
        mock_time.return_value = current_time
        mock_listdir.return_value = ["old_file.mp4"]
        mock_isfile.return_value = True
        mock_getmtime.return_value = current_time - 7200  # 2 horas atrás

        # Ejecutar función directamente
        cleanup_temp_files.run()

        # Verificar que se llamó remove
        assert mock_remove.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
