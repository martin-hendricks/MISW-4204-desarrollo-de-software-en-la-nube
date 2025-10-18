"""
Tests básicos para el módulo de configuración
"""
import pytest
from config import Config, config


class TestConfig:
    """Tests básicos de configuración"""
    
    def test_default_values(self):
        """Test valores por defecto"""
        cfg = Config()
        
        assert cfg.VIDEO_MAX_DURATION == 30
        assert cfg.VIDEO_RESOLUTION_WIDTH == 1280
        assert cfg.VIDEO_RESOLUTION_HEIGHT == 720
        assert cfg.VIDEO_CODEC == 'libx264'
        assert cfg.CELERY_TASK_MAX_RETRIES == 3
    
    def test_directory_properties(self):
        """Test propiedades de directorios"""
        cfg = Config()
        
        assert '/original' in cfg.ORIGINAL_DIR
        assert '/processed' in cfg.PROCESSED_DIR
        assert '/temp' in cfg.TEMP_DIR
    
    def test_video_config(self):
        """Test configuración de video"""
        cfg = Config()
        
        assert cfg.VIDEO_ASPECT_RATIO == "16:9"
        assert cfg.VIDEO_PRESET == "fast"
        assert cfg.VIDEO_CRF == 23
    
    def test_global_config(self):
        """Test instancia global de config"""
        assert config is not None
        assert isinstance(config, Config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

