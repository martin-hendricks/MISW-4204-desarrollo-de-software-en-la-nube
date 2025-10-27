"""Tests de integración para los repositorios"""

import pytest
from datetime import datetime
from app.infrastructure.repositories.player_repository import PlayerRepository
from app.infrastructure.repositories.video_repository import VideoRepository
from app.infrastructure.repositories.vote_repository import VoteRepository
from app.domain.entities.player import Player
from app.domain.entities.video import Video, VideoStatus
from app.domain.entities.vote import Vote
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password


class TestPlayerRepository:
    """Tests de integración para PlayerRepository"""

    @pytest.mark.asyncio
    async def test_create_player(self, db_session):
        """Test para crear un jugador en la base de datos"""
        # Arrange
        repository = PlayerRepository(db_session)
        player = Player(
            id=None,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe.repo@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )

        # Act
        created_player = await repository.create(player)

        # Assert
        assert created_player.id is not None
        assert created_player.first_name == "John"
        assert created_player.last_name == "Doe"
        assert created_player.email.value == "john.doe.repo@example.com"

    @pytest.mark.asyncio
    async def test_get_player_by_id(self, db_session):
        """Test para obtener un jugador por ID"""
        # Arrange
        repository = PlayerRepository(db_session)
        player = Player(
            id=None,
            first_name="Jane",
            last_name="Smith",
            email=Email("jane.smith.repo@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Medellín",
            country="Colombia"
        )
        created_player = await repository.create(player)

        # Act
        found_player = await repository.get_by_id(created_player.id)

        # Assert
        assert found_player is not None
        assert found_player.id == created_player.id
        assert found_player.first_name == "Jane"
        assert found_player.last_name == "Smith"

    @pytest.mark.asyncio
    async def test_get_player_by_email(self, db_session):
        """Test para obtener un jugador por email"""
        # Arrange
        repository = PlayerRepository(db_session)
        email = Email("test.repo@example.com")
        player = Player(
            id=None,
            first_name="Test",
            last_name="User",
            email=email,
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Cali",
            country="Colombia"
        )
        await repository.create(player)

        # Act
        found_player = await repository.get_by_email(email)

        # Assert
        assert found_player is not None
        assert found_player.email == email
        assert found_player.first_name == "Test"

    @pytest.mark.asyncio
    async def test_update_player(self, db_session):
        """Test para actualizar un jugador"""
        # Arrange
        repository = PlayerRepository(db_session)
        player = Player(
            id=None,
            first_name="Original",
            last_name="Name",
            email=Email("update.test@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        created_player = await repository.create(player)

        # Act
        created_player.first_name = "Updated"
        created_player.city = "Medellín"
        updated_player = await repository.update(created_player)

        # Assert
        assert updated_player.first_name == "Updated"
        assert updated_player.city == "Medellín"
        assert updated_player.last_name == "Name"  # No cambió

    @pytest.mark.asyncio
    async def test_get_player_by_id_not_found(self, db_session):
        """Test para obtener un jugador que no existe"""
        # Arrange
        repository = PlayerRepository(db_session)

        # Act
        found_player = await repository.get_by_id(999999)

        # Assert
        assert found_player is None


class TestVideoRepository:
    """Tests de integración para VideoRepository"""

    @pytest.mark.asyncio
    async def test_create_video(self, db_session, test_player):
        """Test para crear un video en la base de datos"""
        # Arrange
        repository = VideoRepository(db_session)
        video = Video(
            id=None,
            player_id=test_player.id,
            title="Test Video",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )

        # Act
        created_video = await repository.create(video)

        # Assert
        assert created_video.id is not None
        assert created_video.title == "Test Video"
        assert created_video.player_id == test_player.id
        assert created_video.status == VideoStatus.UPLOADED

    @pytest.mark.asyncio
    async def test_get_video_by_id(self, db_session, test_video):
        """Test para obtener un video por ID"""
        # Arrange
        repository = VideoRepository(db_session)

        # Act
        found_video = await repository.get_by_id(test_video.id)

        # Assert
        assert found_video is not None
        assert found_video.id == test_video.id
        assert found_video.title == test_video.title

    @pytest.mark.asyncio
    async def test_get_videos_by_player(self, db_session, test_player):
        """Test para obtener videos de un jugador"""
        # Arrange
        repository = VideoRepository(db_session)
        video1 = Video(
            id=None,
            player_id=test_player.id,
            title="Video 1",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        video2 = Video(
            id=None,
            player_id=test_player.id,
            title="Video 2",
            status=VideoStatus.PROCESSED,
            uploaded_at=datetime.now()
        )
        await repository.create(video1)
        await repository.create(video2)

        # Act
        videos = await repository.get_by_player(test_player.id)

        # Assert
        assert len(videos) >= 2  # Puede haber más si test_video fixture se ejecutó
        player_videos = [v for v in videos if v.player_id == test_player.id]
        assert len(player_videos) >= 2

    @pytest.mark.asyncio
    async def test_update_video(self, db_session, test_video):
        """Test para actualizar un video"""
        # Arrange
        repository = VideoRepository(db_session)

        # Act
        test_video.title = "Updated Title"
        test_video.status = VideoStatus.PROCESSED
        updated_video = await repository.update(test_video)

        # Assert
        assert updated_video.title == "Updated Title"
        assert updated_video.status == VideoStatus.PROCESSED

    @pytest.mark.asyncio
    async def test_delete_video(self, db_session, test_player):
        """Test para eliminar un video"""
        # Arrange
        repository = VideoRepository(db_session)
        video = Video(
            id=None,
            player_id=test_player.id,
            title="Video to Delete",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        created_video = await repository.create(video)

        # Act
        result = await repository.delete(created_video.id)

        # Assert
        assert result is True
        deleted_video = await repository.get_by_id(created_video.id)
        assert deleted_video is None

    @pytest.mark.asyncio
    async def test_get_public_videos(self, db_session, test_player):
        """Test para obtener videos públicos"""
        # Arrange
        repository = VideoRepository(db_session)
        video1 = Video(
            id=None,
            player_id=test_player.id,
            title="Public Video",
            status=VideoStatus.PROCESSED,
            uploaded_at=datetime.now()
        )
        video2 = Video(
            id=None,
            player_id=test_player.id,
            title="Private Video",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        await repository.create(video1)
        await repository.create(video2)

        # Act
        public_videos = await repository.get_public_videos()

        # Assert
        assert len(public_videos) > 0
        # Todos los videos deben estar procesados
        for video in public_videos:
            assert video.status == VideoStatus.PROCESSED


class TestVoteRepository:
    """Tests de integración para VoteRepository"""

    @pytest.mark.asyncio
    async def test_create_vote(self, db_session, test_video, test_player):
        """Test para crear un voto en la base de datos"""
        # Arrange
        repository = VoteRepository(db_session)

        # Crear un votante diferente al dueño del video
        from app.infrastructure.repositories.player_repository import PlayerRepository
        player_repo = PlayerRepository(db_session)
        voter = Player(
            id=None,
            first_name="Voter",
            last_name="User",
            email=Email("voter.repo@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        created_voter = await player_repo.create(voter)

        vote = Vote(
            id=None,
            video_id=test_video.id,
            player_id=created_voter.id
        )

        # Act
        created_vote = await repository.create(vote)

        # Assert
        assert created_vote.id is not None
        assert created_vote.video_id == test_video.id
        assert created_vote.player_id == created_voter.id

    @pytest.mark.asyncio
    async def test_has_user_voted(self, db_session, test_video):
        """Test para verificar si un usuario ha votado"""
        # Arrange
        repository = VoteRepository(db_session)

        # Crear un votante
        from app.infrastructure.repositories.player_repository import PlayerRepository
        player_repo = PlayerRepository(db_session)
        voter = Player(
            id=None,
            first_name="Voter2",
            last_name="User",
            email=Email("voter2.repo@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        created_voter = await player_repo.create(voter)

        vote = Vote(
            id=None,
            video_id=test_video.id,
            player_id=created_voter.id
        )
        await repository.create(vote)

        # Act
        has_voted = await repository.has_user_voted(test_video.id, created_voter.id)
        has_not_voted = await repository.has_user_voted(test_video.id, 99999)

        # Assert
        assert has_voted is True
        assert has_not_voted is False

    @pytest.mark.asyncio
    async def test_count_votes_for_video(self, db_session, test_video):
        """Test para contar votos de un video"""
        # Arrange
        repository = VoteRepository(db_session)

        # Crear varios votantes
        from app.infrastructure.repositories.player_repository import PlayerRepository
        player_repo = PlayerRepository(db_session)

        for i in range(3):
            voter = Player(
                id=None,
                first_name=f"Voter{i}",
                last_name="User",
                email=Email(f"voter{i}.count@example.com"),
                password=Password("dummy", hashed_value="$2b$12$hashed..."),
                city="Bogotá",
                country="Colombia"
            )
            created_voter = await player_repo.create(voter)

            vote = Vote(
                id=None,
                video_id=test_video.id,
                player_id=created_voter.id
            )
            await repository.create(vote)

        # Act
        vote_count = await repository.count_votes_for_video(test_video.id)

        # Assert
        assert vote_count >= 3

    @pytest.mark.asyncio
    async def test_get_votes_by_videos(self, db_session, test_video, test_player):
        """Test para obtener votos agrupados por video"""
        # Arrange
        repository = VoteRepository(db_session)

        # Crear votante
        from app.infrastructure.repositories.player_repository import PlayerRepository
        player_repo = PlayerRepository(db_session)
        voter = Player(
            id=None,
            first_name="Voter",
            last_name="User",
            email=Email("voter.grouped@example.com"),
            password=Password("dummy", hashed_value="$2b$12$hashed..."),
            city="Bogotá",
            country="Colombia"
        )
        created_voter = await player_repo.create(voter)

        vote = Vote(
            id=None,
            video_id=test_video.id,
            player_id=created_voter.id
        )
        await repository.create(vote)

        # Act
        votes_dict = await repository.get_votes_by_videos([test_video.id])

        # Assert
        assert test_video.id in votes_dict
        assert votes_dict[test_video.id] >= 1
