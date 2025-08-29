[![en](https://img.shields.io/badge/lang-en-red.svg)](README.md)
[![es](https://img.shields.io/badge/lang-es-yellow.svg)](README_es.md)

# NASA-MCP. Integración vía MCP con las APIs de la NASA

**NASA es la Administración Nacional de Aeronáutica y el Espacio de Estados Unidos.**

**NASA-MCP** te permite obtener datos astronómicos, información del clima espacial, imágenes de la Tierra y más desde las APIs de la NASA directamente desde Claude AI y otros clientes compatibles con MCP, utilizando el protocolo **Model Context Protocol (MCP)**.

NASA-MCP es un servidor MCP que expone herramientas que permiten a los LLMs consultar datos de varias APIs de la NASA, incluyendo APOD (Imagen Astronómica del Día), Asteroids NeoWs, DONKI (Base de Datos del Clima Espacial), imágenes de la Tierra, EPIC (Cámara de Imágenes Policromáticas de la Tierra) y datos de Exoplanetas.

Incluye manejo seguro de claves API y gestión adecuada de errores para todas las solicitudes a las APIs.

## Características Principales

- Acceso a la **Imagen Astronómica del Día (APOD)** con explicaciones e imágenes
- Consulta de datos de **Objetos Cercanos a la Tierra** e información de asteroides
- Obtención de datos del **Clima Espacial** desde DONKI, incluyendo erupciones solares, tormentas geomagnéticas y más
- Obtención de **imágenes de la Tierra** del satélite Landsat 8 para coordenadas específicas
- Acceso a imágenes de la cámara **EPIC** que muestran el disco completo de la Tierra
- Consulta a la base de datos del **Archivo de Exoplanetas** para información sobre planetas fuera de nuestro sistema solar

## Instalación

### Instalar desde Smithery

To install NASA API Integration Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@AnCode666/nasa-mcp):

```bash
npx -y @smithery/cli install @AnCode666/nasa-mcp --client claude
```

### Instalar con uv

### Prerrequisitos

- Python 3.10 o superior
- Gestor de paquetes [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Instalación de uv

El primer paso es instalar `uv`, un gestor de paquetes para Python.  
**Se puede instalar desde la línea de comandos**.

En macOS y Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

En Windows:  

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

También puedes instalarlo con pip:  

```bash
pip install uv
```

Para más información sobre la instalación de uv, visita la [documentación de uv](https://docs.astral.sh/uv/getting-started/installation/).

## Integración con clientes como Claude for Desktop

Una vez que **uv** está instalado, puedes usar el servidor MCP desde cualquier cliente compatible como Claude for Desktop, en cuyo caso los pasos a seguir son:

1. Ve a **Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`**
2. Añade el siguiente bloque dentro de `"mcpServers"`:

```json
"nasa-mcp": {
    "command": "uvx",
    "args": [
        "nasa_mcp"
    ],
    "env": {
        "NASA_API_KEY": "TU_CLAVE_API_NASA"
    }
}
```

3. Obtén una clave API gratuita de la NASA en: <https://api.nasa.gov/>
4. Reemplaza `TU_CLAVE_API_NASA` con tu clave API real (mantén las comillas). También puedes usar "DEMO_KEY" para pruebas limitadas.
5. Si ya tienes otro servidor MCP configurado, separa cada uno con una coma `,`.

En general, para integrarlo en cualquier otro cliente compatible con MCP como Cursor, CODEGPT o Roo Code, simplemente ve a la configuración del servidor MCP de tu cliente y añade el mismo bloque de código.

## Ejemplos de Uso

Una vez configurado correctamente, puedes preguntar cosas como:

- "Muéstrame la imagen astronómica del día de hoy"
- "Encuentra asteroides que pasarán cerca de la Tierra en la próxima semana"
- "Obtén información sobre erupciones solares de enero de 2023"
- "Muéstrame imágenes de la Tierra para las coordenadas 29.78, -95.33"
- "Encuentra exoplanetas en la zona habitable"

## DISTRIBUCIONES

### Smithery

[![smithery badge](https://smithery.ai/badge/@AnCode666/nasa-mcp)](https://smithery.ai/server/@AnCode666/nasa-mcp)

### MCP Review

[Certificado en MCP review](https://mcpreview.com/mcp-servers/ancode666/nasa-mcp)
