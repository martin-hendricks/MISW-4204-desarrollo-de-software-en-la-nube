"""
Procesamiento de videos con FFmpeg
Implementa todas las transformaciones requeridas según especificación ANB
"""

import logging
import os
from typing import Dict, Optional, Tuple

import ffmpeg
from config import config

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Excepción personalizada para errores de procesamiento"""

    pass


class VideoProcessor:
    """
    Procesador de videos con FFmpeg

    Requisitos según especificación:
    - Recortar a máximo 30 segundos
    - Ajustar a 720p, aspect ratio 16:9
    - Agregar cortinillas de intro/outro (máximo 5s adicionales)
    - Eliminar audio
    - Agregar marca de agua/logo ANB
    """

    def __init__(self):
        self.max_duration = config.VIDEO_MAX_DURATION
        self.width = config.VIDEO_RESOLUTION_WIDTH
        self.height = config.VIDEO_RESOLUTION_HEIGHT
        self.codec = config.VIDEO_CODEC
        self.preset = config.VIDEO_PRESET
        self.crf = config.VIDEO_CRF
        self.tune = config.VIDEO_TUNE

    def get_video_info(self, video_path: str) -> Dict:
        """
        Obtiene información del video usando ffprobe

        Args:
            video_path: Ruta del video

        Returns:
            Diccionario con info del video

        Raises:
            FileNotFoundError: Si el archivo no existe
            VideoProcessingError: Si no se puede leer el video
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )

            if not video_info:
                raise VideoProcessingError("No se encontró stream de video")

            duration = float(probe["format"].get("duration", 0))
            width = int(video_info["width"])
            height = int(video_info["height"])
            codec = video_info.get("codec_name", "unknown")

            # Calcular FPS
            fps_str = video_info.get("r_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = map(int, fps_str.split("/"))
                fps = num / den if den != 0 else 30
            else:
                fps = float(fps_str)

            return {
                "duration": duration,
                "width": width,
                "height": height,
                "codec": codec,
                "fps": fps,
                "size_bytes": int(probe["format"].get("size", 0)),
            }

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"❌ Error obteniendo info del video: {error_msg}")
            raise VideoProcessingError(f"Error leyendo video: {error_msg}")
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            raise VideoProcessingError(f"Error procesando video info: {e}")

    def process_video(
        self,
        input_path: str,
        output_path: str,
        add_logo: bool = True,
        logo_path: Optional[str] = None,
    ) -> str:
        """
        Procesa el video aplicando todas las transformaciones

        Pasos:
        1. Recortar a máximo 30 segundos
        2. Escalar a 720p (1280x720)
        3. Ajustar aspect ratio a 16:9
        4. Agregar logo/marca de agua (opcional)
        5. Eliminar audio
        6. Optimizar para streaming

        Args:
            input_path: Ruta del video original
            output_path: Ruta donde guardar el video procesado
            add_logo: Si agregar logo ANB
            logo_path: Ruta del logo (usa config si no se especifica)

        Returns:
            Ruta del video procesado

        Raises:
            FileNotFoundError: Si el archivo de entrada no existe
            VideoProcessingError: Si falla el procesamiento
        """
        # Validar archivo de entrada antes del try
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video de entrada no encontrado: {input_path}")

        try:
            info = self.get_video_info(input_path)
            logger.debug(
                f"📹 Video original: {info['duration']:.2f}s, "
                f"{info['width']}x{info['height']}, "
                f"{info['size_bytes'] / (1024 * 1024):.2f}MB"
            )

            # Asegurar que el directorio de salida existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # ===== CONSTRUIR PIPELINE DE PROCESAMIENTO OPTIMIZADO =====
            # Optimización: ss=0 + t=30 + accurate_seek = solo lee primeros 30s del archivo
            # Crítico para videos largos (1-2 horas): evita decodificar todo el video
            stream = ffmpeg.input(
                input_path,
                ss=0,  # Desde el inicio
                t=self.max_duration,  # Solo 30 segundos
                accurate_seek=None  # Seek preciso y eficiente
            )
            stream = stream.filter("scale", self.width, self.height)
            stream = stream.filter("setsar", 1)

            if add_logo:
                logo_file = logo_path or config.LOGO_PATH
                if os.path.exists(logo_file):
                    logo = ffmpeg.input(logo_file)
                    position = self._get_logo_position()
                    stream = stream.overlay(logo, x=position[0], y=position[1])
                    logger.debug(f"✅ Logo agregado en posición: {config.LOGO_POSITION}")
                else:
                    logger.warning(f"⚠️ Logo no encontrado: {logo_file}, se omite")

            # Output con configuración optimizada
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec=self.codec,
                preset=self.preset,
                crf=self.crf,
                tune=self.tune,  # Optimización para contenido de video (film)
                threads=1,  # 1 thread por worker (concurrency=2, 2 CPUs total)
                format="mp4",
                an=None,  # Elimina el audio
                movflags="+faststart",  # Optimizado para streaming web
                pix_fmt="yuv420p",  # Máxima compatibilidad
            )

            # Ejecutar FFmpeg
            ffmpeg.run(
                stream,
                overwrite_output=True,
                quiet=False  # Permite ver errores sin capturar en memoria
            )

            # Verificar que se creó el archivo
            if not os.path.exists(output_path):
                raise VideoProcessingError(
                    f"No se generó el video procesado: {output_path}"
                )

            # Obtener info del video procesado
            processed_info = self.get_video_info(output_path)
            logger.debug(
                f"✅ Video procesado: {processed_info['duration']:.2f}s, "
                f"{processed_info['width']}x{processed_info['height']}, "
                f"{processed_info['size_bytes'] / (1024 * 1024):.2f}MB"
            )

            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"❌ Error de FFmpeg: {error_msg}")
            raise VideoProcessingError(
                f"Error procesando video con FFmpeg: {error_msg}"
            )

        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            raise VideoProcessingError(f"Error en procesamiento: {e}")

    def _get_logo_position(self) -> Tuple[str, str]:
        """
        Calcula la posición del logo según configuración

        Returns:
            Tupla (x, y) con las coordenadas para FFmpeg overlay
        """
        margin = config.LOGO_MARGIN

        positions = {
            "top-left": (margin, margin),
            "top-right": (f"W-w-{margin}", margin),
            "bottom-left": (margin, f"H-h-{margin}"),
            "bottom-right": (f"W-w-{margin}", f"H-h-{margin}"),
            "center": ("(W-w)/2", "(H-h)/2"),
        }

        return positions.get(config.LOGO_POSITION, positions["top-right"])

    def add_intro_outro(
        self,
        video_path: str,
        output_path: str,
        intro_path: Optional[str] = None,
        outro_path: Optional[str] = None,
    ) -> str:
        """
        Agrega cortinillas de intro y outro al video
        Según especificación: máximo 5 segundos adicionales total

        Args:
            video_path: Video principal (ya procesado)
            output_path: Ruta de salida
            intro_path: Video de intro (opcional)
            outro_path: Video de outro (opcional)

        Returns:
            Ruta del video con cortinillas

        Raises:
            VideoProcessingError: Si falla la concatenación
        """
        try:
            videos_to_concat = []

            # Intro (máximo 2.5 segundos)
            intro_file = intro_path or config.INTRO_VIDEO_PATH
            if os.path.exists(intro_file):
                videos_to_concat.append(
                    ffmpeg.input(intro_file, t=config.MAX_INTRO_DURATION)
                )
                logger.debug(f"📽️ Intro agregado: {intro_file}")

            # Video principal
            videos_to_concat.append(ffmpeg.input(video_path))

            # Outro (máximo 2.5 segundos)
            outro_file = outro_path or config.OUTRO_VIDEO_PATH
            if os.path.exists(outro_file):
                videos_to_concat.append(
                    ffmpeg.input(outro_file, t=config.MAX_OUTRO_DURATION)
                )
                logger.debug(f"📽️ Outro agregado: {outro_file}")

            # Concatenar videos si hay intro/outro
            if len(videos_to_concat) > 1:
                logger.debug("🎬 Concatenando videos con cortinillas...")

                joined = ffmpeg.concat(*videos_to_concat, v=1, a=0)
                output = ffmpeg.output(
                    joined,
                    output_path,
                    vcodec=self.codec,
                    preset=self.preset,
                    crf=self.crf,
                    tune=self.tune,
                    threads=1,
                    movflags="+faststart",
                    pix_fmt="yuv420p",
                )
                ffmpeg.run(
                    output,
                    overwrite_output=True,
                    quiet=False  # Permite ver errores sin capturar en memoria
                )

                logger.debug("✅ Cortinillas agregadas exitosamente")
                return output_path
            else:
                # No hay intro/outro, retornar el video original
                logger.debug("ℹ️ No se encontraron cortinillas, se omite este paso")
                return video_path

        except Exception as e:
            logger.error(f"❌ Error agregando cortinillas: {e}")
            raise VideoProcessingError(f"Error en cortinillas: {e}")

    def validate_video(self, video_path: str) -> bool:
        """
        Valida que el video procesado cumple con los requisitos

        Args:
            video_path: Ruta del video a validar

        Returns:
            True si es válido, False en caso contrario
        """
        try:
            info = self.get_video_info(video_path)

            # Validaciones según especificación
            checks = [
                (
                    info["duration"] <= 35,
                    f"Duración {info['duration']:.2f}s excede 35s (30s video + 5s cortinillas)",
                ),
                (info["width"] == self.width, f"Ancho {info['width']} != {self.width}"),
                (
                    info["height"] == self.height,
                    f"Alto {info['height']} != {self.height}",
                ),
                (os.path.exists(video_path), "Archivo no existe"),
            ]

            all_valid = True
            for check, error_msg in checks:
                if not check:
                    logger.warning(f"⚠️ Validación fallida: {error_msg}")
                    all_valid = False

            if all_valid:
                logger.debug("✅ Video válido - cumple con todas las especificaciones")

            return all_valid

        except Exception as e:
            logger.error(f"❌ Error validando video: {e}")
            return False


# Singleton instance
video_processor = VideoProcessor()
