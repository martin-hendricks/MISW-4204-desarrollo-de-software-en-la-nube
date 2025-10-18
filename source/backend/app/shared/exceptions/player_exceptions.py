"""Excepciones específicas del dominio de jugadores"""


class PlayerException(Exception):
    """Excepción base para el dominio de jugadores"""
    pass


class PlayerNotFoundException(PlayerException):
    """Excepción cuando no se encuentra un jugador"""
    pass


class PlayerAlreadyExistsException(PlayerException):
    """Excepción cuando ya existe un jugador con el mismo email"""
    pass


class InvalidPlayerDataException(PlayerException):
    """Excepción cuando los datos del jugador son inválidos"""
    pass


class PlayerInactiveException(PlayerException):
    """Excepción cuando se intenta operar con un jugador inactivo"""
    pass
