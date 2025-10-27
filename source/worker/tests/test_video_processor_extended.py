"""
Tests extendidos y exhaustivos para el procesamiento de videos
Cubre casos edge, validaciones adicionales y escenarios complejos
"""
import pytest
from unittest.mock import patch, MagicMock, call
from utils.video_processing import VideoProcessor, VideoProcessingError


class TestGetVideoInfoExtended:
    """Tests extendidos para obtener información de video"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_fps_with_division(self, mock_probe, mock_exists, processor):
        """Test cuando FPS viene como fracción (ej: 30/1)"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '30/1'
            }],
            'format': {
                'duration': '30.0',
                'size': '5242880'
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert abs(info['fps'] - 30.0) < 0.001

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_fps_variable(self, mock_probe, mock_exists, processor):
        """Test cuando FPS es variable (ej: 23.976 como 24000/1001)"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '24000/1001'
            }],
            'format': {
                'duration': '30.0',
                'size': '5242880'
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert abs(info['fps'] - 23.976) < 0.001

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_fps_zero_denominator(self, mock_probe, mock_exists, processor):
        """Test cuando el denominador de FPS es 0 (usa default 30)"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '30/0'
            }],
            'format': {
                'duration': '30.0',
                'size': '5242880'
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert abs(info['fps'] - 30.0) < 0.001

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_fps_as_float(self, mock_probe, mock_exists, processor):
        """Test cuando FPS viene como float directo"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '25.0'
            }],
            'format': {
                'duration': '30.0',
                'size': '5242880'
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert abs(info['fps'] - 25.0) < 0.001

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_missing_optional_fields(self, mock_probe, mock_exists, processor):
        """Test cuando faltan campos opcionales"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                # codec_name ausente - usa 'unknown'
                # r_frame_rate ausente - usa '30/1'
            }],
            'format': {
                # duration ausente - usa 0
                # size ausente - usa 0
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert info['codec'] == 'unknown'
        assert abs(info['fps'] - 30.0) < 0.001
        assert info['duration'] == 0
        assert info['size_bytes'] == 0

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_get_video_info_multiple_streams(self, mock_probe, mock_exists, processor):
        """Test cuando hay múltiples streams (debe tomar el primero de video)"""
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac'
                },
                {
                    'codec_type': 'video',
                    'width': 1920,
                    'height': 1080,
                    'codec_name': 'h264',
                    'r_frame_rate': '30/1'
                },
                {
                    'codec_type': 'subtitle'
                }
            ],
            'format': {
                'duration': '30.0',
                'size': '5242880'
            }
        }

        info = processor.get_video_info('/fake/video.mp4')
        assert info['codec'] == 'h264'
        assert info['width'] == 1920


