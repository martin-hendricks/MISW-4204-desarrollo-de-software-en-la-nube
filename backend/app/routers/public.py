from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.schemas.schemas import Video, VoteResponse, RankingResponse, PlayerRanking, VoteCreate
from app.crud import (
    get_public_videos, create_vote, get_vote_by_user_and_video,
    get_player_rankings, get_total_players_count
)
from app.auth import get_current_player
from app.models.models import Player

router = APIRouter(prefix="/api/public", tags=["público"])


@router.get("/videos", response_model=List[Video])
def list_videos_for_voting(db: Session = Depends(get_db)):
    """
    Lista todos los videos públicos habilitados para votación
    """
    videos = get_public_videos(db)
    return videos


@router.post("/videos/{video_id}/vote", response_model=VoteResponse)
def vote_for_video(
    video_id: int,
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Permite a un usuario registrado emitir un voto por un video
    """
    # Verificar si el video existe y está disponible para votación
    video = get_public_videos(db)
    video_exists = any(v.id == video_id for v in video)
    
    if not video_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video no encontrado o no disponible para votación"
        )
    
    # Verificar si el usuario ya votó por este video
    existing_vote = get_vote_by_user_and_video(db, video_id, current_player.id)
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya has votado por este video"
        )
    
    # Crear el voto
    try:
        create_vote(
            db=db,
            vote=VoteCreate(video_id=video_id),
            voter_id=current_player.id
        )
        
        return VoteResponse(
            message="Voto registrado exitosamente."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/rankings", response_model=RankingResponse)
def get_rankings(
    city: Optional[str] = Query(None, description="Filtra el ranking por ciudad"),
    db: Session = Depends(get_db)
):
    """
    Provee un ranking actualizado de los jugadores
    """
    # Validar parámetro de ciudad si se proporciona
    if city is not None and len(city.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro city no puede estar vacío"
        )
    
    # Obtener rankings
    rankings = get_player_rankings(db, city)
    total_players = get_total_players_count(db, city)
    
    return RankingResponse(
        rankings=rankings,
        total_players=total_players
    )
