# 1. Base de datos ejemplo

## Configuración de MySQL

### Iniciar la instancia de MySQL en Docker

Para iniciar una instancia de **MySQL** en un contenedor Docker, ejecuta el siguiente comando en la terminal de tu **GitHub Codespace**:

```sh
docker run --name mysql-container -e MYSQL_ROOT_PASSWORD=contrasena -e MYSQL_DATABASE=tienda_simple -p 3306:3306 -d mysql:latest
```

### Conectarse al contenedor a través de la herramienta de linea de comandos para generar las tablas

```sh
docker exec -i mysql-container mysql -u root -pcontrasena tienda_simple < tienda_simple.sql
```

Esto deberá crear las tablas necesarias e insertar algunos datos de ejemplo


### Verificar que las tablas estén creadas y tenga información. Conectarse al contenedor a través de la herramienta de linea de comandos.
```sh
docker exec -it mysql-container mysql -u root -pcontrasena
```

#### Dentro de mysql ejecuta
```sh
USE tienda_simple;
```

```sh
SELECT * from clientes;
```

```sh
SELECT * from productos;
```

```sh
SELECT * from pedidos;
```

Para salir escriba *quit* y presione enter

### Instala conector python-MySQL
```sh
pip install mysql-connector-python
```

***

# 2. Hands-on: Generar especificación OpenAPI a partir del archivo SQL usando IA

## ¿Qué es OpenAPI 3.0?

**OpenAPI 3.0** es un estándar abierto para describir APIs REST mediante un archivo de texto en formato YAML o JSON. Funciona como un contrato entre el backend y cualquier cliente que lo consuma: define qué endpoints existen, qué parámetros aceptan, qué respuestas regresan y qué esquemas de datos manejan.

Un archivo OpenAPI típico tiene esta estructura:

```yaml
openapi: 3.0.0
info:
  title: Mi API
  version: 1.0.0
servers:
  - url: http://localhost:3000/api/v1
paths:
  /clientes:
    get:
      summary: Lista todos los clientes
      responses:
        '200':
          description: OK
components:
  schemas:
    Cliente:
      type: object
      properties:
        id_cliente:
          type: integer
        nombre:
          type: string
```

Las tres secciones clave son:

- **`paths`** — declara cada endpoint con su método HTTP, parámetros y respuestas posibles
- **`components/schemas`** — define los modelos de datos reutilizables (equivalente a tus tablas MySQL)
- **`servers`** — indica la URL base donde vive la API

La ventaja principal es que este archivo es legible por humanos y por herramientas: generadores de código, plataformas de documentación como Swagger UI, y herramientas de prueba como Postman pueden consumirlo directamente. En este hands-on lo usaremos como puente entre el esquema de base de datos y el código de los servicios web.

## Generar especificación para solo UNA tabla
Si solo quisieras generar la especificación CRUD para una tabla, puedes usar un prompt como el siguiente:

**Prompt:**
```
Genera la especificación OpenAPI 3.0 en formato YAML para una API REST con operaciones CRUD completas sobre la siguiente tabla MySQL:

CREATE TABLE clientes (
  id_cliente   INT          NOT NULL AUTO_INCREMENT,
  nombre       VARCHAR(100) NOT NULL,
  email        VARCHAR(150) NOT NULL UNIQUE,
  telefono     VARCHAR(20)      NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_cliente)
);

Requisitos:
* Incluye los endpoints: GET /clientes, GET /clientes/{id}, POST /clientes, PUT /clientes/{id}, DELETE /clientes/{id}
* Define los schemas Cliente y ClienteInput (sin id_cliente ni created_at para creación/edición)
* Incluye respuestas para los códigos HTTP: 200, 201, 204, 400, 404 y 500
* Agrega ejemplos de request body y response para cada operación
* El servidor base debe ser http://localhost:3000/api/v1
```
***

Algunos ajustes opcionales que puedes agregar al prompt según tus necesidades:

* _"Usa autenticación Bearer Token (JWT)"_ — si necesitas seguridad.
* _"Agrega paginación con parámetros `page` y `limit` en el `GET /clientes`"_ — para listas grandes.
* _"Incluye también el schema para errores estandarizado con `code` y `message`"_ — para respuestas de error consistentes.

