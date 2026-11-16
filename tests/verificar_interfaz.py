"""Prueba de integración con Tk real. Ejecutar desde la raíz del proyecto.

Los selectores de archivos y números reciben respuestas controladas; los botones,
el editor, PhotoImage y las capturas son reales. No agrega dependencias.
"""
import argparse
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageGrab

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from interfaz.ventana_principal import VentanaPrincipal


def ejecutar(capturas=False):
    errores_tk = []
    ventana = VentanaPrincipal()
    ventana.report_callback_exception = lambda *error: errores_tk.append(error)
    ventana.geometry('1000x640+10+10')

    def botones(widget):
        for hijo in widget.winfo_children():
            if hijo.winfo_class() == 'TButton':
                yield hijo
            yield from botones(hijo)

    def pulsar(texto):
        next(b for b in botones(ventana) if b.cget('text') == texto).invoke()
        ventana.update()
        assert not errores_tk, errores_tk

    def captura(nombre):
        if capturas:
            ventana.update()
            time.sleep(0.3)
            ventana.update()
            destino = RAIZ / 'docs/imagenes' / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            # Captura de la ventana nativa renderizada; no se dibuja una interfaz ficticia.
            ImageGrab.grab(window=int(ventana.frame(), 16)).save(destino)

    try:
        with tempfile.TemporaryDirectory() as temporal:
            entrada = Path(temporal) / 'patron_prueba.png'
            salida = Path(temporal) / 'exportada.png'
            patron = Image.new('RGB', (720, 420), '#f5f1e8')
            dibujo = ImageDraw.Draw(patron)
            for i, color in enumerate(['#e05252', '#e6ad37', '#49a783', '#487fca', '#a269b8']):
                dibujo.rectangle((30 + i * 138, 60, 150 + i * 138, 300), fill=color)
                dibujo.ellipse((50 + i * 138, 120, 130 + i * 138, 200), fill='white')
            dibujo.text((30, 20), 'PIXELLAB - PATRON DE PRUEBA (720 x 420)', fill='#172033')
            dibujo.text((30, 340), 'Imagen sintetica para comprobar filtros, rotacion y dimensiones.', fill='#172033')
            patron.save(entrada)
            if capturas:
                (RAIZ / 'recursos').mkdir(exist_ok=True)
                patron.save(RAIZ / 'recursos/patron_prueba.png')
            ventana.update()
            captura('01_inicio.png')
            with patch('interfaz.ventana_principal.filedialog.askopenfilename', return_value=str(entrada)):
                pulsar('Cargar Imagen')
            assert ventana.editor.imagen_actual.size == (720, 420)
            captura('02_imagen_cargada.png')
            for nombre in ['Escala de grises', 'Desenfoque', 'Aumentar contraste', 'Invertir colores', 'Sepia']:
                pulsar('Restaurar')
                pulsar(nombre)
            captura('03_filtro_sepia.png')
            pulsar('Rotar 90°')
            assert ventana.editor.imagen_actual.size == (420, 720)
            with patch('interfaz.ventana_principal.simpledialog.askinteger', side_effect=[300, 500]):
                pulsar('Redimensionar')
            assert ventana.editor.imagen_actual.size == (300, 500)
            captura('04_redimensionada.png')
            with patch('interfaz.ventana_principal.filedialog.asksaveasfilename', return_value=str(salida)):
                pulsar('Guardar')
            with Image.open(salida) as guardada:
                assert guardada.size == (300, 500)
            pulsar('Deshacer')
            assert ventana.editor.imagen_actual.size == (420, 720)
            pulsar('Restaurar')
            assert ventana.editor.imagen_actual.size == (720, 420)
            with patch('interfaz.ventana_principal.simpledialog.askinteger', return_value=None):
                pulsar('Redimensionar')
            assert ventana.editor.imagen_actual.size == (720, 420)
            with patch('interfaz.ventana_principal.filedialog.askopenfilename', return_value='no_existe.png'), \
                    patch('interfaz.ventana_principal.messagebox.showerror') as aviso:
                pulsar('Cargar Imagen')
                aviso.assert_called_once()
                assert 'cargar' in aviso.call_args.args[1]
            assert ventana.editor.imagen_actual.size == (720, 420)
            assert not errores_tk
            print('GUI OK: botones cargar, 5 filtros, rotar, redimensionar, guardar, deshacer, restaurar; cancelacion y error.')
    finally:
        ventana.destroy()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--capturas', action='store_true', help='Guardar capturas reales y patrón de prueba.')
    ejecutar(parser.parse_args().capturas)
