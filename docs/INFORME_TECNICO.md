# Informe técnico — PixelLab

Autor: **Anderson**. Lenguaje: Python 3.10+. Interfaz: Tkinter/ttk.

## 1. Análisis del problema

Se necesita una herramienta de escritorio que permita realizar transformaciones
básicas sin recurrir a un editor complejo. El usuario debe cargar una fotografía,
ver el resultado, combinar filtros y guardar el archivo. Los cambios deben ser
reversibles durante la sesión y los errores deben ser comprensibles.

Requisitos: PNG, JPG, JPEG y BMP; cinco filtros; rotación; restauración; deshacer;
exportación; una sola dependencia externa, Pillow. La solución debe demostrar
POO y permitir agregar filtros sin modificar la lógica del editor.

## 2. Diseño inicial

Se adoptó una separación entre modelo y vista. Un filtro recibe una imagen y
devuelve otra; el editor administra estados; la ventana administra controles,
diálogos y vista previa. Una lista de filtros permite construir los botones
automáticamente. Se eligieron parámetros fijos para mantener el uso sencillo:
desenfoque gaussiano con radio 2 y contraste con factor 1.5.

El historial es una pila de imágenes anteriores. Cada transformación exitosa
apila una copia; Deshacer extrae la última. Restaurar es otra transformación
reversible. Cargar una imagen nueva vacía la pila. Guardar conserva el historial
y el original cargado.

## 3. Arquitectura

```text
main.py
  └── VentanaPrincipal (Tkinter)
        ├── compone EditorImagen
        │     ├── imagen original y actual
        │     ├── historial de imágenes
        │     └── aplicar_filtro(filtro) → filtro.aplicar(imagen)
        └── agrega una lista de Filtro
              ├── FiltroGrises
              ├── FiltroDesenfoque
              ├── FiltroContraste
              ├── FiltroInvertir
              └── FiltroSepia
```

`modelos` no importa Tkinter. `interfaz` llama a la API pública del editor y
solo escala una copia para presentar la vista previa. `main.py` únicamente
instancia la ventana y ejecuta el bucle de eventos.

La carga se completa antes de sustituir el estado anterior. Los filtros trabajan
con copias para que un filtro fallido no destruya la sesión. La propiedad
`imagen_actual` entrega copias defensivas. `_ruta_actual` representa la última
ruta cargada o guardada, mientras el original sigue siendo el de la última carga.

## 4. Tabla de POO

| Concepto | Clase o método | Archivo | Explicación |
| --- | --- | --- | --- |
| Clases y objetos | EditorImagen, VentanaPrincipal | modelos/editor.py; interfaz/ventana_principal.py | Reúnen estado y responsabilidades; la ventana utiliza una instancia concreta del editor. |
| Encapsulamiento | _imagen_original, _imagen_actual, _historial, _ruta_actual; propiedades | modelos/editor.py | El estado es interno por convención de Python y se accede mediante una API; la imagen pública es una copia. |
| Encapsulamiento | _nombre, nombre | modelos/filtros.py | El nombre se consulta con una propiedad sin setter público. |
| Abstracción | Filtro(ABC), aplicar() | modelos/filtros.py | La clase abstracta define el contrato y no puede instanciarse sin implementar aplicar. |
| Herencia | Cinco subclases de Filtro | modelos/filtros.py | Cada clase hereda el contrato y usa super().__init__ para establecer su nombre. |
| Herencia | VentanaPrincipal(tk.Tk) | interfaz/ventana_principal.py | Especializa una ventana raíz de Tkinter. |
| Polimorfismo | EditorImagen.aplicar_filtro(filtro) | modelos/editor.py | Llama filtro.aplicar sin ramas por clase concreta; admite nuevas subclases. |
| Composición | VentanaPrincipal.editor | interfaz/ventana_principal.py | La ventana crea y administra su EditorImagen. |
| Agregación | VentanaPrincipal.filtros | interfaz/ventana_principal.py | La lista puede recibir objetos filtro externos que existen independientemente de la ventana. |

Un guion bajo expresa privacidad por convención, no una barrera de acceso del
lenguaje. La copia defensiva protege los píxeles del estado administrado.

## 5. Construcción de la interfaz

Se utiliza Tkinter con controles ttk, incluidos en Python. La ventana contiene:

- Etiquetas de título, descripción y estado.
- Botones Cargar Imagen, Guardar, Rotar 90°, Deshacer y Restaurar.
- Un LabelFrame lateral con botones generados desde la lista de filtros.
- Un Canvas para mostrar la imagen mediante PIL.ImageTk.PhotoImage.
- Diálogos filedialog y avisos messagebox para los errores del modelo.

Los botones reciben funciones mediante `command`. El callback dinámico captura
el filtro con `lambda f=filtro`, evitando que todos los botones usen el último
elemento del bucle. El evento Configure programa un redibujado con after para
adaptar la imagen al tamaño disponible. Se mantiene una referencia a PhotoImage
para que el recolector de basura no haga desaparecer la vista previa.

Las operaciones de edición se delegan al editor. La vista no implementa filtros,
rotaciones, historial ni exportación. Los botones de edición se habilitan cuando
existe una imagen.

## 6. Proceso de desarrollo

1. Se definieron los contratos del modelo y la división de responsabilidades.
2. Se prepararon pruebas con unittest y archivos temporales.
3. Se implementaron los filtros con ImageOps, ImageFilter e ImageEnhance, además
   de una matriz de color para sepia. Se conserva el alfa de la entrada.
