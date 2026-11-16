# Diagramas – PixelLab

Los diagramas están escritos en **Mermaid**, que GitHub muestra directamente. Solo incluyen las clases y relaciones que existen en el código.

Volver al [README](../README.md) · Ver el [Informe técnico](INFORME_TECNICO.md)

---

## 1. Diagrama de clases

```mermaid
classDiagram
    class ABC
    class Tk {
        <<tkinter>>
    }

    class Filtro {
        <<abstract>>
        -str _nombre
        +str nombre
        +aplicar(imagen) Image*
        -_conservar_alfa(original, resultado)$
    }

    class FiltroGrises {
        +aplicar(imagen) Image
    }
    class FiltroDesenfoque {
        +aplicar(imagen) Image
    }
    class FiltroContraste {
        +aplicar(imagen) Image
    }
    class FiltroInvertir {
        +aplicar(imagen) Image
    }
    class FiltroSepia {
        +aplicar(imagen) Image
    }

    class EditorImagen {
        -Image _imagen_original
        -Image _imagen_actual
        -list~Image~ _historial
        -str _ruta_actual
        +bool tiene_imagen
        +Image imagen_actual
        +str ruta_actual
        -_exigir_imagen() Image
        -_registrar_cambio(nueva_imagen)
        +cargar(ruta)
        +aplicar_filtro(filtro)
        +rotar(grados=90)
        +restaurar()
        +redimensionar(ancho, alto)
        +deshacer()
        +guardar(ruta_destino)
    }

    class VentanaPrincipal {
        +EditorImagen editor
        +list~Filtro~ filtros
        -_foto
        -_redibujado
        -_botones_edicion
        -_estado
        -_lienzo
        -_crear_controles()
        -_actualizar_controles()
        -_ejecutar(accion, mensaje)
        -_cargar()
        -_guardar()
        -_redimensionar()
        -_al_redimensionar(evento)
        -_mostrar_imagen()
    }

    ABC <|-- Filtro
    Filtro <|-- FiltroGrises
    Filtro <|-- FiltroDesenfoque
    Filtro <|-- FiltroContraste
    Filtro <|-- FiltroInvertir
    Filtro <|-- FiltroSepia
    Tk <|-- VentanaPrincipal

    VentanaPrincipal "1" *-- "1" EditorImagen : editor (composición)
    VentanaPrincipal "1" o-- "*" Filtro : filtros (agregación)
    EditorImagen ..> Filtro : usa como parámetro en aplicar_filtro()
```

### Lectura del diagrama

| Símbolo | Relación | En PixelLab |
|---|---|---|
| `<\|--` | Herencia | Los cinco filtros heredan de `Filtro`. `Filtro` hereda de `ABC`. `VentanaPrincipal` hereda de `tk.Tk`. |
| `*--` | Composición | `VentanaPrincipal` crea y administra su propio `EditorImagen`. |
| `o--` | Agregación | `VentanaPrincipal` mantiene una lista de filtros que puede recibir ya creados desde fuera. Con `filtros=None`, crea los cinco incluidos. |
| `..>` | Dependencia de uso | `EditorImagen` recibe un `Filtro` solo durante la llamada a `aplicar_filtro()` y **no** lo almacena. |

Notas:
- Los signos de visibilidad representan la intención del diseño: en Python `_` es una convención, no una restricción de acceso.
- `aplicar(imagen)*` es abstracto en `Filtro` y cada subclase lo implementa. `_conservar_alfa` es estático (`$`).
- `nombre`, `tiene_imagen`, `imagen_actual` y `ruta_actual` son **propiedades de solo lectura** (`@property` sin setter). `imagen_actual` devuelve una copia.
- `Image` corresponde a `PIL.Image.Image`. Las imágenes y la ruta del editor pueden ser `None` mientras no se haya cargado nada.
- Los cinco filtros no añaden atributos propios: solo implementan `__init__()`, que llama a `super().__init__("<nombre>")`, y `aplicar()`.

