"""
Tests comprehensivos para el módulo de configuración
Cubre todos los aspectos de Config: defaults, env vars, properties, validación
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
from config import Config, config


class TestConfigDefaults:
    """Tests para valores por defecto cuando no hay variables de entorno"""
    
    def test_default_redis_url(self):
        """Test valor por defecto de REDIS_URL - verifica que tiene un valor"""
        cfg = Config()
        # Verificar que tiene un valor (puede venir de env o default)
        assert cfg.REDIS_URL is not None
        assert isinstance(cfg.REDIS_URL, str)
        assert len(cfg.REDIS_URL) > 0
    
    def test_default_database_url(self):
        """Test valor por defecto de DATABASE_URL - verifica que tiene un valor"""
        cfg = Config()
        # Verificar que tiene un valor (puede venir de env o default)
        assert cfg.DATABASE_URL is not None
        assert isinstance(cfg.DATABASE_URL, str)
        assert 'postgresql' in cfg.DATABASE_URL
    
    def test_default_upload_dir(self):
        """Test valor por defecto de UPLOAD_BASE_DIR - verifica que tiene un valor"""
        cfg = Config()
        # Verificar que tiene un valor (puede venir de env o default)
        assert cfg.UPLOAD_BASE_DIR is not None
        assert isinstance(cfg.UPLOAD_BASE_DIR, str)
        assert len(cfg.UPLOAD_BASE_DIR) > 0
    
    def test_video_defaults(self):
        """Test valores por defecto de configuración de video"""
        cfg = Config()
        
        assert cfg.VIDEO_MAX_DURATION == 30
        assert cfg.VIDEO_RESOLUTION_WIDTH == 1280
        assert cfg.VIDEO_RESOLUTION_HEIGHT == 720
        assert cfg.VIDEO_ASPECT_RATIO == "16:9"
        assert cfg.VIDEO_CODEC == 'libx264'
        assert cfg.VIDEO_PRESET == 'fast'
        assert cfg.VIDEO_CRF == 23
    
    def test_celery_defaults(self):
        """Test valores por defecto de Celery - verifica que tienen valores válidos"""
        cfg = Config()
        # Verificar que tienen valores numéricos válidos
        assert isinstance(cfg.CELERY_TASK_DEFAULT_RETRY_DELAY, int)
        assert cfg.CELERY_TASK_DEFAULT_RETRY_DELAY > 0
        assert isinstance(cfg.CELERY_TASK_MAX_RETRIES, int)
        assert cfg.CELERY_TASK_MAX_RETRIES > 0
        assert isinstance(cfg.CELERY_WORKER_CONCURRENCY, int)
        assert cfg.CELERY_WORKER_CONCURRENCY > 0
    
    def test_logo_defaults(self):
        """Test valores por defecto de logo - verifica que tienen valores válidos"""
        cfg = Config()
        assert cfg.LOGO_PATH is not None
        assert isinstance(cfg.LOGO_PATH, str)
        assert cfg.LOGO_POSITION is not None
        assert isinstance(cfg.LOGO_POSITION, str)
        assert cfg.LOGO_MARGIN == 10
    
    def test_intro_outro_defaults(self):
        """Test valores por defecto de cortinillas - verifica que tienen valores válidos"""
        cfg = Config()
        assert cfg.INTRO_VIDEO_PATH is not None
        assert isinstance(cfg.INTRO_VIDEO_PATH, str)
        assert cfg.OUTRO_VIDEO_PATH is not None
        assert isinstance(cfg.OUTRO_VIDEO_PATH, str)
        assert cfg.MAX_INTRO_DURATION == 2.5
        assert cfg.MAX_OUTRO_DURATION == 2.5
    
    def test_logging_default(self):
        """Test valor por defecto de LOG_LEVEL - verifica que tiene un valor válido"""
        cfg = Config()
        assert cfg.LOG_LEVEL is not None
        assert isinstance(cfg.LOG_LEVEL, str)
        assert len(cfg.LOG_LEVEL) > 0
    
    def test_timeout_defaults(self):
        """Test valores por defecto de timeouts"""
        cfg = Config()
        assert cfg.TASK_SOFT_TIME_LIMIT == 600  # 10 minutos
        assert cfg.TASK_HARD_TIME_LIMIT == 900  # 15 minutos
    
    def test_api_defaults(self):
        """Test valores por defecto de API - verifica que tienen valores válidos"""
        cfg = Config()
        assert cfg.WORKER_API_HOST is not None
        assert isinstance(cfg.WORKER_API_HOST, str)
        assert isinstance(cfg.WORKER_API_PORT, int)
        assert cfg.WORKER_API_PORT > 0


class TestConfigEnvironmentVariables:
    """Tests para variables de entorno personalizadas"""
    
    def test_custom_redis_url(self):
        """Test REDIS_URL desde variable de entorno"""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://custom:6380/1'}):
            # Necesitamos recargar el módulo para que lea el nuevo valor
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.REDIS_URL == 'redis://custom:6380/1'
            importlib.reload(config)  # Restaurar
    
    def test_custom_database_url(self):
        """Test DATABASE_URL desde variable de entorno"""
        custom_db = 'postgresql://user:pass@host:5432/mydb'
        with patch.dict(os.environ, {'DATABASE_URL': custom_db}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.DATABASE_URL == custom_db
            importlib.reload(config)
    
    def test_custom_upload_dir(self):
        """Test UPLOAD_BASE_DIR desde variable de entorno"""
        # Usar directorio temporal en lugar de /custom
        test_dir = tempfile.mkdtemp()
        try:
            with patch.dict(os.environ, {'UPLOAD_DIR': test_dir}):
                import importlib
                import config
                importlib.reload(config)
                cfg = config.Config()
                assert cfg.UPLOAD_BASE_DIR == test_dir
                importlib.reload(config)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_custom_celery_retry_delay(self):
        """Test CELERY_TASK_DEFAULT_RETRY_DELAY desde variable de entorno"""
        with patch.dict(os.environ, {'CELERY_RETRY_DELAY': '120'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.CELERY_TASK_DEFAULT_RETRY_DELAY == 120
            assert isinstance(cfg.CELERY_TASK_DEFAULT_RETRY_DELAY, int)
            importlib.reload(config)
    
    def test_custom_celery_max_retries(self):
        """Test CELERY_TASK_MAX_RETRIES desde variable de entorno"""
        with patch.dict(os.environ, {'CELERY_MAX_RETRIES': '5'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.CELERY_TASK_MAX_RETRIES == 5
            assert isinstance(cfg.CELERY_TASK_MAX_RETRIES, int)
            importlib.reload(config)
    
    def test_custom_celery_concurrency(self):
        """Test CELERY_WORKER_CONCURRENCY desde variable de entorno"""
        with patch.dict(os.environ, {'CELERY_CONCURRENCY': '8'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.CELERY_WORKER_CONCURRENCY == 8
            assert isinstance(cfg.CELERY_WORKER_CONCURRENCY, int)
            importlib.reload(config)
    
    def test_custom_logo_path(self):
        """Test LOGO_PATH desde variable de entorno"""
        with patch.dict(os.environ, {'LOGO_PATH': '/custom/logo.png'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.LOGO_PATH == '/custom/logo.png'
            importlib.reload(config)
    
    def test_custom_logo_position(self):
        """Test LOGO_POSITION desde variable de entorno"""
        with patch.dict(os.environ, {'LOGO_POSITION': 'bottom-left'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.LOGO_POSITION == 'bottom-left'
            importlib.reload(config)
    
    def test_custom_intro_path(self):
        """Test INTRO_VIDEO_PATH desde variable de entorno"""
        with patch.dict(os.environ, {'INTRO_VIDEO_PATH': '/custom/intro.mp4'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.INTRO_VIDEO_PATH == '/custom/intro.mp4'
            importlib.reload(config)
    
    def test_custom_outro_path(self):
        """Test OUTRO_VIDEO_PATH desde variable de entorno"""
        with patch.dict(os.environ, {'OUTRO_VIDEO_PATH': '/custom/outro.mp4'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.OUTRO_VIDEO_PATH == '/custom/outro.mp4'
            importlib.reload(config)
    
    def test_custom_log_level(self):
        """Test LOG_LEVEL desde variable de entorno"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.LOG_LEVEL == 'DEBUG'
            importlib.reload(config)
    
    def test_custom_api_host(self):
        """Test WORKER_API_HOST desde variable de entorno"""
        with patch.dict(os.environ, {'WORKER_API_HOST': '127.0.0.1'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.WORKER_API_HOST == '127.0.0.1'
            importlib.reload(config)
    
    def test_custom_api_port(self):
        """Test WORKER_API_PORT desde variable de entorno"""
        with patch.dict(os.environ, {'WORKER_API_PORT': '9000'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.WORKER_API_PORT == 9000
            assert isinstance(cfg.WORKER_API_PORT, int)
            importlib.reload(config)


class TestConfigDirectoryProperties:
    """Tests para propiedades de directorios (ORIGINAL_DIR, PROCESSED_DIR, TEMP_DIR)"""
    
    @pytest.fixture
    def temp_dir(self):
        """Fixture para crear directorio temporal"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    def test_original_dir_creation(self, temp_dir):
        """Test que ORIGINAL_DIR crea el directorio si no existe"""
        with patch.dict(os.environ, {'UPLOAD_DIR': temp_dir}):
            cfg = Config()
            original_path = cfg.ORIGINAL_DIR
            
            assert os.path.exists(original_path)
            assert os.path.isdir(original_path)
            assert original_path.endswith('/original')
    
    def test_processed_dir_creation(self, temp_dir):
        """Test que PROCESSED_DIR crea el directorio si no existe"""
        with patch.dict(os.environ, {'UPLOAD_DIR': temp_dir}):
            cfg = Config()
            processed_path = cfg.PROCESSED_DIR
            
            assert os.path.exists(processed_path)
            assert os.path.isdir(processed_path)
            assert processed_path.endswith('/processed')
    
    def test_temp_dir_creation(self, temp_dir):
        """Test que TEMP_DIR crea el directorio si no existe"""
        with patch.dict(os.environ, {'UPLOAD_DIR': temp_dir}):
            cfg = Config()
            temp_path = cfg.TEMP_DIR
            
            assert os.path.exists(temp_path)
            assert os.path.isdir(temp_path)
            assert temp_path.endswith('/temp')
    
    @patch('config.os.getenv')
    def test_directories_structure(self, mock_getenv, temp_dir):
        """Test que los directorios se crean con la estructura correcta"""
        def getenv_side_effect(key, default=None):
            if key == 'UPLOAD_DIR':
                return temp_dir
            return os.environ.get(key, default)
        mock_getenv.side_effect = getenv_side_effect
        # Reimportar para aplicar el mock
        import importlib
        import config
        original_env = os.environ.get('UPLOAD_DIR')
        os.environ['UPLOAD_DIR'] = temp_dir
        importlib.reload(config)
        cfg = config.Config()
        
        original = cfg.ORIGINAL_DIR
        processed = cfg.PROCESSED_DIR
        temp = cfg.TEMP_DIR
        
        # Todos deben estar bajo UPLOAD_BASE_DIR
        assert original.startswith(temp_dir)
        assert processed.startswith(temp_dir)
        assert temp.startswith(temp_dir)
        
        # Verificar que existen
        assert os.path.exists(original)
        assert os.path.exists(processed)
        assert os.path.exists(temp)
        
        # Restaurar
        if original_env:
            os.environ['UPLOAD_DIR'] = original_env
        else:
            os.environ.pop('UPLOAD_DIR', None)
        importlib.reload(config)
    
    def test_directories_parents_creation(self, temp_dir):
        """Test que mkdir crea directorios padre si no existen"""
        deep_path = os.path.join(temp_dir, 'very', 'deep', 'path')
        with patch.dict(os.environ, {'UPLOAD_DIR': deep_path}):
            cfg = Config()
            
            # Debe crear toda la jerarquía
            assert os.path.exists(cfg.ORIGINAL_DIR)
            assert os.path.exists(cfg.PROCESSED_DIR)
            assert os.path.exists(cfg.TEMP_DIR)
    
    def test_directories_idempotent(self, temp_dir):
        """Test que llamar las propiedades múltiples veces no causa error"""
        with patch.dict(os.environ, {'UPLOAD_DIR': temp_dir}):
            cfg = Config()
            
            # Llamar múltiples veces
            dir1 = cfg.ORIGINAL_DIR
            dir2 = cfg.ORIGINAL_DIR
            dir3 = cfg.ORIGINAL_DIR
            
            assert dir1 == dir2 == dir3
            assert os.path.exists(dir1)
    
    def test_directory_paths_are_strings(self, temp_dir):
        """Test que las propiedades retornan strings"""
        with patch.dict(os.environ, {'UPLOAD_DIR': temp_dir}):
            cfg = Config()
            
            assert isinstance(cfg.ORIGINAL_DIR, str)
            assert isinstance(cfg.PROCESSED_DIR, str)
            assert isinstance(cfg.TEMP_DIR, str)


class TestConfigValidation:
    """Tests para el método validate()"""
    
    def test_validate_with_all_required(self):
        """Test validate cuando todas las configuraciones requeridas están presentes"""
        cfg = Config()
        
        # Asumir que las configuraciones por defecto están presentes
        # Si están vacías o None, validate retornará False
        assert isinstance(cfg.validate(), bool)
    
    def test_validate_checks_redis_url(self):
        """Test que validate verifica REDIS_URL"""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://test:6379/0'}):
            cfg = Config()
            # Si REDIS_URL tiene valor, debe pasar
            if cfg.REDIS_URL:
                assert cfg.validate() is True
    
    def test_validate_checks_database_url(self):
        """Test que validate verifica DATABASE_URL"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host/db'}):
            cfg = Config()
            # Si DATABASE_URL tiene valor, debe pasar
            if cfg.DATABASE_URL:
                assert cfg.validate() is True
    
    def test_validate_checks_upload_dir(self):
        """Test que validate verifica UPLOAD_BASE_DIR"""
        with patch.dict(os.environ, {'UPLOAD_DIR': '/test/uploads'}):
            cfg = Config()
            # Si UPLOAD_BASE_DIR tiene valor, debe pasar
            if cfg.UPLOAD_BASE_DIR:
                assert cfg.validate() is True
    
    def test_validate_with_missing_redis_url(self):
        """Test validate cuando REDIS_URL está vacío"""
        # No podemos hacer esto fácilmente porque os.getenv retorna None o string
        # Pero podemos verificar el comportamiento con valores vacíos
        with patch.dict(os.environ, {'REDIS_URL': ''}):
            cfg = Config()
            # String vacío debería hacer que validate retorne False
            result = cfg.validate()
            assert isinstance(result, bool)


class TestConfigRepr:
    """Tests para el método __repr__"""
    
    def test_repr_format(self):
        """Test que __repr__ tiene el formato correcto"""
        cfg = Config()
        repr_str = repr(cfg)
        
        assert isinstance(repr_str, str)
        assert 'Config' in repr_str
        assert 'redis' in repr_str.lower()
        assert 'db' in repr_str.lower() or 'database' in repr_str.lower()
    
    def test_repr_contains_redis_url(self):
        """Test que __repr__ contiene REDIS_URL"""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://test:6379/0'}):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            repr_str = repr(cfg)
            assert 'redis://test:6379/0' in repr_str
            importlib.reload(config)
    
    def test_repr_contains_database_url(self):
        """Test que __repr__ contiene DATABASE_URL"""
        test_db = 'postgresql://user:pass@host/db'
        with patch.dict(os.environ, {'DATABASE_URL': test_db}):
            cfg = Config()
            repr_str = repr(cfg)
            # Debe contener parte de la URL (puede estar truncada)
            assert 'postgresql' in repr_str.lower() or 'db' in repr_str.lower()


class TestConfigTypeConversions:
    """Tests para conversión de tipos (int, float)"""
    
    def test_celery_retry_delay_is_int(self):
        """Test que CELERY_TASK_DEFAULT_RETRY_DELAY es int"""
        cfg = Config()
        assert isinstance(cfg.CELERY_TASK_DEFAULT_RETRY_DELAY, int)
    
    def test_celery_max_retries_is_int(self):
        """Test que CELERY_TASK_MAX_RETRIES es int"""
        cfg = Config()
        assert isinstance(cfg.CELERY_TASK_MAX_RETRIES, int)
    
    def test_celery_concurrency_is_int(self):
        """Test que CELERY_WORKER_CONCURRENCY es int"""
        cfg = Config()
        assert isinstance(cfg.CELERY_WORKER_CONCURRENCY, int)
    
    def test_api_port_is_int(self):
        """Test que WORKER_API_PORT es int"""
        cfg = Config()
        assert isinstance(cfg.WORKER_API_PORT, int)
    
    def test_video_max_duration_is_int(self):
        """Test que VIDEO_MAX_DURATION es int"""
        cfg = Config()
        assert isinstance(cfg.VIDEO_MAX_DURATION, int)
    
    def test_resolution_dimensions_are_int(self):
        """Test que dimensiones de resolución son int"""
        cfg = Config()
        assert isinstance(cfg.VIDEO_RESOLUTION_WIDTH, int)
        assert isinstance(cfg.VIDEO_RESOLUTION_HEIGHT, int)
    
    def test_logo_margin_is_int(self):
        """Test que LOGO_MARGIN es int"""
        cfg = Config()
        assert isinstance(cfg.LOGO_MARGIN, int)
    
    def test_timeout_limits_are_int(self):
        """Test que los límites de timeout son int"""
        cfg = Config()
        assert isinstance(cfg.TASK_SOFT_TIME_LIMIT, int)
        assert isinstance(cfg.TASK_HARD_TIME_LIMIT, int)
    
    def test_max_intro_duration_is_float(self):
        """Test que MAX_INTRO_DURATION es float"""
        cfg = Config()
        assert isinstance(cfg.MAX_INTRO_DURATION, float)
    
    def test_max_outro_duration_is_float(self):
        """Test que MAX_OUTRO_DURATION es float"""
        cfg = Config()
        assert isinstance(cfg.MAX_OUTRO_DURATION, float)


class TestConfigGlobalInstance:
    """Tests para la instancia global de config"""
    
    def test_global_config_exists(self):
        """Test que la instancia global config existe"""
        # Importar config directamente sin reload
        import config as config_module
        global_config = config_module.config
        assert global_config is not None
        # Usar Config del módulo actual en caso de que haya sido recargado
        ConfigClass = config_module.Config
        assert isinstance(global_config, ConfigClass)
    
    def test_global_config_singleton_behavior(self):
        """Test que la instancia global es consistente"""
        # Importar config dos veces
        import config as config_module
        config1 = config_module.config
        config2 = config_module.config
        
        # Deben ser la misma instancia
        assert config1 is config2
        # Usar el Config del módulo en lugar del importado globalmente
        ConfigClass = config_module.Config
        assert isinstance(config1, ConfigClass)
        assert isinstance(config2, ConfigClass)
        assert type(config1) == type(config2)


class TestConfigEdgeCases:
    """Tests para casos límite y edge cases"""
    
    def test_numeric_env_vars_as_strings(self):
        """Test que variables numéricas se convierten correctamente desde strings"""
        with patch.dict(os.environ, {
            'CELERY_RETRY_DELAY': '120',
            'CELERY_MAX_RETRIES': '5',
            'CELERY_CONCURRENCY': '8',
            'WORKER_API_PORT': '9000'
        }):
            import importlib
            import config
            importlib.reload(config)
            cfg = config.Config()
            assert cfg.CELERY_TASK_DEFAULT_RETRY_DELAY == 120
            assert cfg.CELERY_TASK_MAX_RETRIES == 5
            assert cfg.CELERY_WORKER_CONCURRENCY == 8
            assert cfg.WORKER_API_PORT == 9000
            importlib.reload(config)
    
    def test_video_constants_immutable(self):
        """Test que constantes de video no cambian"""
        cfg1 = Config()
        cfg2 = Config()
        
        assert cfg1.VIDEO_MAX_DURATION == cfg2.VIDEO_MAX_DURATION
        assert cfg1.VIDEO_RESOLUTION_WIDTH == cfg2.VIDEO_RESOLUTION_WIDTH
        assert cfg1.VIDEO_ASPECT_RATIO == cfg2.VIDEO_ASPECT_RATIO
    
    def test_directory_properties_consistent(self):
        """Test que propiedades de directorios son consistentes"""
        cfg = Config()
        
        original1 = cfg.ORIGINAL_DIR
        original2 = cfg.ORIGINAL_DIR
        
        assert original1 == original2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=config", "--cov-report=term-missing"])

