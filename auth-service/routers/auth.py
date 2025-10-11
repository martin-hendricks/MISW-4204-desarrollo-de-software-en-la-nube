from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config.database import get_database_session
from models.user import UserLogin, Token, UserCreate, UserResponse
from services.auth_service import AuthService
from services.jwt_service import JWTService

router = APIRouter()
security = HTTPBearer()
jwt_service = JWTService()

def get_auth_service(db: Session = Depends(get_database_session)) -> AuthService:
    """Dependency para obtener AuthService con sesión de BD"""
    return AuthService(db)

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    """Registro de nuevos usuarios en la plataforma"""
    try:
        user = await auth_service.create_user(user_data)
        return {"message": "Usuario creado exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(user_credentials: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    """Autenticación de usuarios y generación de token JWT"""
    user = await auth_service.authenticate_user(
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = jwt_service.create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",  
        "expires_in": jwt_service.get_expires_in_seconds() 
    }

@router.post("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar la validez de un token JWT"""
    try:
        payload = jwt_service.verify_token(credentials.credentials)
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("sub")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Renovar token JWT"""
    try:
        payload = jwt_service.verify_token(credentials.credentials)
        new_token = jwt_service.create_access_token(
            data={"sub": payload.get("sub"), "user_id": payload.get("user_id")}
        )
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para renovación",
            headers={"WWW-Authenticate": "Bearer"},
        )