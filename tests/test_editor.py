"""Pruebas de comportamiento; ejecutar: python -m unittest discover -s tests -v."""

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from modelos.editor import EditorImagen
from modelos.filtros import (
    Filtro, FiltroContraste, FiltroDesenfoque, FiltroGrises,
    FiltroInvertir, FiltroSepia,
)


class PruebasEditor(unittest.TestCase):
    def test_redimensionar_y_deshacer(self):
        self.editor.cargar(self.ruta)
        self.editor.redimensionar(12, 8)
        self.assertEqual(self.editor.imagen_actual.size, (12, 8))
        self.editor.deshacer()
        self.assertEqual(self.editor.imagen_actual.size, (3, 2))

    def test_redimensionar_invalido_conserva_estado(self):
        self.editor.cargar(self.ruta)
        for ancho, alto in [(0, 4), (-1, 4), (2.5, 4), (True, 4), (4, '2'), (10001, 1)]:
            with self.subTest(ancho=ancho, alto=alto):
                with self.assertRaises(ValueError):
                    self.editor.redimensionar(ancho, alto)
                self.assertEqual(self.editor.imagen_actual.size, (3, 2))
        with self.assertRaises(ValueError):
            self.editor.deshacer()

    def test_redimensionar_sin_imagen(self):
        with self.assertRaisesRegex(ValueError, 'imagen'):
            self.editor.redimensionar(10, 10)

    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = Path(self.temporal.name)
        self.ruta = self.carpeta / 'entrada.png'
        imagen = Image.new('RGBA', (3, 2), (100, 150, 200, 128))
        imagen.putpixel((0, 0), (255, 0, 0, 0))
        imagen.save(self.ruta)
        self.editor = EditorImagen()

    def test_operaciones_sin_imagen_dan_error(self):
        acciones = [lambda: self.editor.aplicar_filtro(FiltroGrises()),
                    self.editor.rotar, self.editor.restaurar,
                    self.editor.deshacer,
                    lambda: self.editor.guardar(self.carpeta / 'salida.png')]
        for accion in acciones:
            with self.subTest(accion=accion):
                with self.assertRaisesRegex(ValueError, 'imagen'):
                    accion()

    def test_carga_y_copia_defensiva(self):
        self.editor.cargar(self.ruta)
        copia = self.editor.imagen_actual
        copia.putpixel((1, 1), (0, 0, 0, 0))
        self.assertEqual(self.editor.imagen_actual.getpixel((1, 1)),
                         (100, 150, 200, 128))
        self.assertTrue(self.editor.tiene_imagen)

    def test_invertir_pixeles_y_deshacer(self):
        self.editor.cargar(self.ruta)
        self.editor.aplicar_filtro(FiltroInvertir())
        self.assertEqual(self.editor.imagen_actual.getpixel((1, 1)),
                         (155, 105, 55, 128))
        self.editor.deshacer()
        self.assertEqual(self.editor.imagen_actual.getpixel((1, 1)),
                         (100, 150, 200, 128))

    def test_rotar_restaurar_y_deshacer_restauracion(self):
        self.editor.cargar(self.ruta)
        self.editor.rotar()
        self.assertEqual(self.editor.imagen_actual.size, (2, 3))
        self.editor.restaurar()
        self.assertEqual(self.editor.imagen_actual.size, (3, 2))
        self.editor.deshacer()
        self.assertEqual(self.editor.imagen_actual.size, (2, 3))

    def test_historial_vacio(self):
        self.editor.cargar(self.ruta)
        with self.assertRaisesRegex(ValueError, 'deshacer'):
            self.editor.deshacer()

    def test_carga_fallida_conserva_estado(self):
        self.editor.cargar(self.ruta)
        with self.assertRaises(ValueError):
            self.editor.cargar(self.carpeta / 'inexistente.png')
        self.assertEqual(self.editor.imagen_actual.size, (3, 2))
        self.assertEqual(self.editor.ruta_actual, str(self.ruta))

    def test_formatos_de_carga_y_guardado(self):
        for extension in ('png', 'jpg', 'jpeg', 'bmp'):
            with self.subTest(extension=extension):
                entrada = self.carpeta / f'foto.{extension}'
                Image.new('RGB', (4, 2), (50, 100, 150)).save(entrada)
                self.editor.cargar(entrada)
                salida = self.carpeta / f'salida.{extension}'
                self.editor.guardar(salida)
                with Image.open(salida) as resultado:
                    self.assertEqual(resultado.size, (4, 2))

    def test_exportar_transparencia_a_jpeg(self):
        self.editor.cargar(self.ruta)
        salida = self.carpeta / 'salida.jpg'
        self.editor.guardar(salida)
        with Image.open(salida) as imagen:
            self.assertEqual(imagen.mode, 'RGB')
        self.assertEqual(self.editor.imagen_actual.mode, 'RGBA')

    def test_filtro_externo_sin_cambiar_editor(self):
        class FiltroAzul(Filtro):
            def __init__(self):
                super().__init__('Azul')

            def aplicar(self, imagen):
                return Image.new('RGBA', imagen.size, (0, 0, 255, 255))

        self.editor.cargar(self.ruta)
        self.editor.aplicar_filtro(FiltroAzul())
        self.assertEqual(self.editor.imagen_actual.getpixel((0, 0)),
                         (0, 0, 255, 255))

    def test_filtro_fallido_no_modifica_imagen_ni_historial(self):
        class FiltroFallido(Filtro):
            def __init__(self):
                super().__init__('Fallido')

            def aplicar(self, imagen):
                imagen.paste((0, 0, 0, 0), (0, 0, 3, 2))
                raise ValueError('Fallo de prueba')

        self.editor.cargar(self.ruta)
        with self.assertRaises(ValueError):
            self.editor.aplicar_filtro(FiltroFallido())
        self.assertEqual(self.editor.imagen_actual.getpixel((1, 1)),
                         (100, 150, 200, 128))
        with self.assertRaises(ValueError):
            self.editor.deshacer()


