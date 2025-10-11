from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional
from app.models.models import Player, Video, Vote, Task
from app.schemas.schemas import PlayerCreate, VideoCreate, VoteCreate, TaskStatus
import uuid


# Operaciones CRUD para Player
def get_player_by_email(db: Session, email: str) -> Optional[Player]:
    """Obtiene un jugador por email"""
    return db.query(Player).filter(Player.email == email).first()


def get_player_by_id(db: Session, player_id: int) -> Optional[Player]:
    """Obtiene un jugador por ID"""
    return db.query(Player).filter(Player.id == player_id).first()


def create_player(db: Session, player: PlayerCreate, password_hash: str) -> Player:
    """Crea un nuevo jugador"""
    db_player = Player(
        first_name=player.first_name,
        last_name=player.last_name,
        email=player.email,
        password_hash=password_hash,
        city=player.city,
        country=player.country
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


# Operaciones CRUD para Video
def create_video(db: Session, video: VideoCreate, player_id: int, filename: str) -> Video:
    """Crea un nuevo video"""
    db_video = Video(
        player_id=player_id,
        title=video.title,
        filename=filename,
        status="uploaded"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    """Obtiene un video por ID"""
    return db.query(Video).filter(Video.id == video_id).first()


def get_videos_by_player(db: Session, player_id: int) -> List[Video]:
    """Obtiene todos los videos de un jugador"""
    return db.query(Video).filter(Video.player_id == player_id).all()


def get_public_videos(db: Session) -> List[Video]:
    """Obtiene todos los videos públicos (procesados) para votación"""
    return db.query(Video).filter(Video.status == "processed").all()


def update_video_status(db: Session, video_id: int, status: str, 
                       original_url: str = None, processed_url: str = None) -> Optional[Video]:
    """Actualiza el estado de un video"""
    video = get_video_by_id(db, video_id)
    if video:
        video.status = status
        if original_url:
            video.original_url = original_url
        if processed_url:
            video.processed_url = processed_url
        db.commit()
        db.refresh(video)
    return video


def delete_video(db: Session, video_id: int) -> bool:
    """Elimina un video y sus tareas relacionadas"""
    video = get_video_by_id(db, video_id)
    if video and video.status in ["uploaded", "processing"]:
        # Eliminar tareas relacionadas primero
        db.query(Task).filter(Task.video_id == video_id).delete()
        # Eliminar votos relacionados
        db.query(Vote).filter(Vote.video_id == video_id).delete()
        # Eliminar el video
        db.delete(video)
        db.commit()
        return True
    return False


def increment_video_votes(db: Session, video_id: int) -> Optional[Video]:
    """Incrementa el contador de votos de un video"""
    video = get_video_by_id(db, video_id)
    if video:
        video.votes_count += 1
        db.commit()
        db.refresh(video)
    return video


# Operaciones CRUD para Vote
def create_vote(db: Session, vote: VoteCreate, voter_id: int) -> Vote:
    """Crea un nuevo voto"""
    # Verificar si el usuario ya votó por este video
    existing_vote = db.query(Vote).filter(
        and_(Vote.video_id == vote.video_id, Vote.voter_id == voter_id)
    ).first()
    
    if existing_vote:
        raise ValueError("Ya has votado por este video")
    
    db_vote = Vote(
        video_id=vote.video_id,
        voter_id=voter_id
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    
    # Incrementar contador de votos del video
    increment_video_votes(db, vote.video_id)
    
    return db_vote


def get_vote_by_user_and_video(db: Session, video_id: int, voter_id: int) -> Optional[Vote]:
    """Verifica si un usuario ya votó por un video"""
    return db.query(Vote).filter(
        and_(Vote.video_id == video_id, Vote.voter_id == voter_id)
    ).first()


# Operaciones CRUD para Task
def create_task(db: Session, video_id: int) -> Task:
    """Crea una nueva tarea de procesamiento"""
    task_id = str(uuid.uuid4())
    db_task = Task(
        video_id=video_id,
        task_id=task_id,
        status="pending"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_status(db: Session, task_id: str, status: TaskStatus, 
                      progress: float = None, error_message: str = None) -> Optional[Task]:
    """Actualiza el estado de una tarea"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if task:
        task.status = status
        if progress is not None:
            task.progress = progress
        if error_message:
            task.error_message = error_message
        if status == "completed":
            from datetime import datetime
            task.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return task


def get_task_by_id(db: Session, task_id: str) -> Optional[Task]:
    """Obtiene una tarea por ID"""
    return db.query(Task).filter(Task.task_id == task_id).first()


# Operaciones para Rankings
def get_player_rankings(db: Session, city: str = None) -> List[dict]:
    """Obtiene el ranking de jugadores ordenado por votos"""
    query = db.query(
        Player.id,
        Player.first_name,
        Player.last_name,
        Player.city,
        func.sum(Video.votes_count).label('total_votes')
    ).join(Video, Player.id == Video.player_id)\
     .filter(Video.status == "processed")\
     .group_by(Player.id, Player.first_name, Player.last_name, Player.city)\
     .order_by(desc('total_votes'))
    
    if city:
        query = query.filter(Player.city == city)
    
    results = query.all()
    
    rankings = []
    for i, result in enumerate(results, 1):
        rankings.append({
            "position": i,
            "username": f"{result.first_name.lower()}.{result.last_name.lower()}",
            "city": result.city,
            "votes": result.total_votes or 0
        })
    
    return rankings


def get_total_players_count(db: Session, city: str = None) -> int:
    """Obtiene el total de jugadores con videos procesados"""
    query = db.query(Player.id).join(Video, Player.id == Video.player_id)\
             .filter(Video.status == "processed")\
             .distinct()
    
    if city:
        query = query.filter(Player.city == city)
    
    return query.count()
