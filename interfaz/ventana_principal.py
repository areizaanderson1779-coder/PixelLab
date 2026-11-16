"""Vista Tkinter: diálogos, controles y presentación de la imagen."""

from collections.abc import Callable, Iterable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from modelos.editor import EditorImagen
from modelos.filtros import (
    Filtro, FiltroContraste, FiltroDesenfoque, FiltroGrises,
    FiltroInvertir, FiltroSepia,
)


class VentanaPrincipal(tk.Tk):
    """Compone un editor y agrega filtros que también pueden venir del exterior."""

    def __init__(self, filtros: Iterable[Filtro] | None = None) -> None:
        super().__init__()
        self.editor = EditorImagen()
        self.filtros = list(filtros) if filtros is not None else [
            FiltroGrises(), FiltroDesenfoque(), FiltroContraste(),
            FiltroInvertir(), FiltroSepia(),
        ]
        self._foto: ImageTk.PhotoImage | None = None
        self._redibujado: str | None = None
        self._botones_edicion: list[ttk.Button] = []
        self.title("PixelLab · Editor de imágenes")
        self.geometry("1100x740")
        self.minsize(800, 560)
        self.configure(background="#eef2f7")
        self._estado = tk.StringVar(value="Carga una imagen para empezar.")
        self._crear_controles()
        self._actualizar_controles()

    def _crear_controles(self) -> None:
        estilo = ttk.Style(self)
        estilo.configure("Title.TLabel", font=("Segoe UI", 23, "bold"))
        estilo.configure("TButton", padding=(10, 8))
        estilo.configure("Subtitle.TLabel", foreground="#526078")
        contenedor = ttk.Frame(self, padding=20)
        contenedor.pack(fill=tk.BOTH, expand=True)
        ttk.Label(contenedor, text="PixelLab", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(contenedor, text="Tu imagen, una nueva perspectiva.",
                  style="Subtitle.TLabel").pack(anchor=tk.W, pady=(2, 16))

        barra = ttk.Frame(contenedor)
        barra.pack(fill=tk.X, pady=(0, 14))
        ttk.Button(barra, text="Cargar Imagen", command=self._cargar).pack(side=tk.LEFT)
        acciones = [
            ("Guardar", self._guardar),
            ("Rotar 90°", lambda: self._ejecutar(self.editor.rotar, "Imagen rotada 90°.")),
            ("Deshacer", lambda: self._ejecutar(self.editor.deshacer, "Cambio deshecho.")),
            ("Restaurar", lambda: self._ejecutar(self.editor.restaurar, "Original restaurado.")),
        ]
        for texto, callback in acciones:
            boton = ttk.Button(barra, text=texto, command=callback)
            boton.pack(side=tk.LEFT, padx=(8, 0))
            self._botones_edicion.append(boton)

        cuerpo = ttk.Frame(contenedor)
        cuerpo.pack(fill=tk.BOTH, expand=True)
        lateral = ttk.LabelFrame(cuerpo, text="Filtros", padding=12)
        lateral.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        for filtro in self.filtros:
            boton = ttk.Button(
                lateral, text=filtro.nombre,
                command=lambda f=filtro: self._ejecutar(
                    lambda: self.editor.aplicar_filtro(f), f"Filtro aplicado: {f.nombre}."),
            )
            boton.pack(fill=tk.X, pady=(0, 8))
            self._botones_edicion.append(boton)
        ttk.Label(lateral, text="Los filtros se acumulan.\nDeshacer revierte un paso.",
                  style="Subtitle.TLabel").pack(anchor=tk.W, pady=(16, 0))

        self._lienzo = tk.Canvas(cuerpo, background="#172033", highlightthickness=0)
        self._lienzo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._lienzo.bind("<Configure>", self._al_redimensionar)
        ttk.Label(contenedor, textvariable=self._estado,
                  style="Subtitle.TLabel").pack(anchor=tk.W, pady=(12, 0))

    def _actualizar_controles(self) -> None:
        estado = tk.NORMAL if self.editor.tiene_imagen else tk.DISABLED
        for boton in self._botones_edicion:
            boton.configure(state=estado)

    def _ejecutar(self, accion: Callable[[], None], mensaje: str) -> None:
        try:
            accion()
        except (ValueError, OSError, MemoryError) as error:
            messagebox.showerror("PixelLab", str(error) or "Memoria insuficiente.", parent=self)
            return
        self._estado.set(mensaje)
        self._actualizar_controles()
        self._mostrar_imagen()

    def _cargar(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self, title="Cargar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"),
                       ("Todos los archivos", "*.*")],
        )
        if ruta:
            self._ejecutar(lambda: self.editor.cargar(ruta),
                           f"Imagen cargada: {Path(ruta).name}")

    def _guardar(self) -> None:
        actual = self.editor.ruta_actual
        nombre = f"{Path(actual).stem}_editada.png" if actual else "imagen_editada.png"
        ruta = filedialog.asksaveasfilename(
            parent=self, title="Guardar imagen", initialfile=nombre,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("BMP", "*.bmp")],
        )
        if ruta:
            self._ejecutar(lambda: self.editor.guardar(ruta),
                           f"Imagen guardada: {Path(ruta).name}")

    def _al_redimensionar(self, evento: tk.Event) -> None:
        if self._redibujado is not None:
            self.after_cancel(self._redibujado)
        self._redibujado = self.after(100, self._mostrar_imagen)

    def _mostrar_imagen(self) -> None:
        self._redibujado = None
        self._lienzo.delete("all")
        ancho = max(1, self._lienzo.winfo_width())
        alto = max(1, self._lienzo.winfo_height())
        imagen = self.editor.imagen_actual
        if imagen is None:
            self._foto = None
            self._lienzo.create_text(
                ancho // 2, alto // 2, text="Carga una imagen\nPNG · JPG · JPEG · BMP",
                fill="#c6d1e5", font=("Segoe UI", 16), justify=tk.CENTER,
            )
            return
        # Solo la copia para vista previa cambia de tamaño.
        imagen.thumbnail((max(1, ancho - 32), max(1, alto - 32)), Image.Resampling.LANCZOS)
        self._foto = ImageTk.PhotoImage(imagen, master=self)
        self._lienzo.create_image(ancho // 2, alto // 2, image=self._foto, anchor=tk.CENTER)
