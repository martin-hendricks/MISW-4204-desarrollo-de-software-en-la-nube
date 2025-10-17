"""
Tests unitarios para el procesamiento de videos
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from utils.video_processing import VideoProcessor, VideoProcessingError


class TestVideoProcessor:
    """Tests para la clase VideoProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Fixture que crea un procesador de video"""
        return VideoProcessor()
    
    @pytest.fixture
    def mock_video_info(self):
        """Fixture con información de video de ejemplo"""
        return {
            'duration': 45.5,
            'width': 1920,
            'height': 1080,
            'codec': 'h264',
            'fps': 30.0,
            'size_bytes': 10485760  # 10 MB
        }
    
    def test_init(self, processor):
        """Test que el procesador se inicializa correctamente"""
        assert processor.max_duration == 30
        assert processor.width == 1280
        assert processor.height == 720
        assert processor.codec == 'libx264'
    
    @patch('ffmpeg.probe')
    def test_get_video_info_success(self, mock_probe, processor, mock_video_info):
        """Test obtener información de video exitosamente"""
        # Mock de ffprobe
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '30/1'
            }],
            'format': {
                'duration': '45.5',
                'size': '10485760'
            }
        }
        
        with patch('os.path.exists', return_value=True):
            info = processor.get_video_info('/fake/path.mp4')
            
            assert info['duration'] == 45.5
            assert info['width'] == 1920
            assert info['height'] == 1080
            assert info['codec'] == 'h264'
    
    @patch('os.path.exists', return_value=False)
    def test_get_video_info_file_not_found(self, mock_exists, processor):
        """Test error cuando el archivo no existe"""
        with pytest.raises(FileNotFoundError):
            processor.get_video_info('/nonexistent/video.mp4')
    
    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.filter')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    def test_process_video_success(
        self,
        mock_get_info,
        mock_exists,
        mock_input,
        mock_filter,
        mock_output,
        mock_run,
        processor,
        mock_video_info
    ):
        """Test procesamiento de video exitoso"""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_info.side_effect = [
            mock_video_info,  # Video original
            {**mock_video_info, 'duration': 30, 'width': 1280, 'height': 720}  # Video procesado
        ]
        
        # Mock de cadena de FFmpeg
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_filter.return_value = mock_stream
        mock_output.return_value = mock_stream
        
        # Simular directorios
        with patch('os.makedirs'):
            result = processor.process_video(
                '/fake/input.mp4',
                '/fake/output.mp4',
                add_logo=False
            )
        
        assert result == '/fake/output.mp4'
        mock_run.assert_called_once()
    
    @patch('os.path.exists', return_value=True)
    def test_validate_video_success(self, mock_exists, processor, mock_video_info):
        """Test validación de video exitosa"""
        valid_info = {
            **mock_video_info,
            'duration': 30,
            'width': 1280,
            'height': 720
        }
        
        with patch.object(processor, 'get_video_info', return_value=valid_info):
            assert processor.validate_video('/fake/video.mp4') is True
    
    @patch('os.path.exists', return_value=True)
    def test_validate_video_too_long(self, mock_exists, processor, mock_video_info):
        """Test validación falla si el video es muy largo"""
        invalid_info = {
            **mock_video_info,
            'duration': 40,  # Más de 35 segundos
            'width': 1280,
            'height': 720
        }
        
        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            assert processor.validate_video('/fake/video.mp4') is False
    
    def test_get_logo_position(self, processor):
        """Test cálculo de posiciones del logo"""
        positions = processor._get_logo_position()
        assert isinstance(positions, tuple)
        assert len(positions) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

