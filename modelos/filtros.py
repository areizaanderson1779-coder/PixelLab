"""Filtros polimórficos que producen imágenes nuevas y conservan el alfa."""

from abc import ABC, abstractmethod

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class Filtro(ABC):
    """Contrato común para cualquier transformación de imagen."""

    def __init__(self, nombre: str) -> None:
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del filtro debe ser un texto no vacío.")
        self._nombre = nombre.strip()

    @property
    def nombre(self) -> str:
        return self._nombre

    @abstractmethod
    def aplicar(self, imagen: Image.Image) -> Image.Image:
        """Devuelve el resultado sin modificar la imagen recibida."""
        raise NotImplementedError

    @staticmethod
    def _conservar_alfa(original: Image.Image, resultado: Image.Image) -> Image.Image:
        if "A" in original.getbands() or "transparency" in original.info:
            resultado = resultado.convert("RGBA")
            resultado.putalpha(original.convert("RGBA").getchannel("A"))
        return resultado


class FiltroGrises(Filtro):
    def __init__(self) -> None:
        super().__init__("Escala de grises")

    def aplicar(self, imagen: Image.Image) -> Image.Image:
        resultado = ImageOps.grayscale(imagen.convert("RGB")).convert("RGB")
        return self._conservar_alfa(imagen, resultado)


class FiltroDesenfoque(Filtro):
    def __init__(self) -> None:
        super().__init__("Desenfoque")

    def aplicar(self, imagen: Image.Image) -> Image.Image:
        resultado = imagen.convert("RGB").filter(ImageFilter.GaussianBlur(radius=2))
        return self._conservar_alfa(imagen, resultado)


class FiltroContraste(Filtro):
    def __init__(self) -> None:
        super().__init__("Aumentar contraste")

    def aplicar(self, imagen: Image.Image) -> Image.Image:
        resultado = ImageEnhance.Contrast(imagen.convert("RGB")).enhance(1.5)
        return self._conservar_alfa(imagen, resultado)


class FiltroInvertir(Filtro):
    def __init__(self) -> None:
        super().__init__("Invertir colores")

    def aplicar(self, imagen: Image.Image) -> Image.Image:
        resultado = ImageOps.invert(imagen.convert("RGB"))
        return self._conservar_alfa(imagen, resultado)


class FiltroSepia(Filtro):
    def __init__(self) -> None:
        super().__init__("Sepia")

    def aplicar(self, imagen: Image.Image) -> Image.Image:
        matriz = (
            0.393, 0.769, 0.189, 0,
            0.349, 0.686, 0.168, 0,
            0.272, 0.534, 0.131, 0,
        )
        resultado = imagen.convert("RGB").convert("RGB", matriz)
        return self._conservar_alfa(imagen, resultado)
