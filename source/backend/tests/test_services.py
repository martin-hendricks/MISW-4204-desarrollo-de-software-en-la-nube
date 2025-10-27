"""Tests para los servicios de aplicación"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from app.services.player_service import PlayerService
from app.services.video_service import VideoService
from app.domain.entities.player import Player
from app.domain.entities.video import Video, VideoStatus
from app.domain.entities.vote import Vote
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.shared.exceptions.player_exceptions import PlayerAlreadyExistsException, PlayerNotFoundException
from app.shared.exceptions.video_exceptions import VideoNotFoundException, VideoNotOwnedException


class TestPlayerService:
    """Tests para PlayerService"""

    @pytest.fixture
    def mock_player_repository(self):
        """Mock del repositorio de jugadores"""
        return AsyncMock()

    @pytest.fixture
    def mock_auth_service(self):
        """Mock del servicio de autenticación"""
        return AsyncMock()

    @pytest.fixture
    def player_service(self, mock_player_repository, mock_auth_service):
        """Instancia del servicio de jugadores con mocks"""
        return PlayerService(mock_player_repository, mock_auth_service)

    @pytest.mark.asyncio
    async def test_register_player_success(self, player_service, mock_player_repository, mock_auth_service):
        """Test para registro exitoso de jugador"""
        # Arrange
        mock_player_repository.get_by_email.return_value = None
        mock_auth_service.hash_password.return_value = "$2b$12$hashed..."

        expected_player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.create.return_value = expected_player

        # Act
        result = await player_service.register_player(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            password="password123",
            city="Bogotá",
            country="Colombia"
        )

        # Assert
        assert result.id == 1
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        mock_player_repository.get_by_email.assert_called_once()
        mock_auth_service.hash_password.assert_called_once_with("password123")
        mock_player_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_player_duplicate_email(self, player_service, mock_player_repository):
        """Test para registro con email duplicado"""
        # Arrange
        existing_player = Player(
            id=1,
            first_name="Existing",
            last_name="Player",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.get_by_email.return_value = existing_player

        # Act & Assert
        with pytest.raises(PlayerAlreadyExistsException, match="ya está registrado"):
            await player_service.register_player(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                password="password123",
                city="Bogotá",
                country="Colombia"
            )

    @pytest.mark.asyncio
    async def test_authenticate_player_success(self, player_service, mock_player_repository, mock_auth_service):
        """Test para autenticación exitosa de jugador"""
        # Arrange
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.get_by_email.return_value = player
        mock_auth_service.verify_password.return_value = True

        # Act
        result = await player_service.authenticate_player("john.doe@example.com", "password123")

        # Assert
        assert result is not None
        assert result.id == 1
        mock_player_repository.get_by_email.assert_called_once()
        mock_auth_service.verify_password.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_player_wrong_password(self, player_service, mock_player_repository, mock_auth_service):
        """Test para autenticación con contraseña incorrecta"""
        # Arrange
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.get_by_email.return_value = player
        mock_auth_service.verify_password.return_value = False

        # Act
        result = await player_service.authenticate_player("john.doe@example.com", "wrongpassword")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_player_nonexistent_email(self, player_service, mock_player_repository):
        """Test para autenticación con email inexistente"""
        # Arrange
        mock_player_repository.get_by_email.return_value = None

        # Act
        result = await player_service.authenticate_player("nonexistent@example.com", "password123")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_access_token(self, player_service, mock_auth_service):
        """Test para generación de token de acceso"""
        # Arrange
        mock_auth_service.create_player_token.return_value = "jwt.token.here"

        # Act
        result = await player_service.generate_access_token(1)

        # Assert
        assert result == "jwt.token.here"
        mock_auth_service.create_player_token.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_player_by_id_success(self, player_service, mock_player_repository):
        """Test para obtener jugador por ID exitosamente"""
        # Arrange
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.get_by_id.return_value = player

        # Act
        result = await player_service.get_player_by_id(1)

        # Assert
        assert result.id == 1
        assert result.first_name == "John"
        mock_player_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_player_by_id_not_found(self, player_service, mock_player_repository):
        """Test para obtener jugador por ID que no existe"""
        # Arrange
        mock_player_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(PlayerNotFoundException, match="no encontrado"):
            await player_service.get_player_by_id(999)

    @pytest.mark.asyncio
    async def test_update_player_profile(self, player_service, mock_player_repository):
        """Test para actualizar perfil de jugador"""
        # Arrange
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        updated_player = Player(
            id=1,
            first_name="Jane",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Medellín",
            country="Colombia"
        )
        mock_player_repository.get_by_id.return_value = player
        mock_player_repository.update.return_value = updated_player

        # Act
        result = await player_service.update_player_profile(1, first_name="Jane", city="Medellín")

        # Assert
        assert result.first_name == "Jane"
        assert result.city == "Medellín"
        mock_player_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_player(self, player_service, mock_player_repository):
        """Test para desactivar jugador"""
        # Arrange
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        mock_player_repository.get_by_id.return_value = player
        mock_player_repository.update.return_value = player

        # Act
        result = await player_service.deactivate_player(1)

        # Assert
        mock_player_repository.update.assert_called_once()


class TestVideoService:
    """Tests para VideoService"""

    @pytest.fixture
    def mock_video_repository(self):
        """Mock del repositorio de videos"""
        return AsyncMock()

    @pytest.fixture
    def mock_vote_repository(self):
        """Mock del repositorio de votos"""
        return AsyncMock()

    @pytest.fixture
    def mock_file_storage(self):
        """Mock del almacenamiento de archivos"""
        return AsyncMock()

    @pytest.fixture
    def mock_task_queue(self):
        """Mock de la cola de tareas"""
        return AsyncMock()

    @pytest.fixture
    def video_service(self, mock_video_repository, mock_vote_repository, mock_file_storage, mock_task_queue):
        """Instancia del servicio de videos con mocks"""
        return VideoService(mock_video_repository, mock_vote_repository, mock_file_storage, mock_task_queue)

    @pytest.mark.asyncio
    async def test_get_player_videos(self, video_service, mock_video_repository):
        """Test para obtener videos de un jugador"""
        # Arrange
        videos = [
            Video(
                id=1,
                player_id=1,
                title="Video 1",
                status=VideoStatus.UPLOADED,
                uploaded_at=datetime.now()
            ),
            Video(
                id=2,
                player_id=1,
                title="Video 2",
                status=VideoStatus.PROCESSED,
                uploaded_at=datetime.now()
            )
        ]
        mock_video_repository.get_by_player.return_value = videos

        # Act
        result = await video_service.get_player_videos(1)

        # Assert
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_video_repository.get_by_player.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_video_success(self, video_service, mock_video_repository):
        """Test para obtener un video exitosamente"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video

        # Act
        result = await video_service.get_video(1, 1)

        # Assert
        assert result.id == 1
        assert result.player_id == 1
        mock_video_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_video_not_found(self, video_service, mock_video_repository):
        """Test para obtener un video que no existe"""
        # Arrange
        mock_video_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(VideoNotFoundException, match="no encontrado"):
            await video_service.get_video(999, 1)

    @pytest.mark.asyncio
    async def test_get_video_not_owned(self, video_service, mock_video_repository):
        """Test para obtener un video que no pertenece al jugador"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video

        # Act & Assert
        with pytest.raises(VideoNotOwnedException, match="No tienes permisos"):
            await video_service.get_video(1, 2)  # player_id diferente

    @pytest.mark.asyncio
    async def test_get_public_videos(self, video_service, mock_video_repository):
        """Test para obtener videos públicos"""
        # Arrange
        videos = [
            Video(
                id=1,
                player_id=1,
                title="Video 1",
                status=VideoStatus.PROCESSED,
                uploaded_at=datetime.now()
            )
        ]
        mock_video_repository.get_public_videos.return_value = videos

        # Act
        result = await video_service.get_public_videos()

        # Assert
        assert len(result) == 1
        assert result[0].id == 1
        mock_video_repository.get_public_videos.assert_called_once()

    @pytest.mark.asyncio
    async def test_vote_for_video_success(self, video_service, mock_video_repository, mock_vote_repository):
        """Test para votar por un video exitosamente"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.PROCESSED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video
        mock_vote_repository.has_user_voted.return_value = False
        mock_vote_repository.create.return_value = Vote(id=1, video_id=1, player_id=2)

        # Act
        result = await video_service.vote_for_video(1, 2)

        # Assert
        assert result is True
        mock_video_repository.get_by_id.assert_called_once_with(1)
        mock_vote_repository.has_user_voted.assert_called_once_with(1, 2)
        mock_vote_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_vote_for_own_video(self, video_service, mock_video_repository):
        """Test para intentar votar por el propio video"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.PROCESSED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video

        # Act & Assert
        with pytest.raises(ValueError, match="No puedes votar por tu propio video"):
            await video_service.vote_for_video(1, 1)  # mismo player_id

    @pytest.mark.asyncio
    async def test_vote_for_video_duplicate(self, video_service, mock_video_repository, mock_vote_repository):
        """Test para intentar votar dos veces por el mismo video"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.PROCESSED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video
        mock_vote_repository.has_user_voted.return_value = True

        # Act & Assert
        with pytest.raises(ValueError, match="Ya has votado"):
            await video_service.vote_for_video(1, 2)

    @pytest.mark.asyncio
    async def test_get_video_votes_count(self, video_service, mock_vote_repository):
        """Test para obtener el conteo de votos de un video"""
        # Arrange
        mock_vote_repository.count_votes_for_video.return_value = 5

        # Act
        result = await video_service.get_video_votes_count(1)

        # Assert
        assert result == 5
        mock_vote_repository.count_votes_for_video.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_mark_video_as_processed(self, video_service, mock_video_repository):
        """Test para marcar un video como procesado"""
        # Arrange
        video = Video(
            id=1,
            player_id=1,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        mock_video_repository.get_by_id.return_value = video
        mock_video_repository.update.return_value = video

        # Act
        await video_service.mark_video_as_processed(1, "/videos/processed/1")

        # Assert
        mock_video_repository.get_by_id.assert_called_once_with(1)
        mock_video_repository.update.assert_called_once()
