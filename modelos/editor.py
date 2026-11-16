"""Estado, historial y operaciones de edición sin dependencias de interfaz."""

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from modelos.filtros import Filtro


class EditorImagen:
    """Encapsula la imagen original, el estado actual y los pasos anteriores."""

    def __init__(self) -> None:
        self._imagen_original: Image.Image | None = None
        self._imagen_actual: Image.Image | None = None
        self._historial: list[Image.Image] = []
        self._ruta_actual: str | None = None

    @property
    def tiene_imagen(self) -> bool:
        return self._imagen_actual is not None

    @property
    def imagen_actual(self) -> Image.Image | None:
        """Entrega una copia para impedir cambios externos sin historial."""
        return self._imagen_actual.copy() if self._imagen_actual is not None else None

    @property
    def ruta_actual(self) -> str | None:
        return self._ruta_actual

    def _exigir_imagen(self) -> Image.Image:
        if self._imagen_actual is None:
            raise ValueError("Primero debes cargar una imagen.")
        return self._imagen_actual

    def _registrar_cambio(self, nueva_imagen: Image.Image) -> None:
        anterior = self._exigir_imagen()
        self._historial.append(anterior.copy())
        self._imagen_actual = nueva_imagen.copy()

    def cargar(self, ruta: str | Path) -> None:
        """Carga PNG/JPEG/BMP; un fallo conserva la sesión anterior."""
        archivo = Path(ruta)
        if archivo.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            raise ValueError("Formato no admitido. Usa PNG, JPG, JPEG o BMP.")
        try:
            with Image.open(archivo) as origen:
                if origen.format not in {"PNG", "JPEG", "BMP"}:
                    raise ValueError("El contenido debe ser una imagen PNG, JPEG o BMP.")
                corregida = ImageOps.exif_transpose(origen)
                con_alfa = "A" in corregida.getbands() or "transparency" in corregida.info
                nueva = corregida.convert("RGBA" if con_alfa else "RGB")
                nueva.load()
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            raise ValueError(f"No se pudo cargar la imagen: {error}") from error
        self._imagen_original = nueva.copy()
        self._imagen_actual = nueva.copy()
        self._historial.clear()
        self._ruta_actual = str(archivo)

    def aplicar_filtro(self, filtro: Filtro) -> None:
        """Despacho polimórfico: no depende del tipo concreto del filtro."""
        imagen = self._exigir_imagen()
        resultado = filtro.aplicar(imagen.copy())
        if not isinstance(resultado, Image.Image):
            raise ValueError("El filtro debe devolver una imagen válida.")
        self._registrar_cambio(resultado)

    def rotar(self, grados: float = 90) -> None:
        """Rota en sentido antihorario y amplía el lienzo para evitar recortes."""
        imagen = self._exigir_imagen()
        self._registrar_cambio(imagen.rotate(grados, expand=True))

    def restaurar(self) -> None:
        """Regresa al original cargado; esta operación también se puede deshacer."""
        self._exigir_imagen()
        self._registrar_cambio(self._imagen_original)

    def redimensionar(self, ancho: int, alto: int) -> None:
        """Cambia las dimensiones reales y permite deshacer la operación."""
        imagen = self._exigir_imagen()
        if (type(ancho) is not int or type(alto) is not int
                or not 1 <= ancho <= 10000 or not 1 <= alto <= 10000):
            raise ValueError("Ancho y alto deben ser enteros entre 1 y 10000 píxeles.")
        if ancho * alto > 25000000:
            raise ValueError("El resultado no debe superar 25 millones de píxeles.")
        self._registrar_cambio(imagen.resize((ancho, alto), Image.Resampling.LANCZOS))

    def deshacer(self) -> None:
        self._exigir_imagen()
        if not self._historial:
            raise ValueError("No hay cambios para deshacer.")
        self._imagen_actual = self._historial.pop()

    def guardar(self, ruta_destino: str | Path) -> None:
        """Exporta sin reducir resolución; JPEG compone transparencia sobre blanco."""
        imagen = self._exigir_imagen()
        destino = Path(ruta_destino)
        formatos = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".bmp": "BMP"}
        formato = formatos.get(destino.suffix.lower())
        if formato is None:
            raise ValueError("El destino debe terminar en .png, .jpg, .jpeg o .bmp.")
        salida = imagen.copy()
        if formato in {"JPEG", "BMP"}:
            if "A" in salida.getbands():
                fondo = Image.new("RGB", salida.size, "white")
                fondo.paste(salida, mask=salida.getchannel("A"))
                salida = fondo
            else:
                salida = salida.convert("RGB")
        try:
            opciones = {"quality": 95} if formato == "JPEG" else {}
            salida.save(destino, format=formato, **opciones)
        except OSError as error:
            raise ValueError(f"No se pudo guardar la imagen: {error}") from error
        self._ruta_actual = str(destino)
