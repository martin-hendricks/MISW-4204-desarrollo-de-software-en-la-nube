"""Excepciones específicas del dominio de videos"""


class VideoException(Exception):
    """Excepción base para el dominio de videos"""
    pass


class VideoNotFoundException(VideoException):
    """Excepción cuando no se encuentra un video"""
    pass


class VideoNotOwnedException(VideoException):
    """Excepción cuando un jugador intenta acceder a un video que no le pertenece"""
    pass


class VideoCannotBeDeletedException(VideoException):
    """Excepción cuando un video no puede ser eliminado en su estado actual"""
    pass


class InvalidVideoFileException(VideoException):
    """Excepción cuando el archivo de video es inválido"""
    pass


class VideoProcessingException(VideoException):
    """Excepción durante el procesamiento de un video"""
    pass
