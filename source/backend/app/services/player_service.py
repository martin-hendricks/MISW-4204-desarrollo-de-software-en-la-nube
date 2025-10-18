from typing import Optional
from app.domain.entities.player import Player
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.domain.repositories.player_repository import PlayerRepositoryInterface
from app.shared.interfaces.authentication import AuthenticationInterface
from app.shared.exceptions.player_exceptions import PlayerAlreadyExistsException, PlayerNotFoundException


class PlayerService:
    """Servicio de aplicación para la gestión de jugadores"""
    
    def __init__(
        self,
        player_repository: PlayerRepositoryInterface,
        auth_service: AuthenticationInterface
    ):
        self._player_repository = player_repository
        self._auth_service = auth_service
    
    async def register_player(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        city: str,
        country: str
    ) -> Player:
        """Registra un nuevo jugador"""
        # Verificar si el jugador ya existe
        existing_player = await self._player_repository.get_by_email(Email(email))
        if existing_player:
            raise PlayerAlreadyExistsException(f"El email {email} ya está registrado")
        
        # Crear entidad de dominio
        player = Player(
            id=None,
            first_name=first_name,
            last_name=last_name,
            email=Email(email),
            password=Password(password),
            city=city,
            country=country
        )
        
        # Hash de la contraseña
        hashed_password = await self._auth_service.hash_password(password)
        # Crear un nuevo objeto Password con el hash
        player.password = Password(value=password, hashed_value=hashed_password)
        
        # Guardar en el repositorio
        created_player = await self._player_repository.create(player)
        
        return created_player
    
    async def authenticate_player(self, email: str, password: str) -> Optional[Player]:
        """Autentica un jugador"""
        # Buscar jugador por email
        player = await self._player_repository.get_by_email(Email(email))
        if not player:
            return None
        
        # Verificar contraseña
        is_valid = await self._auth_service.verify_password(password, player.password.hashed_value)
        if not is_valid:
            return None
        
        return player
    
    async def generate_access_token(self, player_id: int) -> str:
        """Genera un token de acceso JWT para el jugador"""
        return await self._auth_service.create_player_token(player_id)
    
    async def get_player_by_id(self, player_id: int) -> Player:
        """Obtiene un jugador por ID"""
        player = await self._player_repository.get_by_id(player_id)
        if not player:
            raise PlayerNotFoundException(f"Jugador con ID {player_id} no encontrado")
        return player
    
    async def get_player_by_email(self, email: str) -> Player:
        """Obtiene un jugador por email"""
        player = await self._player_repository.get_by_email(Email(email))
        if not player:
            raise PlayerNotFoundException(f"Jugador con email {email} no encontrado")
        return player
    
    async def update_player_profile(
        self,
        player_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> Player:
        """Actualiza el perfil de un jugador"""
        player = await self.get_player_by_id(player_id)
        player.update_profile(first_name, last_name, city, country)
        return await self._player_repository.update(player)
    
    async def deactivate_player(self, player_id: int) -> Player:
        """Desactiva un jugador"""
        player = await self.get_player_by_id(player_id)
        player.deactivate()
        return await self._player_repository.update(player)
    
    async def get_rankings(self, city: Optional[str] = None) -> list:
        """Obtiene el ranking de jugadores"""
        players = await self._player_repository.get_rankings(city)
        
        rankings = []
        for i, player in enumerate(players, 1):
            rankings.append({
                "position": i,
                "username": player.username,
                "city": player.city,
                "votes": 0  # Esto se calculará en el servicio de videos
            })
        
        return rankings
