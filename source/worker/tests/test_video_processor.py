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


class TestVideoValidation:
    """Tests para validación de videos"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=True)
    def test_validate_video_invalid_duration(self, mock_exists, processor):
        """Test validación con duración excesiva"""
        invalid_info = {
            'duration': 40,  # Más de 35 segundos
            'width': 1280,
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            assert processor.validate_video('/fake/video.mp4') is False

    @patch('os.path.exists', return_value=True)
    def test_validate_video_invalid_resolution(self, mock_exists, processor):
        """Test validación con resolución incorrecta"""
        invalid_info = {
            'duration': 30,
            'width': 1920,  # Debería ser 1280
            'height': 1080  # Debería ser 720
        }

        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            assert processor.validate_video('/fake/video.mp4') is False

    @patch('os.path.exists', return_value=False)
    def test_validate_video_file_not_exists(self, mock_exists, processor):
        """Test validación cuando el archivo no existe"""
        info = {
            'duration': 30,
            'width': 1280,
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=info):
            assert processor.validate_video('/fake/video.mp4') is False


class TestVideoInfoErrors:
    """Tests para manejo de errores al obtener info de video"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=False)
    def test_get_video_info_file_not_found(self, mock_exists, processor):
        """Test cuando el archivo no existe"""
        with pytest.raises(FileNotFoundError):
            processor.get_video_info('/fake/nonexistent.mp4')

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_no_video_stream(self, mock_probe, mock_exists, processor):
        """Test cuando no hay stream de video"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'audio'  # Solo audio, no video
            }],
            'format': {}
        }

        with pytest.raises(VideoProcessingError, match="No se encontró stream de video"):
            processor.get_video_info('/fake/audio_only.mp4')

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_ffmpeg_error(self, mock_probe, mock_exists, processor):
        """Test cuando FFmpeg falla"""
        import ffmpeg as ffmpeg_module
        mock_error = ffmpeg_module.Error('ffmpeg', '', b'Error message')
        mock_probe.side_effect = mock_error

        with pytest.raises(VideoProcessingError, match="Error leyendo video"):
            processor.get_video_info('/fake/corrupted.mp4')


class TestProcessVideoErrors:
    """Tests para manejo de errores en procesamiento"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=False)
    def test_process_video_input_not_found(self, mock_exists, processor):
        """Test cuando el archivo de entrada no existe"""
        with pytest.raises(FileNotFoundError):
            processor.process_video('/fake/input.mp4', '/fake/output.mp4')

    @patch('os.path.exists')
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('ffmpeg.run')
    def test_process_video_output_not_created(
        self, mock_run, mock_output, mock_input, mock_get_info, mock_exists, processor
    ):
        """Test cuando el procesamiento no genera el archivo de salida"""
        # Input existe, output no
        mock_exists.side_effect = lambda path: '/output' not in path
        mock_get_info.return_value = {
            'duration': 30,
            'width': 1920,
            'height': 1080,
            'codec': 'h264',
            'fps': 30.0,
            'size_bytes': 1024 * 1024
        }

        # Mock the ffmpeg stream pipeline
        mock_stream = MagicMock()
        mock_stream.filter.return_value = mock_stream
        mock_stream.overlay.return_value = mock_stream
        mock_input.return_value = mock_stream
        mock_output.return_value = mock_stream

        with patch('os.makedirs'):
            with pytest.raises(VideoProcessingError, match="No se generó el video procesado"):
                processor.process_video('/fake/input.mp4', '/fake/output.mp4')


class TestLogoPositioning:
    """Tests para posicionamiento del logo"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    def test_logo_position_top_left(self, processor):
        """Test posición superior izquierda"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'top-left'
            mock_config.LOGO_MARGIN = 10

            position = processor._get_logo_position()
            assert position == (10, 10)

    def test_logo_position_bottom_right(self, processor):
        """Test posición inferior derecha"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'bottom-right'
            mock_config.LOGO_MARGIN = 10

            position = processor._get_logo_position()
            assert position[0] == 'W-w-10'
            assert position[1] == 'H-h-10'

    def test_logo_position_center(self, processor):
        """Test posición centrada"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'center'

            position = processor._get_logo_position()
            assert position[0] == '(W-w)/2'
            assert position[1] == '(H-h)/2'

    def test_logo_position_invalid_defaults_to_top_right(self, processor):
        """Test que posición inválida usa default (top-right)"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'invalid-position'
            mock_config.LOGO_MARGIN = 10

            position = processor._get_logo_position()
            assert position[0] == 'W-w-10'


class TestIntroOutroEdgeCases:
    """Tests para casos especiales de intro/outro"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=False)
    def test_add_intro_outro_no_files(self, mock_exists, processor):
        """Test cuando no hay archivos de intro/outro"""
        result = processor.add_intro_outro('/fake/video.mp4', '/fake/output.mp4')

        # Debe retornar el video original sin modificar
        assert result == '/fake/video.mp4'

    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    def test_add_intro_outro_ffmpeg_error(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test cuando FFmpeg falla al concatenar"""
        mock_exists.return_value = True
        mock_run.side_effect = Exception("FFmpeg concatenation failed")

        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream

        with pytest.raises(VideoProcessingError, match="Error en cortinillas"):
            processor.add_intro_outro('/fake/video.mp4', '/fake/output.mp4')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