---

## 2. Diagrama de secuencia: aplicar un filtro

```mermaid
sequenceDiagram
    actor U as Usuario
    participant V as VentanaPrincipal
    participant E as EditorImagen
    participant F as Filtro concreto
    participant M as messagebox

    U->>V: Clic en el botón de un filtro
    V->>V: Callback lambda f=filtro
    V->>V: _ejecutar(accion, mensaje)
    V->>E: aplicar_filtro(f)
    E->>E: _exigir_imagen()

    alt Operación correcta
        E->>F: aplicar(imagen.copy())
        Note over F: Implementación propia de la subclase<br/>(grises, desenfoque, contraste, invertir o sepia)
        F-->>E: resultado
        E->>E: Verifica que resultado sea Image.Image
        E->>E: _registrar_cambio(resultado)
        Note over E: Copia del estado anterior al historial<br/>Copia del resultado como imagen actual
        E-->>V: Retorna sin error
        V->>V: Actualiza estado y controles
        V->>V: _mostrar_imagen()
        Note over V: thumbnail sobre una copia<br/>ImageTk.PhotoImage guardado en self._foto
        V-->>U: Vista previa actualizada
    else El modelo lanza ValueError, OSError o MemoryError
        E-->>V: Excepción (por ejemplo, Primero debes cargar una imagen.)
        V->>M: showerror(...)
        M-->>U: Mensaje de error
        Note over E: Entradas inválidas y filtros fallidos probados conservan el estado.<br/>No hay garantía de atomicidad ante MemoryError.
    end
```

Aclaraciones:
- El editor llama a `aplicar()` de forma **polimórfica**: no sabe qué subclase recibe ni usa `if` por tipo.
- Desde la interfaz, los botones de filtros están deshabilitados sin imagen. La comprobación `_exigir_imagen()` es una protección adicional del modelo.
- El filtro recibe una **copia**, de modo que un filtro defectuoso no altera la imagen interna.

---

## 3. Historial según la operación

El flujo anterior (registrar en el historial) corresponde a las **transformaciones**. Cargar, guardar y deshacer se comportan de forma distinta:

```mermaid
flowchart TD
    OP["Operación solicitada"] --> T{"¿Tipo de operación?"}
    T -->|"aplicar_filtro, rotar,<br/>redimensionar, restaurar"| R["_registrar_cambio()<br/>guarda una copia del estado anterior"]
    T -->|"deshacer"| D{"¿Historial vacío?"}
    D -->|"Sí"| DE["ValueError:<br/>No hay cambios para deshacer."]
    D -->|"No"| DP["Recupera el último estado<br/>con pop()"]
    T -->|"cargar"| C{"¿Decodificación correcta?"}
    C -->|"Sí"| CO["Nuevo original y actual<br/>historial vaciado<br/>ruta actualizada"]
    C -->|"No"| CE["ValueError<br/>la sesión anterior se conserva"]
    T -->|"guardar"| G["Escribe el archivo<br/>actualiza ruta_actual<br/>sin cambios en historial ni original"]
```

---

## 4. Organización de módulos

```mermaid
flowchart LR
    MAIN["main.py<br/>punto de entrada"] --> VP["interfaz/ventana_principal.py<br/>VentanaPrincipal"]
    VP --> ED["modelos/editor.py<br/>EditorImagen"]
    VP --> FI["modelos/filtros.py<br/>Filtro y subclases"]
    ED -.->|"recibe filtro como parámetro"| FI
    VP --> TK["Tkinter / ttk<br/>biblioteca estándar"]
    VP --> PIL["Pillow<br/>dependencia externa"]
    ED --> PIL
    FI --> PIL
```

La capa `modelos/` no depende de Tkinter. No existe un controlador independiente, por lo que la arquitectura separa modelo y presentación sin ser un MVC completo.
