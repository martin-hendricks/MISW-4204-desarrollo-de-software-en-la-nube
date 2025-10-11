from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.schemas import Video, VideoDetail, VideoUploadResponse, VideoDeleteResponse, VideoCreate
from app.crud import (
    create_video, get_videos_by_player, get_video_by_id, 
    delete_video, create_task
)
from app.auth import get_current_player
from app.models.models import Player
from app.file_storage import validate_video_file, generate_unique_filename, save_uploaded_file, get_file_url, delete_file
from app.tasks import process_video

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_video(
    video_file: UploadFile = File(...),
    title: str = Form(...),
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Permite a un jugador subir un video de habilidades
    """
    # Validar el archivo de video
    validate_video_file(video_file)
    
    # Generar nombre único para el archivo
    filename = generate_unique_filename(video_file.filename)
    
    # Guardar el archivo
    file_path = save_uploaded_file(video_file, filename)
    
    # Crear registro en la base de datos
    video = create_video(
        db=db,
        video=VideoCreate(title=title),
        player_id=current_player.id,
        filename=filename
    )
    
    # Crear tarea de procesamiento
    task = create_task(db, video.id)
    
    # Iniciar procesamiento asíncrono
    process_video.delay(video.id)
    
    return VideoUploadResponse(
        task_id=task.task_id,
        message="Video subido exitosamente. El procesamiento ha comenzado."
    )


@router.get("/", response_model=List[Video])
def get_my_videos(
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Consulta el listado de videos subidos por el jugador autenticado
    """
    videos = get_videos_by_player(db, current_player.id)
    return videos


@router.get("/{video_id}", response_model=VideoDetail)
def get_video(
    video_id: int,
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Recupera el detalle de un video específico del jugador
    """
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video no encontrado"
        )
    
    # Verificar que el video pertenece al jugador
    if video.player_id != current_player.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este video"
        )
    
    return video


@router.delete("/{video_id}", response_model=VideoDeleteResponse)
def delete_video_endpoint(
    video_id: int,
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Elimina uno de los videos del jugador
    """
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video no encontrado"
        )
    
    # Verificar que el video pertenece al jugador
    if video.player_id != current_player.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este video"
        )
    
    # Verificar que el video puede ser eliminado
    if video.status not in ["uploaded", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El video no puede ser eliminado porque ya ha sido procesado o publicado"
        )
    
    # Eliminar archivo del sistema
    if video.filename:
        delete_file(video.filename)
    
    # Eliminar de la base de datos
    success = delete_video(db, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo eliminar el video"
        )
    
    return VideoDeleteResponse(
        message="El video ha sido eliminado exitosamente."
    )
