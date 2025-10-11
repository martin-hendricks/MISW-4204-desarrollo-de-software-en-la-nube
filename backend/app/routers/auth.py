from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.application.services.player_service import PlayerService
from app.application.dtos.player_dtos import (
    PlayerCreateDTO, PlayerLoginDTO, PlayerResponseDTO, 
    TokenResponseDTO
)
from app.shared.container import container
from app.shared.dependencies.auth_dependencies import get_current_player_id
from app.shared.exceptions.player_exceptions import (
    PlayerAlreadyExistsException, PlayerNotFoundException
)

router = APIRouter(prefix="/api/auth", tags=["autenticación"])
security = HTTPBearer()


def get_player_service() -> PlayerService:
    """Dependency para obtener el servicio de jugadores"""
    return container.get_player_service()


# La dependencia get_current_player_id ahora está en auth_dependencies.py


@router.post("/signup", response_model=PlayerResponseDTO, status_code=status.HTTP_201_CREATED)
async def signup(
    player_data: PlayerCreateDTO,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Registra un nuevo jugador en la plataforma
    """
    try:
        player = await player_service.register_player(
            first_name=player_data.first_name,
            last_name=player_data.last_name,
            email=player_data.email,
            password=player_data.password1,  # Usar password1
            city=player_data.city,
            country=player_data.country
        )
        
        return PlayerResponseDTO(message="Usuario creado exitosamente.")
        
    except PlayerAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    login_data: PlayerLoginDTO,
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Autentica a un jugador y genera un token JWT
    """
    try:
        player = await player_service.authenticate_player(
            email=login_data.email,
            password=login_data.password
        )
        
        if not player:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Generar token JWT
        token = await player_service.generate_access_token(player.id)
        
        return TokenResponseDTO(
            access_token=token,
            token_type="Bearer",
            expires_in=3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error en la autenticación"
        )


@router.get("/me", response_model=PlayerResponseDTO)
async def get_current_user(
    player_id: int = Depends(get_current_player_id),
    player_service: PlayerService = Depends(get_player_service)
):
    """
    Obtiene información del jugador autenticado
    """
    try:
        player = await player_service.get_player_by_id(player_id)
        
        return PlayerResponseDTO(
            id=player.id,
            first_name=player.first_name,
            last_name=player.last_name,
            email=player.email.value,
            city=player.city,
            country=player.country,
            username=player.username,
            is_active=player.is_active,
            created_at=player.created_at
        )
        
    except PlayerNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
