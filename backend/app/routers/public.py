from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, List, Optional

from app.application.dtos.video_dtos import VideoListItemDTO, VoteResponseDTO, RankingItemDTO
from app.application.services.video_service import VideoService
from app.application.services.player_service import PlayerService
from app.shared.container import container
from app.shared.dependencies.auth_dependencies import get_current_player_id

router = APIRouter(prefix="/api/public", tags=["endpoints públicos"])
security = HTTPBearer()


def get_video_service() -> VideoService:
    """Dependency para obtener el servicio de videos"""
    return container.get_video_service()


def get_player_service() -> PlayerService:
    """Dependency para obtener el servicio de jugadores"""
    return container.get_player_service()


@router.get("/videos", response_model=List[VideoListItemDTO])
async def list_videos_for_voting(
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Lista todos los videos públicos habilitados para votación.
    Este endpoint es público y no requiere autenticación.
    Solo retorna videos en estado 'processed'.
    """
    try:
        videos = await video_service.get_public_videos()
        return [
            VideoListItemDTO(
                video_id=video.id,
                title=video.title,
                status=video.status.value,
                uploaded_at=video.created_at,
                processed_at=video.updated_at,
                processed_url=video.processed_url
            )
            for video in videos
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/videos/{video_id}/vote", response_model=VoteResponseDTO)
async def vote_for_video(
    video_id: int,
    voter_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Permite a un usuario registrado emitir un voto por un video.
    - Requiere autenticación (JWT).
    - Un usuario solo puede votar una vez por el mismo video.
    """
    try:
        # voter_id ya viene de la dependencia de autenticación
        
        await video_service.vote_for_video(video_id, voter_id)
        return VoteResponseDTO(message="Voto registrado exitosamente.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if "no encontrado" in str(e).lower() or "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video no encontrado.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/rankings", response_model=List[RankingItemDTO])
async def get_rankings(
    city: Optional[str] = Query(None, description="Filtrar por ciudad"),
    player_service: Annotated[PlayerService, Depends(get_player_service)] = None,
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Provee un ranking actualizado de los jugadores.
    - Organiza a los competidores por el número de votos obtenidos.
    - Puede incluir un parámetro de consulta 'city' para filtrar los resultados.
    - Este endpoint es público.
    """
    try:
        if city is not None and city.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parámetro inválido en la consulta."
            )
        
        # Obtener todos los videos con sus votos
        all_videos = await video_service.get_public_videos()
        
        # Agrupar por jugador y sumar votos
        player_votes = {}
        for video in all_videos:
            if video.player_id not in player_votes:
                player_votes[video.player_id] = 0
            player_votes[video.player_id] += video.votes_count
        
        # Obtener información de los jugadores
        rankings = []
        for player_id, total_votes in player_votes.items():
            player = await player_service.get_player_by_id(player_id)
            if player and (city is None or player.city == city):
                rankings.append({
                    "player_id": player.id,
                    "username": player.username,
                    "city": player.city,
                    "votes": total_votes
                })
        
        # Ordenar por votos descendente
        rankings.sort(key=lambda x: x["votes"], reverse=True)
        
        # Asignar posiciones
        result = []
        for idx, ranking in enumerate(rankings, start=1):
            result.append(RankingItemDTO(
                position=idx,
                username=ranking["username"],
                city=ranking["city"],
                votes=ranking["votes"]
            ))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

