             DIRECTORIO ACADÉMICO - API REST Y FRONTEND
Este proyecto consiste en un sistema de gestion academica compuesto por 
una API REST construida con Flask y MySQL, y un cliente web interactivo 
desarrollado en HTML y JavaScript puro. Permite realizar operaciones 
CRUD (Crear, Leer, Actualizar y Eliminar) sobre los recursos de Materias 
y Docentes, respetando las restricciones de integridad referencial.

------------------------------------------------------------------------
1. CONFIGURACIÓN DE LA BASE DE DATOS
------------------------------------------------------------------------

Antes de inicializar la aplicacion, asegurese de ejecutar el siguiente 
script en su servidor MySQL para estructurar la base de datos e insertar 
los registros iniciales:

CREATE DATABASE IF NOT EXISTS directorio;
USE directorio;

CREATE TABLE materias (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  clave    VARCHAR(20) UNIQUE NOT NULL,
  nombre   VARCHAR(100) NOT NULL,
  creditos INT
);

CREATE TABLE docentes (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(100) NOT NULL,
  email       VARCHAR(100) UNIQUE NOT NULL,
  materia_id INT,
  FOREIGN KEY (materia_id) REFERENCES materias(id)
);

INSERT INTO materias (clave, nombre, creditos) VALUES
  ('TC1028', 'Programacion en Python', 5),
  ('TC1004B', 'Implementacion de IoT', 4),
  ('TC2005B', 'Construccion de Software', 5);

------------------------------------------------------------------------
2. INSTALACIÓN Y CONFIGURACIÓN DEL BACKEND
------------------------------------------------------------------------

El backend se aloja en el archivo 'main.py' y expone los servicios bajo 
el prefijo '/api/v1'.

Paso 2.1: Instalar dependencias de Python
Abra una terminal en Codespaces y ejecute el siguiente comando para 
instalar las bibliotecas requeridas:

  pip install Flask mysql-connector-python flask-cors

Paso 2.2: Configurar las variables de entorno
Defina las credenciales de acceso de MySQL en su terminal para que Flask 
pueda consumirlas:

  En Linux / macOS / GitHub Codespaces:
  export DB_HOST="localhost"
  export DB_USER="tu_usuario_mysql"
  export DB_PASSWORD="tu_password_mysql"
  export DB_NAME="directorio"

  En Windows (Command Prompt):
  set DB_HOST=localhost
  set DB_USER=tu_usuario_mysql
  set DB_PASSWORD=tu_password_mysql
  set DB_NAME=directorio

Paso 2.3: Ejecutar la API Flask
Inicie el servidor de desarrollo ejecutando:

  python main.py

El servidor estara escuchando de forma nativa en el puerto 3000.

Paso 2.4: Modificar visibilidad del puerto en Codespaces
1. Dirijase a la pestaña "Ports" (Puertos) en la parte inferior de GitHub 
   Codespaces.
2. Localice el puerto 3000.
3. Haga clic derecho sobre el puerto o en la columna "Port Visibility".
4. Cambie el estado de "Private" a "Public". Esto permitira que el 
   navegador o herramientas externas tengan acceso a los endpoints.

------------------------------------------------------------------------
3. INSTALACIÓN Y CONFIGURACIÓN DEL FRONTEND
------------------------------------------------------------------------

El cliente web esta construido en un unico archivo independiente llamado 
'index.html'.

Paso 3.1: Actualizar URL del backend en el codigo
Abra 'index.html' y localice la constante 'API_BASE_URL' en las primeras 
lineas de la etiqueta <script>. Reemplace su valor con la URL publica 
provista por su entorno de Codespaces para el puerto 3000:

  const API_BASE_URL = 'https://URL_DE_TU_CODESPACE-3000.app.github.dev/api/v1';

Paso 3.2: Levantar el servidor web para el Frontend
Abra una segunda terminal en Codespaces (manteniendo la de Flask en 
ejecucion) y despliegue un servidor HTTP ligero usando el modulo 
integrado de Python:

  python -m http.server 8080

Paso 3.3: Modificar visibilidad del puerto del Frontend
1. Vuelva a la pestaña "Ports" (Puertos) de Codespaces.
2. Localice el puerto 8080.
3. Cambie la propiedad "Port Visibility" de "Private" a "Public".
4. Haga clic en la URL del puerto 8080 o en la opcion "Open in Browser" 
   para visualizar e interactuar con la interfaz de usuario de la 
   aplicacion.

------------------------------------------------------------------------
4. ESTRUCTURA DE ENDPOINTS DISPONIBLES (API REST)
------------------------------------------------------------------------

Materias:
- GET  /api/v1/materias       : Retorna la coleccion completa de materias.
- POST /api/v1/materias       : Registra una nueva materia. Requiere 
                                JSON en el body con 'clave' y 'nombre'.
- GET  /api/v1/materias/<id>  : Obtiene los detalles de una materia.
- PUT  /api/v1/materias/<id>  : Actualiza los datos de una materia.
- DELETE /api/v1/materias/<id>: Remueve una materia si no cuenta con 
                                registros relacionados.

Docentes:
- GET  /api/v1/docentes       : Retorna la coleccion de docentes junto 
                                con el ID de su materia.
- POST /api/v1/docentes       : Registra un nuevo docente. Requiere 
                                JSON con 'nombre' y 'email'.
- DELETE /api/v1/docentes/<id>: Remueve un docente del directorio.
========================================================================