## Generar especificación para TODAS las tablas

**Prompt:**

```
Genera la especificación OpenAPI 3.0 en formato YAML para una API REST con operaciones CRUD completas para cada tabla del siguiente esquema MySQL:

[pega aquí todo el contenido del archivo tienda_simple.sql]

Requisitos:
* Por cada tabla genera los endpoints: GET /{recurso}, GET /{recurso}/{id}, POST /{recurso}, PUT /{recurso}/{id}, DELETE /{recurso}/{id}
* Los recursos deben llamarse clientes, productos y pedidos
* Define un schema por cada tabla (ej. Cliente, Producto, Pedido) y su variante Input sin campos autogenerados como id y created_at
* Respeta las relaciones entre tablas: pedidos referencia a clientes e productos mediante sus IDs
* Incluye respuestas para los códigos HTTP: 200, 201, 204, 400, 404 y 500
* Define un schema reutilizable Error con campos code y message, y úsalo en todas las respuestas de error
* Agrega ejemplos de request body y response para cada operación de cada recurso
* El servidor base debe ser http://localhost:3000/api/v1
* Agrupa los endpoints por tag: uno por tabla (Clientes, Productos, Pedidos)
```

## Validar los archivos YAML generados

Usa las siguientes herramientas para validar tu archivo:

- https://oas-validation.com
- https://swapcode.ai/swagger-validator

***

# 3. Generar los servicios web a partir del archivo YAML usando IA

### Ventajas y desventajas
Es una práctica muy común y generalmente recomendable.

**Ventajas**

La especificación OpenAPI es una fuente de verdad estructurada y sin ambigüedades, lo que hace que la IA genere código bastante confiable a partir de ella. En la práctica obtenemos:

* **Consistencia garantizada** — los nombres de campos, tipos de datos y rutas coinciden exactamente con el YAML, sin errores de transcripción.
* **Velocidad** — podemos tener un servidor funcional con validaciones, modelos y rutas en minutos. El scaffolding tedioso (manejo de errores, estructura de carpetas) sale casi gratis.
* **Multi-lenguaje** — el mismo YAML puede producir código en Node/Express, FastAPI, Spring Boot, Laravel, etc. sin reescribir la lógica de contrato.
* **Generación de clientes y tests** — además del servidor podemos generar SDKs para el frontend, colecciones de Postman o pruebas de integración básicas desde el mismo archivo.

**Desventajas y riesgos reales**

El código generado rara vez está listo para producción sin revisión. Los problemas más frecuentes son:

* **Lógica de negocio ausente** — la IA genera la estructura, pero validaciones específicas ("el email debe ser corporativo", "no se puede eliminar un cliente con pedidos activos") no viven en el YAML y hay que agregarlas a mano.
* **Seguridad superficial** — autenticación, autorización por roles y sanitización de inputs suelen generarse como placeholders o directamente se omiten si el YAML no los especifica con detalle.
* **Código no idiomático** — a veces el resultado es funcional pero no sigue las convenciones del framework, lo que genera deuda técnica si el equipo no lo revisa.
* **Falsa confianza** — el mayor riesgo es asumir que porque compila y responde bien en Postman, está listo. Las "edge cases" (concurrencia, transacciones en la BD, manejo de errores a nivel de driver MySQL) necesitan atención humana.

**Recomendación práctica**

Usarlo, pero con una estrategia en capas:

1. **Genera con IA** el scaffolding completo (rutas, controladores, modelos, middleware de validación).
2. **Revisa y ajusta** la conexión a base de datos, manejo de errores y transacciones.
3. **Agrega a mano** la lógica de negocio y seguridad.
4. **Genera también** los tests desde el mismo YAML y úsalos para validar el código generado.

El YAML es suficientemente completo para que una IA produzca un ~70% del trabajo real. Ese porcentaje es el que más tiempo lleva hacer a mano, así que la ganancia es usando IA es muy buena.


## Ejemplos de Prompts para generación de código


**Python**

