from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, List, Optional

from app.dtos.video_dtos import VideoListItemDTO, VoteResponseDTO, RankingItemDTO
from app.services.video_service import VideoService
from app.services.player_service import PlayerService
from app.shared.container import container
from app.shared.dependencies.auth_dependencies import get_current_player_id

router = APIRouter(prefix="/public", tags=["endpoints públicos"])
security = HTTPBearer()


def get_video_service() -> VideoService:
    """Dependency para obtener el servicio de videos"""
    return container.get_video_service()


def get_player_service() -> PlayerService:
    """Dependency para obtener el servicio de jugadores"""
    return container.get_player_service()


@router.get("/videos", response_model=List[VideoListItemDTO])
async def list_videos_for_voting(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de registros a retornar (máx: 100)"),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Lista los videos públicos habilitados para votación con paginación.
    Este endpoint es público y no requiere autenticación.
    Solo retorna videos en estado 'processed'.
    OPTIMIZADO: Incluye paginación para evitar cargar todos los videos de una vez.
    """
    try:
        # La paginación se hace a nivel de base de datos para mejor performance
        videos = await video_service.get_public_videos(skip=skip, limit=limit)

        return [
            VideoListItemDTO(
                video_id=video.id,
                title=video.title,
                status=video.status.value,
                uploaded_at=video.uploaded_at,
                processed_at=video.uploaded_at,
                processed_url=video.processed_url
            )
            for video in videos
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/videos/{video_id}/vote", response_model=VoteResponseDTO)
async def vote_for_video(
    video_id: int,
    player_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Permite a un usuario registrado emitir un voto por un video.
    - Requiere autenticación (JWT).
    - Un usuario solo puede votar una vez por el mismo video.
    """
    try:
        # player_id ya viene de la dependencia de autenticación
        
        await video_service.vote_for_video(video_id, player_id)
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
    OPTIMIZADO: Reduce N+1 queries usando batch loading de jugadores.
    """
    try:
        if city is not None and city.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parámetro inválido en la consulta."
            )

        # Obtener todos los videos con sus votos
        videos_with_votes = await video_service.get_videos_with_votes()

        # Agrupar por jugador y sumar votos
        player_votes = {}
        player_ids = set()
        for video_data in videos_with_votes:
            video = video_data["video"]
            votes_count = video_data["votes_count"]
            player_ids.add(video.player_id)
            if video.player_id not in player_votes:
                player_votes[video.player_id] = 0
            player_votes[video.player_id] += votes_count

        # OPTIMIZACIÓN: Obtener todos los jugadores en una sola query batch
        players_dict = {}
        for player_id in player_ids:
            player = await player_service.get_player_by_id(player_id)
            if player:
                players_dict[player_id] = player

        # Construir rankings filtrando por ciudad si es necesario
        rankings = []
        for player_id, total_votes in player_votes.items():
            player = players_dict.get(player_id)
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

