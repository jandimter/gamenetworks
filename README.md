# GameNetworks

Aplicación educativa para simular un **juego de redes sociales dirigidas** entre estudiantes.
Cada participante propone cambios en sus conexiones, y al cerrar la ronda el sistema aplica los cambios y calcula métricas de red para visualizar la estructura resultante.

## ¿Qué hace la aplicación?

- Permite a cada estudiante iniciar sesión con su ID y contraseña.
- En cada ronda, cada estudiante puede:
  - **Ronda 0**: agregar hasta 2 conexiones.
  - **Rondas posteriores**: agregar hasta 2 conexiones y eliminar 1 conexión existente.
- Si un estudiante no envía cambios, el sistema genera cambios aleatorios válidos para mantener el avance del juego.
- Calcula y muestra métricas de red (indegree, outdegree, clustering y betweenness centrality).
- Visualiza la red con nodos etiquetados y flechas de dirección.

## Arquitectura (archivos principales)

- `streamlit_app.py`  
  Interfaz principal en Streamlit: login, formulario de cambios y visualización del grafo.
- `networkclass.py`  
  Lógica de dominio: clases `Networks_Game` y `Student`, aplicación de cambios, métricas y visualización con Bokeh.
- `Run_Round.py`  
  Script de administración para cerrar una ronda, aplicar todos los cambios pendientes, guardar nuevo grafo y actualizar metadatos.
- `Users.txt`  
  Diccionario JSON con usuarios y contraseñas.
- `Metadata.txt`  
  Estado global del juego (ej. ronda actual).
- `Graph_Round<N>.txt`  
  Archivo de aristas para cada ronda.
- `user_<id>.config`  
  Estado temporal de cambios enviados por cada usuario (se elimina al cerrar ronda).
- `log_changes.csv`  
  Bitácora histórica de cambios por ronda.

## Requisitos

- Python 3.9+
- Dependencias Python:
  - `networkx`
  - `numpy`
  - `bokeh==2.4.1`
  - `streamlit` (requerido por la UI)

Instalación sugerida:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install streamlit
```

> Nota: `requirements.txt` actualmente no incluye `streamlit`, por eso se instala explícitamente en el último comando.

## Cómo ejecutar la aplicación

En la raíz del proyecto:

```bash
streamlit run streamlit_app.py
```

Luego abre en navegador la URL local que muestra Streamlit (normalmente `http://localhost:8501`).

## Flujo de una ronda

1. Los usuarios inician sesión y envían cambios desde la UI.
2. Cada envío se guarda en un archivo `user_<id>.config`.
3. El administrador ejecuta:

```bash
python Run_Round.py
```

4. El script:
   - Carga todos los `user_<id>.config`.
   - Aplica cambios al grafo de la ronda actual.
   - Genera `Graph_Round<N+1>.txt`.
   - Incrementa `Metadata["Round"]`.
   - Elimina archivos `user_<id>.config`.
   - Registra cambios en `log_changes.csv`.

## Formato de datos

### `Users.txt`
JSON con pares `"usuario": "password"`.

Ejemplo:

```json
{
  "admin1": "admin1",
  "admin2": "admin2"
}
```

### `Metadata.txt`
JSON con la ronda actual.

Ejemplo:

```json
{
  "Round": 2
}
```

### `Graph_Round<N>.txt`
Lista de aristas dirigidas (formato edge-list, una arista por línea), por ejemplo:

```text
admin1 admin3
admin2 admin1
```

## Métricas y visualización

La visualización muestra:

- **ID del estudiante**
- **Indegree** (enlaces recibidos)
- **Outdegree** (enlaces salientes)
- **Clustering coefficient**
- **Betweenness centrality**

Además, el tamaño del nodo depende del grado total y el grafo usa flechas para representar dirección de enlace.

## Operación recomendada

- Respaldar `Graph_Round*.txt`, `Metadata.txt` y `log_changes.csv` antes de cerrar ronda.
- No editar manualmente archivos `user_<id>.config`.
- Si se necesita reiniciar decisiones de un usuario, usar el botón **Reset changes** desde la UI antes del cierre de ronda.

## Problemas comunes

- **Error al iniciar UI por falta de módulo `streamlit`**  
  Instalar con `pip install streamlit`.
- **No se reflejan cambios de una nueva ronda**  
  Verificar que se ejecutó `python Run_Round.py` y que `Metadata.txt` incrementó la ronda.
- **Ronda inconsistente por edición manual de archivos**  
  Restaurar respaldo de `Graph_Round*.txt` y `Metadata.txt`.

## Créditos

Proyecto original forkeado desde `@jesalasc`.