```
Eres un desarrollador Python. A partir del siguiente OpenAPI 3.0 YAML,
genera una API REST funcional con Flask y MySQL.

<openapi_yaml>
[PEGA AQUÍ TU YAML]
</openapi_yaml>

Requisitos:
- Flask + mysql-connector-python
- Un solo archivo main.py
- Implementa todos los endpoints del YAML con sus rutas,
  métodos HTTP y códigos de respuesta exactos
- Usa variables de entorno para la conexión a MySQL
- Si un recurso no existe, responde con 404
- Habilita CORS para todos los orígenes usando flask-cors:
  from flask_cors import CORS
  app = Flask(__name__)
  CORS(app, origins="*")
```

---

**Node.js**

```
Eres un desarrollador Node.js. A partir del siguiente OpenAPI 3.0 YAML,
genera una API REST funcional con Express y MySQL.

<openapi_yaml>
[PEGA AQUÍ TU YAML]
</openapi_yaml>

Requisitos:
- Express + mysql2
- Un solo archivo index.js
- Implementa todos los endpoints del YAML con sus rutas,
  métodos HTTP y códigos de respuesta exactos
- Usa variables de entorno para la conexión a MySQL
- Si un recurso no existe, responde con 404
- Habilita CORS para todos los orígenes usando el paquete cors:
  const cors = require('cors')
  app.use(cors())
```

---


# 4. Generar el frontend a partir de los webservices usando IA

Una vez que tienes los servicios web funcionando, el mismo YAML de OpenAPI (y opcionalmente el código del servidor) sirven como base para que la IA genere un cliente web funcional. Los prompts siguientes asumen que el servidor corre en `http://localhost:3000/api/v1`.

## HTML + JavaScript (sin frameworks)

```
Eres un desarrollador frontend. A partir del siguiente OpenAPI 3.0 YAML,
genera una aplicación web funcional usando solo HTML, CSS y JavaScript vanilla.

<openapi_yaml>
[PEGA AQUÍ TU YAML]
</openapi_yaml>

Requisitos:
- Un solo archivo index.html (CSS y JS embebidos en el mismo archivo)
- Una sección por cada recurso (Clientes, Productos, Pedidos) navegable mediante tabs o un menú lateral
- Por cada recurso implementa:
  - Tabla para listar todos los registros (GET /{recurso})
  - Formulario para crear un nuevo registro (POST /{recurso})
  - Formulario para editar un registro existente (PUT /{recurso}/{id})
  - Botón para eliminar un registro con confirmación (DELETE /{recurso}/{id})
- Usa fetch() para todas las llamadas HTTP con la base URL http://localhost:3000/api/v1
- Muestra mensajes de éxito y error en pantalla (no solo console.log)
- No uses librerías externas; solo HTML5, CSS y JS nativos del navegador
```

---

## React + Vite

```
Eres un desarrollador frontend. A partir del siguiente OpenAPI 3.0 YAML,
genera una aplicación React funcional usando Vite como bundler.

<openapi_yaml>
[PEGA AQUÍ TU YAML]
</openapi_yaml>

Requisitos:
- Estructura de archivos:
  - src/api/        → un módulo por recurso (clientesApi.js, productosApi.js, pedidosApi.js)
                      con funciones async que encapsulan los fetch() a http://localhost:3000/api/v1
  - src/components/ → componentes reutilizables: tabla genérica, formulario, modal de confirmación
  - src/pages/      → una página por recurso (ClientesPage, ProductosPage, PedidosPage)
  - App.jsx         → enrutamiento con React Router entre las tres páginas
- Por cada recurso implementa las operaciones CRUD completas:
  GET (listar), GET por id (detalle), POST (crear), PUT (editar), DELETE (eliminar con confirm)
- Manejo de estado con useState y useEffect; sin librerías de estado global
- Muestra estados de carga (loading) y mensajes de error en la UI
- Usa solo Tailwind CSS para estilos (configurado en el proyecto Vite)
- El archivo vite.config.js debe incluir un proxy de /api hacia http://localhost:3000
  para evitar problemas de CORS en desarrollo
```

---

> **Nota sobre el proxy en Vite:** configurar el proxy en `vite.config.js` es importante porque evita los errores de CORS durante el desarrollo sin tener que modificar el servidor backend. En producción se resuelve a nivel de servidor web (nginx, caddy, etc.).
```

---