class TestProcessVideoExtended:
    """Tests extendidos para procesamiento de video"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists')
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('ffmpeg.run')
    def test_process_video_with_custom_logo(
        self, mock_run, mock_output, mock_input, mock_get_info, mock_exists, processor
    ):
        """Test procesamiento con logo personalizado"""
        # Input y logo existen siempre, output existe después de ffmpeg.run
        mock_exists.side_effect = lambda path: 'input' in path or 'logo' in path or 'output' in path

        # Mock get_video_info para ser llamado dos veces: antes y después del procesamiento
        mock_get_info.side_effect = [
            {
                'duration': 25,
                'width': 1920,
                'height': 1080,
                'codec': 'h264',
                'fps': 30.0,
                'size_bytes': 5242880
            },
            {
                'duration': 25,
                'width': 1280,
                'height': 720,
                'codec': 'h264',
                'fps': 30.0,
                'size_bytes': 3145728
            }
        ]

        # Mock the ffmpeg stream pipeline
        mock_stream = MagicMock()
        mock_stream.filter.return_value = mock_stream
        mock_stream.overlay.return_value = mock_stream
        mock_input.return_value = mock_stream
        mock_output.return_value = mock_stream

        with patch('os.makedirs'):
            result = processor.process_video(
                '/fake/input.mp4',
                '/fake/output.mp4',
                add_logo=True,
                logo_path='/fake/custom_logo.png'
            )

        assert result == '/fake/output.mp4'
        # Debe llamar a get_video_info dos veces: antes y después del procesamiento
        assert mock_get_info.call_count == 2
        # Debe llamar a input dos veces: video y logo
        assert mock_input.call_count >= 2

    @patch('os.path.exists')
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('ffmpeg.run')
    def test_process_video_logo_not_found(
        self, mock_run, mock_output, mock_input, mock_get_info, mock_exists, processor
    ):
        """Test procesamiento cuando el logo no existe (debe continuar sin logo)"""
        # Input existe, logo NO existe
        def exists_side_effect(path):
            if 'input' in path or 'output' in path:
                return True
            if 'logo' in path:
                return False
            return False

        mock_exists.side_effect = exists_side_effect

        mock_get_info.return_value = {
            'duration': 25,
            'width': 1920,
            'height': 1080,
            'codec': 'h264',
            'fps': 30.0,
            'size_bytes': 5242880
        }

        mock_stream = MagicMock()
        mock_stream.filter.return_value = mock_stream
        mock_input.return_value = mock_stream
        mock_output.return_value = mock_stream

        with patch('os.makedirs'):
            result = processor.process_video(
                '/fake/input.mp4',
                '/fake/output.mp4',
                add_logo=True
            )

        assert result == '/fake/output.mp4'
        # No debe llamar a overlay si no hay logo
        mock_stream.overlay.assert_not_called()

    @patch('os.path.exists', return_value=True)
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    @patch('ffmpeg.run')
    def test_process_video_ffmpeg_error(
        self, mock_run, mock_output, mock_input, mock_get_info, mock_exists, processor
    ):
        """Test cuando FFmpeg falla durante el procesamiento"""
        import ffmpeg as ffmpeg_module

        mock_get_info.return_value = {
            'duration': 25,
            'width': 1920,
            'height': 1080,
            'codec': 'h264',
            'fps': 30.0,
            'size_bytes': 5242880
        }

        mock_stream = MagicMock()
        mock_stream.filter.return_value = mock_stream
        mock_input.return_value = mock_stream
        mock_output.return_value = mock_stream

        # Simular error de FFmpeg
        mock_error = ffmpeg_module.Error('ffmpeg', '', b'Encoding failed')
        mock_run.side_effect = mock_error

        with patch('os.makedirs'):
            with pytest.raises(VideoProcessingError, match="Error procesando video con FFmpeg"):
                processor.process_video('/fake/input.mp4', '/fake/output.mp4', add_logo=False)

    @patch('os.path.exists', return_value=True)
    @patch('utils.video_processing.VideoProcessor.get_video_info')
    def test_process_video_get_info_fails(
        self, mock_get_info, mock_exists, processor
    ):
        """Test cuando get_video_info falla"""
        mock_get_info.side_effect = VideoProcessingError("No se puede leer el video")

        with pytest.raises(VideoProcessingError, match="Error en procesamiento"):
            processor.process_video('/fake/input.mp4', '/fake/output.mp4')


class TestAddIntroOutroExtended:
    """Tests extendidos para intro/outro"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    def test_add_intro_outro_only_intro(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test agregar solo intro (sin outro)"""
        def exists_side_effect(path):
            if 'intro' in path or 'video' in path:
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream

        result = processor.add_intro_outro(
            '/fake/video.mp4',
            '/fake/output.mp4',
            intro_path='/fake/intro.mp4'
        )

        assert result == '/fake/output.mp4'
        # Debe concatenar 2 videos: intro + video principal
        args = mock_concat.call_args
        assert len(args[0]) == 2

    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists')
    def test_add_intro_outro_only_outro(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test agregar solo outro (sin intro)"""
        def exists_side_effect(path):
            if 'outro' in path or 'video' in path:
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream

        result = processor.add_intro_outro(
            '/fake/video.mp4',
            '/fake/output.mp4',
            outro_path='/fake/outro.mp4'
        )

        assert result == '/fake/output.mp4'
        # Debe concatenar 2 videos: video principal + outro
        args = mock_concat.call_args
        assert len(args[0]) == 2

    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists', return_value=True)
    def test_add_intro_outro_both(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test agregar intro y outro"""
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream

        result = processor.add_intro_outro(
            '/fake/video.mp4',
            '/fake/output.mp4',
            intro_path='/fake/intro.mp4',
            outro_path='/fake/outro.mp4'
        )

        assert result == '/fake/output.mp4'
        # Debe concatenar 3 videos: intro + video principal + outro
        args = mock_concat.call_args
        assert len(args[0]) == 3

    @patch('os.path.exists', return_value=False)
    def test_add_intro_outro_all_missing(self, mock_exists, processor):
        """Test cuando no existen intro, outro ni config defaults"""
        result = processor.add_intro_outro('/fake/video.mp4', '/fake/output.mp4')

        # Debe retornar el video original sin modificar
        assert result == '/fake/video.mp4'

    @patch('ffmpeg.run')
    @patch('ffmpeg.output')
    @patch('ffmpeg.concat')
    @patch('ffmpeg.input')
    @patch('os.path.exists', return_value=True)
    def test_add_intro_outro_concat_parameters(
        self, mock_exists, mock_input, mock_concat, mock_output, mock_run, processor
    ):
        """Test que los parámetros de concatenación son correctos"""
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_concat.return_value = mock_stream
        mock_output.return_value = mock_stream

        processor.add_intro_outro(
            '/fake/video.mp4',
            '/fake/output.mp4',
            intro_path='/fake/intro.mp4'
        )

        # Verificar que concat se llama con v=1 (video) y a=0 (sin audio)
        mock_concat.assert_called_once()
        call_kwargs = mock_concat.call_args.kwargs
        assert call_kwargs.get('v') == 1
        assert call_kwargs.get('a') == 0


class TestValidateVideoExtended:
    """Tests extendidos para validación de videos"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=True)
    def test_validate_video_all_valid(self, mock_exists, processor):
        """Test validación completa exitosa"""
        valid_info = {
            'duration': 30,
            'width': 1280,
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=valid_info):
            result = processor.validate_video('/fake/video.mp4')
            assert result is True

    @patch('os.path.exists', return_value=True)
    def test_validate_video_max_duration_with_intro_outro(self, mock_exists, processor):
        """Test validación con duración máxima (30s + 5s de cortinillas)"""
        valid_info = {
            'duration': 35,  # Máximo permitido
            'width': 1280,
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=valid_info):
            result = processor.validate_video('/fake/video.mp4')
            assert result is True

    @patch('os.path.exists', return_value=True)
    def test_validate_video_duration_exceeds_limit(self, mock_exists, processor):
        """Test validación con duración que excede el límite"""
        invalid_info = {
            'duration': 35.1,  # Más del máximo
            'width': 1280,
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            result = processor.validate_video('/fake/video.mp4')
            assert result is False

    @patch('os.path.exists', return_value=True)
    def test_validate_video_invalid_width(self, mock_exists, processor):
        """Test validación con ancho incorrecto"""
        invalid_info = {
            'duration': 30,
            'width': 1920,  # Debería ser 1280
            'height': 720
        }

        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            result = processor.validate_video('/fake/video.mp4')
            assert result is False

    @patch('os.path.exists', return_value=True)
    def test_validate_video_invalid_height(self, mock_exists, processor):
        """Test validación con alto incorrecto"""
        invalid_info = {
            'duration': 30,
            'width': 1280,
            'height': 1080  # Debería ser 720
        }

        with patch.object(processor, 'get_video_info', return_value=invalid_info):
            result = processor.validate_video('/fake/video.mp4')
            assert result is False

    @patch('os.path.exists', return_value=True)
    def test_validate_video_exception_handling(self, mock_exists, processor):
        """Test manejo de excepciones durante la validación"""
        with patch.object(processor, 'get_video_info', side_effect=Exception("Error inesperado")):
            result = processor.validate_video('/fake/video.mp4')
            assert result is False


class TestLogoPositioningExtended:
    """Tests extendidos para posicionamiento del logo"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    def test_logo_position_top_right(self, processor):
        """Test posición superior derecha (default)"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'top-right'
            mock_config.LOGO_MARGIN = 20

            position = processor._get_logo_position()
            assert position[0] == 'W-w-20'
            assert position[1] == 20

    def test_logo_position_bottom_left(self, processor):
        """Test posición inferior izquierda"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'bottom-left'
            mock_config.LOGO_MARGIN = 15

            position = processor._get_logo_position()
            assert position[0] == 15
            assert position[1] == 'H-h-15'

    def test_logo_position_different_margins(self, processor):
        """Test con diferentes márgenes"""
        with patch('utils.video_processing.config') as mock_config:
            mock_config.LOGO_POSITION = 'top-left'
            mock_config.LOGO_MARGIN = 50

            position = processor._get_logo_position()
            assert position == (50, 50)

    def test_logo_position_all_positions(self, processor):
        """Test todas las posiciones posibles"""
        positions_to_test = ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']

        for pos in positions_to_test:
            with patch('utils.video_processing.config') as mock_config:
                mock_config.LOGO_POSITION = pos
                mock_config.LOGO_MARGIN = 10

                position = processor._get_logo_position()
                assert isinstance(position, tuple)
                assert len(position) == 2


class TestVideoProcessorInit:
    """Tests para la inicialización del procesador"""

    def test_processor_initialization_default_config(self):
        """Test que la inicialización usa valores de config"""
        processor = VideoProcessor()

        assert hasattr(processor, 'max_duration')
        assert hasattr(processor, 'width')
        assert hasattr(processor, 'height')
        assert hasattr(processor, 'codec')
        assert hasattr(processor, 'preset')
        assert hasattr(processor, 'crf')

    def test_processor_singleton_exists(self):
        """Test que existe la instancia singleton"""
        from utils.video_processing import video_processor

        assert video_processor is not None
        assert isinstance(video_processor, VideoProcessor)


class TestVideoProcessingErrorException:
    """Tests para la excepción personalizada"""

    def test_video_processing_error_creation(self):
        """Test crear excepción VideoProcessingError"""
        error = VideoProcessingError("Test error message")
        assert str(error) == "Test error message"

    def test_video_processing_error_inheritance(self):
        """Test que VideoProcessingError hereda de Exception"""
        error = VideoProcessingError("Test")
        assert isinstance(error, Exception)

    def test_video_processing_error_can_be_raised(self):
        """Test que se puede lanzar y capturar VideoProcessingError"""
        with pytest.raises(VideoProcessingError) as exc_info:
            raise VideoProcessingError("Custom error")

        assert "Custom error" in str(exc_info.value)


class TestEdgeCasesAndIntegration:
    """Tests de casos extremos e integración"""

    @pytest.fixture
    def processor(self):
        return VideoProcessor()

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_very_short_video(self, mock_probe, mock_exists, processor):
        """Test video muy corto (menos de 1 segundo)"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264',
                'r_frame_rate': '30/1'
            }],
            'format': {
                'duration': '0.5',
                'size': '102400'
            }
        }

        info = processor.get_video_info('/fake/short.mp4')
        assert abs(info['duration'] - 0.5) < 0.001
        assert info['size_bytes'] == 102400

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_very_large_video(self, mock_probe, mock_exists, processor):
        """Test video muy grande (varios GB)"""
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'video',
                'width': 3840,
                'height': 2160,
                'codec_name': 'h265',
                'r_frame_rate': '60/1'
            }],
            'format': {
                'duration': '30.0',
                'size': str(5 * 1024 * 1024 * 1024)  # 5 GB
            }
        }

        info = processor.get_video_info('/fake/large.mp4')
        assert info['size_bytes'] == 5 * 1024 * 1024 * 1024

    @patch('os.path.exists', return_value=True)
    @patch('ffmpeg.probe')
    def test_different_codecs(self, mock_probe, mock_exists, processor):
        """Test diferentes códecs de video"""
        codecs = ['h264', 'h265', 'vp9', 'av1', 'mpeg4']

        for codec in codecs:
            mock_probe.return_value = {
                'streams': [{
                    'codec_type': 'video',
                    'width': 1920,
                    'height': 1080,
                    'codec_name': codec,
                    'r_frame_rate': '30/1'
                }],
                'format': {
                    'duration': '30.0',
                    'size': '5242880'
                }
            }

            info = processor.get_video_info('/fake/video.mp4')
            assert info['codec'] == codec


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
