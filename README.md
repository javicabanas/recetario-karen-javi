# Recetario de Karen y Javi

Copia de seguridad del recetario de casa y versión pública, de solo lectura, para la familia.

El recetario que se usa al cocinar es una página privada; aquí se guarda una copia diaria de sus datos y, a partir de ella, se genera la página pública de `docs/`, que sirve GitHub Pages.

## Qué hay

| Carpeta | Contenido |
|---|---|
| `pagina/index.html` | La página del recetario (HTML, CSS y JavaScript en un solo fichero). |
| `recetas/` | Una receta por fichero, en Markdown, generada a partir de los datos. |
| `datos/recipes.json` | Colección `recipes`: las recetas tal como las lee la página. |
| `datos/ratings.json` | Colección `ratings`: valoraciones de 1 a 5 por receta. |
| `datos/menus.json` | Colección `menus`: menús semanales y plan del fin de semana. |
| `datos/history.json` | Colección `history`: lo que se ha comido, día a día. |
| `docs/index.html` | La página pública: la misma página con los datos dentro, solo de lectura. La sirve GitHub Pages. |
| `herramientas/` | `descodificar.py` (adjunto → JSON), `importar.py` (JSON → `datos/` y `recetas/`) y `publicar.py` (genera `docs/index.html`). |

Cada fichero de `datos/` es un objeto `{ "<id del documento>": { ...campos } }`, ordenado por id.

## Cómo se actualiza

Es automático, en dos pasos:

1. **La página guarda la copia.** Cuando Javier abre el recetario y los datos han cambiado, la página guarda todas las colecciones como un adjunto suyo y apunta cuál es en el documento `meta/backup` de su base de datos (`assetId`, `hash`, `at`).
2. **Una tarea programada la sube.** Cada día lee `meta/backup`, descarga el adjunto, lo descodifica con `herramientas/descodificar.py` (que comprueba el SHA-256), regenera `datos/` y `recetas/` con `herramientas/importar.py`, actualiza `pagina/index.html`, vuelve a generar la página pública con `herramientas/publicar.py` y sube el cambio.

`datos/exportado.txt` guarda la fecha de la copia y `datos/copia.sha256` su huella: si la huella no ha cambiado, la tarea no hace nada.

El adjunto es un PNG cuyos píxeles llevan el JSON (formato `png-rgb-v1`, descrito en `descodificar.py`). Se hace así porque la tarea recibe los adjuntos binarios como fichero, byte a byte, y eso permite comprobar que la copia es exacta.

## Avisos

- `pagina/index.html` es la página privada: abierta desde aquí no muestra nada, porque lee sus datos de una base de datos. La que funciona en GitHub Pages es `docs/index.html`, que los lleva dentro.
- La página pública va con un día de retraso como mucho y no se puede modificar desde ella.
- La copia refleja el recetario tal como estaba la última vez que Javier lo abrió: lo que se cambie después por otra vía entra en la copia siguiente.
