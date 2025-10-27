"""Tests para las entidades de dominio"""

import pytest
from datetime import datetime
from app.domain.entities.player import Player
from app.domain.entities.video import Video, VideoStatus
from app.domain.entities.vote import Vote
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password


class TestEmailValueObject:
    """Tests para el value object Email"""

    def test_valid_email_creation(self):
        """Test para crear un email válido"""
        email = Email("test@example.com")
        assert email.value == "test@example.com"
        assert str(email) == "test@example.com"

    def test_invalid_email_format(self):
        """Test para email con formato inválido"""
        with pytest.raises(ValueError, match="Formato de email inválido"):
            Email("invalid-email")

    def test_email_without_at_symbol(self):
        """Test para email sin símbolo @"""
        with pytest.raises(ValueError, match="Formato de email inválido"):
            Email("invalidemail.com")

    def test_email_without_domain(self):
        """Test para email sin dominio"""
        with pytest.raises(ValueError, match="Formato de email inválido"):
            Email("test@")

    def test_email_equality_case_insensitive(self):
        """Test para igualdad de emails (case insensitive)"""
        email1 = Email("Test@Example.com")
        email2 = Email("test@example.com")
        assert email1 == email2

    def test_email_hash_consistency(self):
        """Test para consistencia del hash"""
        email1 = Email("Test@Example.com")
        email2 = Email("test@example.com")
        assert hash(email1) == hash(email2)


class TestPasswordValueObject:
    """Tests para el value object Password"""

    def test_valid_password_creation(self):
        """Test para crear una contraseña válida"""
        password = Password("StrongPass123")
        assert str(password) == "***"  # No debe exponer la contraseña

    def test_password_too_short(self):
        """Test para contraseña muy corta"""
        with pytest.raises(ValueError, match="debe tener al menos 8 caracteres"):
            Password("short")

    def test_password_minimum_length(self):
        """Test para contraseña con longitud mínima"""
        password = Password("12345678")
        assert str(password) == "***"

    def test_password_with_hashed_value(self):
        """Test para contraseña con valor hasheado"""
        password = Password("password123", hashed_value="$2b$12$hashed...")
        assert password.hashed_value == "$2b$12$hashed..."

    def test_password_equality(self):
        """Test para igualdad de contraseñas"""
        password1 = Password("password123")
        password2 = Password("password123")
        assert password1 == password2

    def test_password_dummy_value(self):
        """Test para valor dummy (usado cuando viene de BD)"""
        password = Password("dummy", hashed_value="$2b$12$hashed...")
        assert password.value == "dummy"
        assert password.hashed_value == "$2b$12$hashed..."


