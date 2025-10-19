"""Dependencias de autenticación para FastAPI"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.shared.container import container
from app.shared.interfaces.authentication import AuthenticationInterface
from app.domain.repositories.player_repository import PlayerRepositoryInterface

security = HTTPBearer()


async def get_current_player_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Extrae el player_id del token JWT y lo valida
    """
    try:
        # Obtener el servicio de autenticación
        auth_service: AuthenticationInterface = container.get(AuthenticationInterface)
        
        # Verificar el token
        payload = await auth_service.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extraer el player_id del payload
        player_id = payload.get("sub")
        if player_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta player_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el jugador existe y está activo
        player_repo: PlayerRepositoryInterface = container.get(PlayerRepositoryInterface)
        player = await player_repo.get_by_id(int(player_id))
        if player is None or not player.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Jugador no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return int(player_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error en la autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_player_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[int]:
    """
    Extrae el player_id del token JWT de forma opcional (para endpoints que pueden ser públicos)
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_player_id(credentials)
    except HTTPException:
        return None