4. Se implementaron carga, historial, copias defensivas y exportación.
5. Se construyó la ventana y se conectaron los controles con callbacks.
6. Se documentaron uso, arquitectura y publicación en GitHub.
7. Se prepararon verificaciones de compilación, importación y comportamiento.

Los resultados efectivos de ejecución se registran al final de este informe.

## 7. Pruebas

Suite: `python -m unittest discover -s tests -v`. Usa unittest y tempfile de
la biblioteca estándar, además de Pillow; no agrega dependencias externas.

| Prueba | Entrada o acción | Resultado esperado |
| --- | --- | --- |
| Carga y encapsulamiento | Cargar PNG y modificar la copia pública | Los píxeles internos permanecen iguales. |
| Inversión y deshacer | Invertir (100,150,200,128), luego deshacer | Produce (155,105,55,128) y recupera el valor original. |
| Rotación y restauración | Rotar imagen 3×2 y restaurar | Pasa a 2×3, vuelve a 3×2; deshacer restauración recupera 2×3. |
| Error sin imagen | Rotar, filtrar, restaurar, guardar o deshacer antes de cargar | ValueError con explicación. |
| Error al cargar | Archivo inexistente durante una sesión | ValueError y conservación del estado anterior. |
| Error de historial | Deshacer inmediatamente después de cargar | ValueError; no se altera la imagen. |
| Exportación | Cargar y guardar PNG, JPG, JPEG, BMP | Archivo legible de las mismas dimensiones. |
| Transparencia | Guardar PNG con alfa como JPEG | JPEG RGB y estado original RGBA intacto. |
| Polimorfismo | Instancia de filtro nuevo definido en la prueba | El editor lo aplica sin modificaciones de su código. |
| Fallo de filtro | Filtro que modifica su copia y lanza excepción | No cambia la imagen ni añade historial. |
| Abstracción | Instanciar Filtro directamente | TypeError. |
| Operaciones de color | Rojo puro a grises y sepia | Grises (76,76,76), sepia (100,89,69), con redondeo al entero más cercano. |
| Cinco filtros | Procesar una imagen con alfa | Alfa conservado y entrada sin mutaciones. |
| Desenfoque y contraste | Punto claro sobre fondo oscuro | Desenfoque suaviza el punto y contraste lo acentúa. |

Prueba manual de interfaz: cargar cada formato, pulsar cada filtro, redimensionar,
deshacer, restaurar, cancelar diálogos y exportar. Debe realizarse en una sesión
gráfica con Tkinter disponible; la compilación por sí sola no valida esta prueba.

## 8. Problemas y soluciones

| Problema | Solución |
| --- | --- |
| JPEG no admite RGBA | Exportar sobre un fondo RGB blanco, sin cambiar el estado del editor. |
| Vista previa puede desaparecer por recolección de basura | Mantener PhotoImage en self._foto. |
| Callbacks de un bucle pueden compartir el último filtro | Capturar el objeto con el argumento predeterminado lambda f=filtro. |
| Cambiar la vista previa podría reducir el archivo guardado | Escalar una copia y conservar el modelo a resolución completa. |
| Un archivo inválido podría borrar la sesión | Decodificar en una variable local y sustituir el estado solo tras el éxito. |
| PowerShell no expande comodines para py_compile | Obtener los archivos con Get-ChildItem y pasarlos como una lista de argumentos. |

## 9. Conclusiones

PixelLab aplica POO con responsabilidades concretas: la abstracción permite
extender los filtros; el polimorfismo mantiene estable al editor; las copias y
propiedades encapsulan el estado. La separación permite probar el modelo sin
abrir una ventana. El historial favorece la exploración reversible.

Como límites, cada estado ocupa una imagen completa en memoria y las operaciones
son síncronas. Una evolución futura podría limitar el historial o procesar tareas
costosas en segundo plano. Estas mejoras no son necesarias para el alcance actual.

## Registro de verificación

Verificado el 16 de noviembre de 2026 en Windows con Python 3.14.10 y Pillow
13.0.0, que satisface `Pillow>=10.0.0`:

| Verificación ejecutada | Resultado |
| --- | --- |
| Instalación con python -m pip install -r requirements.txt | Correcta. |
| python -m py_compile sobre main.py y todos los módulos de modelos/interfaz | Sin errores; salida 0. |
| python -m unittest discover -s tests -v | 14 pruebas correctas. |
| Importación de main y VentanaPrincipal | Correcta, sin iniciar la ventana al importar. |
| Creación y cierre programático de VentanaPrincipal | Correctos. |
| Ejecución de callbacks del contenedor con carga, cinco filtros, rotación, deshacer, restauración y guardado | Correcta; archivo exportado y dimensiones comprobados. |
| Revisión independiente de requisitos y código | Sin hallazgos importantes. |

La primera prueba de sepia tenía una expectativa incorrecta de redondeo: el
canal verde de rojo puro es 255×0.349 = 88.995, que Pillow redondea a 89. Se
corrigió el dato esperado y se repitió la suite completa con éxito.

El entorno de ejecución utilizó una copia local de Python facilitada por el
usuario. Para esa copia reubicada se configuraron TCL_LIBRARY y TK_LIBRARY con
las bibliotecas Tcl/Tk extraídas en la carpeta de trabajo. Esta adaptación es
exclusiva del entorno de verificación; no modifica la aplicación ni requiere
pasos adicionales al utilizar una instalación normal de Python con Tkinter.

La prueba de GUI ejecutó las operaciones programáticamente; no sustituye una
revisión visual manual de todos los diálogos del sistema.
