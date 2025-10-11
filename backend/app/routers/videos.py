from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, List
import uuid

from app.application.dtos.video_dtos import (
    VideoUploadResponseDTO, VideoListItemDTO, VideoDetailDTO, VideoDeleteResponseDTO
)
from app.application.services.video_service import VideoService
from app.shared.container import container
from app.shared.dependencies.auth_dependencies import get_current_player_id

router = APIRouter(prefix="/api/videos", tags=["gestión de videos"])
security = HTTPBearer()


def get_video_service() -> VideoService:
    """Dependency para obtener el servicio de videos"""
    return container.get_video_service()


@router.post("/upload", response_model=VideoUploadResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_video(
    title: str = Form(...),
    video_file: UploadFile = File(...),
    player_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Permite a un jugador subir un video de habilidades.
    - La solicitud debe ser form-data.
    - El video_file debe ser un archivo MP4 de máximo 100MB.
    - Inicia una tarea de procesamiento asíncrono.
    """
    try:
        # Validar tipo de archivo
        if not video_file.content_type or not video_file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser un video válido"
            )
        
        # player_id ya viene de la dependencia de autenticación
        
        # Subir video usando el servicio
        video = await video_service.upload_video(
            player_id=player_id,
            file=video_file,
            title=title
        )
        
        # Generar task_id (en este caso usamos el video_id)
        task_id = str(uuid.uuid4())
        
        return VideoUploadResponseDTO(
            message="Video subido correctamente. Procesamiento en curso.",
            task_id=task_id
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=List[VideoListItemDTO])
async def get_my_videos(
    player_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Consulta el listado de videos subidos por el jugador autenticado.
    Retorna diferentes campos según el estado del video:
    - uploaded/processing: video_id, title, status, uploaded_at
    - processed: video_id, title, status, uploaded_at, processed_at, processed_url
    """
    try:
        # player_id ya viene de la dependencia de autenticación
        
        videos = await video_service.get_player_videos(player_id)
        
        return [
            VideoListItemDTO(
                video_id=video.id,
                title=video.title,
                status=video.status.value,
                uploaded_at=video.created_at,
                processed_at=video.updated_at if video.status.value == "processed" else None,
                processed_url=video.processed_url if video.status.value == "processed" else None
            )
            for video in videos
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{video_id}", response_model=VideoDetailDTO)
async def get_specific_video(
    video_id: int,
    player_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Recupera el detalle de un video específico del jugador.
    Incluye las URLs del video original y procesado, así como el conteo de votos.
    """
    try:
        # player_id ya viene de la dependencia de autenticación
        
        video = await video_service.get_video(video_id, player_id)
        
        return VideoDetailDTO(
            video_id=video.id,
            title=video.title,
            status=video.status.value,
            votes=video.votes_count,
            original_url=video.original_url,
            processed_url=video.processed_url,
            created_at=video.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{video_id}", response_model=VideoDeleteResponseDTO)
async def delete_video(
    video_id: int,
    player_id: int = Depends(get_current_player_id),
    video_service: Annotated[VideoService, Depends(get_video_service)] = None
):
    """
    Elimina uno de los videos del jugador.
    Solo se puede eliminar si el video no ha sido publicado para votación o aún no ha sido procesado.
    """
    try:
        # player_id ya viene de la dependencia de autenticación
        
        # Eliminar video usando el servicio
        from app.shared.exceptions.video_exceptions import VideoNotFoundException, VideoNotOwnedException, VideoCannotBeDeletedException
        
        success = await video_service.delete_video(video_id, player_id)
        
        if success:
            return VideoDeleteResponseDTO(
                message="El video ha sido eliminado exitosamente.",
                video_id=video_id
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El video no existe."
            )
    except VideoNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El video no existe."
        )
    except VideoNotOwnedException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este video."
        )
    except VideoCannotBeDeletedException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