class PruebasFiltros(unittest.TestCase):
    def test_nombre_filtro_validado(self):
        class Personalizado(Filtro):
            def aplicar(self, imagen):
                return imagen.copy()
        for nombre in ('', '   ', None, 123):
            with self.subTest(nombre=nombre):
                with self.assertRaises(ValueError):
                    Personalizado(nombre)
        self.assertEqual(Personalizado('  Mi filtro  ').nombre, 'Mi filtro')

    def test_filtro_es_abstracto(self):
        with self.assertRaises(TypeError):
            Filtro('Base')

    def test_grises_y_sepia_pixeles_conocidos(self):
        imagen = Image.new('RGB', (1, 1), (255, 0, 0))
        self.assertEqual(FiltroGrises().aplicar(imagen).getpixel((0, 0)),
                         (76, 76, 76))
        self.assertEqual(FiltroSepia().aplicar(imagen).getpixel((0, 0)),
                         (100, 89, 69))

    def test_cinco_filtros_conservan_alfa_y_entrada(self):
        imagen = Image.new('RGBA', (5, 5), (100, 150, 200, 128))
        original = imagen.tobytes()
        for clase in (FiltroGrises, FiltroDesenfoque, FiltroContraste,
                      FiltroInvertir, FiltroSepia):
            with self.subTest(filtro=clase.__name__):
                resultado = clase().aplicar(imagen)
                self.assertEqual(resultado.getchannel('A').getextrema(), (128, 128))
                self.assertEqual(imagen.tobytes(), original)

    def test_desenfoque_y_contraste_transforman(self):
        imagen = Image.new('RGB', (5, 5), (40, 40, 40))
        imagen.putpixel((2, 2), (200, 200, 200))
        self.assertLess(FiltroDesenfoque().aplicar(imagen).getpixel((2, 2))[0], 200)
        self.assertGreater(FiltroContraste().aplicar(imagen).getpixel((2, 2))[0], 200)


if __name__ == '__main__':
    unittest.main()
