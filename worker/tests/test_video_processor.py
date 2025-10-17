"""
Tests unitarios básicos para el procesamiento de videos
"""
import pytest
from unittest.mock import patch, MagicMock
from utils.video_processing import VideoProcessor, VideoProcessingError


class TestVideoProcessor:
    """Tests básicos para la clase VideoProcessor"""
    
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
            'size_bytes': 10485760
        }
    
    def test_init(self, processor):
        """Test inicialización del procesador"""
        assert processor.max_duration == 30
        assert processor.width == 1280
        assert processor.height == 720
        assert processor.codec == 'libx264'
    
    @patch('ffmpeg.probe')
    def test_get_video_info(self, mock_probe, processor):
        """Test obtener información de video"""
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
    
    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.filter')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    def test_process_video(
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
        """Test procesamiento de video básico"""
        mock_exists.return_value = True
        mock_get_info.side_effect = [
            mock_video_info,
            {**mock_video_info, 'duration': 30, 'width': 1280, 'height': 720}
        ]
        
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_filter.return_value = mock_stream
        mock_output.return_value = mock_stream
        
        with patch('os.makedirs'):
            result = processor.process_video(
                '/fake/input.mp4',
                '/fake/output.mp4',
                add_logo=False
            )
        
        assert result == '/fake/output.mp4'
        mock_run.assert_called_once()
    
    @patch('os.path.exists', return_value=True)
    def test_validate_video(self, mock_exists, processor):
        """Test validación de video"""
        valid_info = {
            'duration': 30,
            'width': 1280,
            'height': 720
        }
        
        with patch.object(processor, 'get_video_info', return_value=valid_info):
            assert processor.validate_video('/fake/video.mp4') is True
    
    def test_get_logo_position(self, processor):
        """Test posición del logo"""
        positions = processor._get_logo_position()
        assert isinstance(positions, tuple)
        assert len(positions) == 2


class TestIntroOutro:
    """Tests básicos para intro/outro"""
    
    @pytest.fixture
    def processor(self):
        return VideoProcessor()
    
    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    def test_add_intro_outro(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test agregar intro y outro"""
        mock_exists.return_value = True
        
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream
        
        result = processor.add_intro_outro(
            '/fake/video.mp4',
            '/fake/output.mp4'
        )
        
        assert result == '/fake/output.mp4'
        mock_concat.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

