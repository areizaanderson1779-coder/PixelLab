# PixelLab — Editor de Imágenes con POO en Python

**Autor: Anderson**

Aplicación de escritorio para editar fotografías con Python 3.10+, Tkinter y
Pillow. Demuestra programación orientada a objetos con un modelo independiente
de la interfaz y filtros intercambiables.

## Problema

Las tareas básicas de edición suelen requerir herramientas complejas. PixelLab
reúne carga, filtros, rotación y exportación en una ventana sencilla, con un
historial que permite corregir acciones sin perder el original de la sesión.

## Objetivos

- Crear un editor de imágenes sencillo y reutilizable.
- Aplicar abstracción, encapsulamiento, herencia y polimorfismo reales.
- Separar procesamiento de imágenes y presentación gráfica.
- Conservar la resolución de exportación y permitir deshacer los cambios.

## Funcionalidades

- Cargar PNG, JPG, JPEG y BMP, incluida corrección de orientación EXIF.
- Aplicar escala de grises, desenfoque gaussiano, contraste, inversión y sepia.
- Rotar 90° en sentido antihorario sin recortar la imagen.
- Deshacer sucesivos cambios y restaurar el original cargado.
- Deshacer también la restauración.
- Guardar PNG, JPEG y BMP con su tamaño real.
- Conservar transparencia en PNG; al exportar JPEG/BMP se usa fondo blanco.
- Ajustar la vista previa al tamaño de la ventana sin reducir la imagen editada.
- Mostrar mensajes claros al cargar archivos inválidos o agotar el historial.

## Tecnologías

| Tecnología | Uso |
| --- | --- |
| Python 3.10+ | Lenguaje y clases |
| Tkinter y ttk | Interfaz gráfica de la biblioteca estándar |
| Pillow >= 10.0.0 | Lectura, filtros, transformación, ImageTk y exportación |
| unittest | Pruebas con la biblioteca estándar |
| Git y GitHub | Control de versiones y publicación |

Pillow es la **única dependencia externa**. No se utiliza CustomTkinter ni Flet.

## Instalación

Instala Python 3.10 o superior con soporte Tkinter. En Windows puedes comprobarlo
con `python -m tkinter`: debe abrir una ventana de demostración.

Desde una terminal dentro de `PixelLab`:

```powershell
pip install -r requirements.txt
```

También puedes usar `python -m pip install -r requirements.txt` si `pip` no está
en el PATH. Es recomendable un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En Linux, si Tkinter no está disponible, instala el paquete `python3-tk` de tu
distribución. Tkinter no se instala mediante requirements.txt.

## Ejecución

```powershell
python main.py
```

## Manual de usuario

1. Pulsa **Cargar Imagen** y selecciona un archivo admitido. Cargar otra imagen
   inicia una nueva sesión y vacía el historial anterior.
2. Pulsa un filtro del panel izquierdo. Los filtros se aplican sobre el resultado
   actual y se pueden combinar o repetir.
3. Pulsa **Rotar 90°** para girar la imagen en sentido antihorario.
4. Pulsa **Deshacer** para volver un paso atrás. Si no quedan pasos se muestra
   un mensaje y la imagen permanece intacta.
5. Pulsa **Restaurar** para recuperar el original de la sesión. Puedes deshacer
   esta acción si deseas regresar a la versión editada.
6. Pulsa **Guardar**, elige destino y extensión. La exportación conserva la
   resolución completa. Guardar no cambia el original usado por Restaurar.

Cancelar un diálogo no altera la imagen. Cierra la aplicación desde el control
de cierre de Windows. Los cambios sin guardar y el historial solo viven en
memoria: guarda el resultado antes de cerrar o cargar otra imagen.

## Estructura del proyecto

```text
PixelLab/
├── main.py
├── modelos/
│   ├── __init__.py
│   ├── filtros.py
│   └── editor.py
├── interfaz/
│   ├── __init__.py
│   └── ventana_principal.py
├── docs/
│   └── INFORME_TECNICO.md
├── tests/
│   └── test_editor.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Verificación

Compilación portable (expande los archivos con Python):

```powershell
python -c "import glob, py_compile; [py_compile.compile(p, doraise=True) for p in ['main.py'] + glob.glob('modelos/*.py') + glob.glob('interfaz/*.py')]"
python -m unittest discover -s tests -v
```

En PowerShell también puedes compilar con:

```powershell
$archivos = @('main.py') + @(Get-ChildItem modelos/*.py, interfaz/*.py | ForEach-Object FullName)
python -m py_compile @archivos
```

PowerShell no expande los comodines de argumentos de ejecutables como lo hacen
algunas shells; por eso no se pasa literalmente `modelos/*.py` a py_compile.

## Subir a GitHub

Si aún no se inicializó Git, ejecuta desde esta carpeta:

```powershell
git init
git add .
git commit -m "feat: proyecto inicial PixelLab editor de imagenes con POO"
git branch -M main
```

Con GitHub CLI instalado y autenticado:

```powershell
gh repo create PixelLab --public --source=. --remote=origin --push
```

O crea un repositorio vacío llamado PixelLab en GitHub, reemplaza `TU-USUARIO`
por tu usuario y ejecuta:

```powershell
git remote add origin https://github.com/TU-USUARIO/PixelLab.git
git push -u origin main
```

Si Git solicita identidad, configura tu nombre y correo reales antes del commit.

## Limitaciones

El historial guarda copias completas: imágenes grandes y muchos cambios consumen
memoria. Las operaciones se ejecutan en el hilo de Tkinter, por lo que una imagen
grande puede ocupar la ventana temporalmente. No hay rehacer ni edición de capas.
