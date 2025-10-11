from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import PlayerSignup, PlayerLogin, Token, Player
from app.crud import get_player_by_email, create_player
from app.auth import authenticate_player, create_access_token, get_password_hash, get_current_player
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


@router.post("/signup", response_model=dict, status_code=status.HTTP_201_CREATED)
def signup(player: PlayerSignup, db: Session = Depends(get_db)):
    """
    Registra un nuevo jugador en la plataforma
    """
    # Verificar si el email ya existe
    existing_player = get_player_by_email(db, player.email)
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear hash de la contraseña
    password_hash = get_password_hash(player.password1)
    
    # Crear el jugador
    db_player = create_player(
        db=db,
        player=PlayerSignup(
            first_name=player.first_name,
            last_name=player.last_name,
            email=player.email,
            password1=player.password1,
            password2=player.password2,
            city=player.city,
            country=player.country
        ),
        password_hash=password_hash
    )
    
    return {
        "message": "Usuario creado exitosamente.",
        "player_id": db_player.id
    }


@router.post("/login", response_model=Token)
def login(player: PlayerLogin, db: Session = Depends(get_db)):
    """
    Autentica a un jugador y genera un token JWT
    """
    # Autenticar al jugador
    authenticated_player = authenticate_player(db, player.email, player.password)
    if not authenticated_player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Crear token de acceso
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": authenticated_player.email}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=Player)
def get_current_user_info(current_player: Player = Depends(get_current_player)):
    """
    Obtiene información del jugador autenticado
    """
    return current_player