class TestPlayerEntity:
    """Tests para la entidad Player"""

    def test_valid_player_creation(self):
        """Test para crear un jugador válido"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia"
        )
        assert player.id == 1
        assert player.first_name == "John"
        assert player.last_name == "Doe"
        assert player.city == "Bogotá"
        assert player.country == "Colombia"
        assert player.is_active is True

    def test_player_username_property(self):
        """Test para la propiedad username"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia"
        )
        assert player.username == "john.doe"

    def test_player_full_name_property(self):
        """Test para la propiedad full_name"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia"
        )
        assert player.full_name == "John Doe"

    def test_player_empty_first_name(self):
        """Test para jugador con nombre vacío"""
        with pytest.raises(ValueError, match="El nombre no puede estar vacío"):
            Player(
                id=1,
                first_name="",
                last_name="Doe",
                email=Email("john.doe@example.com"),
                password=Password("password123"),
                city="Bogotá",
                country="Colombia"
            )

    def test_player_empty_last_name(self):
        """Test para jugador con apellido vacío"""
        with pytest.raises(ValueError, match="El apellido no puede estar vacío"):
            Player(
                id=1,
                first_name="John",
                last_name="",
                email=Email("john.doe@example.com"),
                password=Password("password123"),
                city="Bogotá",
                country="Colombia"
            )

    def test_player_empty_city(self):
        """Test para jugador con ciudad vacía"""
        with pytest.raises(ValueError, match="La ciudad no puede estar vacía"):
            Player(
                id=1,
                first_name="John",
                last_name="Doe",
                email=Email("john.doe@example.com"),
                password=Password("password123"),
                city="",
                country="Colombia"
            )

    def test_player_empty_country(self):
        """Test para jugador con país vacío"""
        with pytest.raises(ValueError, match="El país no puede estar vacío"):
            Player(
                id=1,
                first_name="John",
                last_name="Doe",
                email=Email("john.doe@example.com"),
                password=Password("password123"),
                city="Bogotá",
                country=""
            )

    def test_player_deactivate(self):
        """Test para desactivar un jugador"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia"
        )
        player.deactivate()
        assert player.is_active is False

    def test_player_activate(self):
        """Test para activar un jugador"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia",
            is_active=False
        )
        player.activate()
        assert player.is_active is True

    def test_player_update_profile(self):
        """Test para actualizar el perfil de un jugador"""
        player = Player(
            id=1,
            first_name="John",
            last_name="Doe",
            email=Email("john.doe@example.com"),
            password=Password("password123"),
            city="Bogotá",
            country="Colombia"
        )
        player.update_profile(first_name="Jane", city="Medellín")
        assert player.first_name == "Jane"
        assert player.last_name == "Doe"  # No cambió
        assert player.city == "Medellín"
        assert player.country == "Colombia"  # No cambió


class TestVideoEntity:
    """Tests para la entidad Video"""

    def test_valid_video_creation(self):
        """Test para crear un video válido"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        assert video.id == 1
        assert video.player_id == 1
        assert video.title == "Mi mejor jugada"
        assert video.status == VideoStatus.UPLOADED

    def test_video_empty_title(self):
        """Test para video con título vacío"""
        with pytest.raises(ValueError, match="El título del video no puede estar vacío"):
            Video(
                id=1,
                player_id=1,
                title="",
                status=VideoStatus.UPLOADED
            )

    def test_video_invalid_player_id(self):
        """Test para video con player_id inválido"""
        with pytest.raises(ValueError, match="El ID del jugador debe ser válido"):
            Video(
                id=1,
                player_id=0,
                title="Mi mejor jugada",
                status=VideoStatus.UPLOADED
            )

    def test_video_mark_as_processed(self):
        """Test para marcar un video como procesado"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.UPLOADED,
            uploaded_at=datetime.now()
        )
        processed_url = "/videos/processed/1"
        video.mark_as_processed(processed_url)

        assert video.status == VideoStatus.PROCESSED
        assert video.processed_url == processed_url
        assert video.processed_at is not None

    def test_video_can_be_deleted_uploaded(self):
        """Test para verificar si un video subido puede ser eliminado"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.UPLOADED
        )
        assert video.can_be_deleted() is True

    def test_video_can_be_deleted_processed(self):
        """Test para verificar si un video procesado puede ser eliminado"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.PROCESSED
        )
        assert video.can_be_deleted() is False

    def test_video_is_public_uploaded(self):
        """Test para verificar si un video subido es público"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.UPLOADED
        )
        assert video.is_public() is False

    def test_video_is_public_processed(self):
        """Test para verificar si un video procesado es público"""
        video = Video(
            id=1,
            player_id=1,
            title="Mi mejor jugada",
            status=VideoStatus.PROCESSED
        )
        assert video.is_public() is True


class TestVoteEntity:
    """Tests para la entidad Vote"""

    def test_valid_vote_creation(self):
        """Test para crear un voto válido"""
        vote = Vote(
            id=1,
            video_id=1,
            player_id=2
        )
        assert vote.id == 1
        assert vote.video_id == 1
        assert vote.player_id == 2

    def test_vote_invalid_video_id(self):
        """Test para voto con video_id inválido"""
        with pytest.raises(ValueError, match="El ID del video debe ser válido"):
            Vote(
                id=1,
                video_id=0,
                player_id=2
            )

    def test_vote_invalid_player_id(self):
        """Test para voto con player_id inválido"""
        with pytest.raises(ValueError, match="El ID del votante debe ser válido"):
            Vote(
                id=1,
                video_id=1,
                player_id=0
            )

    def test_vote_is_valid(self):
        """Test para verificar si un voto es válido"""
        vote = Vote(
            id=1,
            video_id=1,
            player_id=2
        )
        assert vote.is_valid() is True