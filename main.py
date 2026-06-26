import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode

app = Flask(__name__)
# Habilitar CORS para todos los orígenes
CORS(app, origins="*")

# Configuración de MySQL a través de variables de entorno
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "contrasena")
DB_NAME = os.environ.get("DB_NAME", "directorio")


def get_db_connection():
    """Establece y retorna una conexión a la base de datos MySQL."""
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


# ==============================================================================
# ENDPOINTS: MATERIAS
# ==============================================================================


@app.route("/api/v1/materias", methods=["GET"])
def get_materias():
    """Listar todas las materias."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, clave, nombre, creditos FROM materias")
        materias = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(materias), 200
    except mysql.connector.Error as err:
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/materias", methods=["POST"])
def create_materia():
    """Crear una nueva materia."""
    data = request.get_json() or {}

    # Validación manual básica según especificación (Campos obligatorios)
    if "clave" not in data or "nombre" not in data:
        return (
            jsonify(
                {
                    "code": "BAD_REQUEST",
                    "message": "Los campos 'clave' y 'nombre' son obligatorios.",
                }
            ),
            400,
        )

    clave = data.get("clave")
    nombre = data.get("nombre")
    creditos = data.get("creditos")  # Puede ser None si no se envía

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = (
            "INSERT INTO materias (clave, nombre, creditos) VALUES (%s, %s, %s)"
        )
        cursor.execute(query, (clave, nombre, creditos))
        new_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "id": new_id,
                    "clave": clave,
                    "nombre": nombre,
                    "creditos": creditos,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return (
                jsonify(
                    {
                        "code": "BAD_REQUEST",
                        "message": f"La clave de materia '{clave}' ya existe.",
                    }
                ),
                400,
            )
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/materias/<int:id>", methods=["GET"])
def get_materia_by_id(id):
    """Obtener una materia por ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, clave, nombre, creditos FROM materias WHERE id = %s",
            (id,),
        )
        materia = cursor.fetchone()
        cursor.close()
        conn.close()

        if not materia:
            return (
                jsonify(
                    {
                        "code": "NOT_FOUND",
                        "message": f"Materia con ID {id} no encontrada.",
                    }
                ),
                404,
            )

        return jsonify(materia), 200
    except mysql.connector.Error as err:
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/materias/<int:id>", methods=["PUT"])
def update_materia(id):
    """Actualizar una materia por ID."""
    data = request.get_json() or {}

    if "clave" not in data or "nombre" not in data:
        return (
            jsonify(
                {
                    "code": "BAD_REQUEST",
                    "message": "Los campos 'clave' y 'nombre' son obligatorios.",
                }
            ),
            400,
        )

    clave = data.get("clave")
    nombre = data.get("nombre")
    creditos = data.get("creditos")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar primero si existe el recurso
        cursor.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "code": "NOT_FOUND",
                        "message": f"Materia con ID {id} no encontrada.",
                    }
                ),
                404,
            )

        query = "UPDATE materias SET clave = %s, nombre = %s, creditos = %s WHERE id = %s"
        cursor.execute(query, (clave, nombre, creditos, id))
        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {"id": id, "clave": clave, "nombre": nombre, "creditos": creditos}
            ),
            200,
        )

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return (
                jsonify(
                    {
                        "code": "BAD_REQUEST",
                        "message": f"La clave de materia '{clave}' ya está en uso por otra materia.",
                    }
                ),
                400,
            )
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/materias/<int:id>", methods=["DELETE"])
def delete_materia(id):
    """Eliminar una materia por ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si existe antes de intentar eliminar
        cursor.execute("SELECT id FROM materias WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "code": "NOT_FOUND",
                        "message": f"Materia con ID {id} no encontrada.",
                    }
                ),
                404,
            )

        cursor.execute("DELETE FROM materias WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()

        # Respuesta 204 No Content no lleva cuerpo
        return "", 204

    except mysql.connector.Error as err:
        # Controlar el error de restricción de clave foránea (Id de materia siendo usado en tabla Docentes)
        if err.errno == errorcode.ER_ROW_IS_REFERENCED_2:
            return (
                jsonify(
                    {
                        "code": "BAD_REQUEST",
                        "message": "No se puede eliminar la materia debido a restricciones de clave foránea. Tiene docentes asignados.",
                    }
                ),
                400,
            )
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


# ==============================================================================
# ENDPOINTS: DOCENTES
# ==============================================================================


@app.route("/api/v1/docentes", methods=["GET"])
def get_docentes():
    """Listar todos los docentes."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, email, materia_id FROM docentes")
        docentes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(docentes), 200
    except mysql.connector.Error as err:
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/docentes", methods=["POST"])
def create_docente():
    """Crear un nuevo docente."""
    data = request.get_json() or {}

    if "nombre" not in data or "email" not in data:
        return (
            jsonify(
                {
                    "code": "BAD_REQUEST",
                    "message": "Los campos 'nombre' y 'email' son obligatorios.",
                }
            ),
            400,
        )

    nombre = data.get("nombre")
    email = data.get("email")
    materia_id = data.get("materia_id")  # Puede ser None / Null

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO docentes (nombre, email, materia_id) VALUES (%s, %s, %s)"
        cursor.execute(query, (nombre, email, materia_id))
        new_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "id": new_id,
                    "nombre": nombre,
                    "email": email,
                    "materia_id": materia_id,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        # Controlar error de Email duplicado
        if err.errno == errorcode.ER_DUP_ENTRY:
            return (
                jsonify(
                    {
                        "code": "BAD_REQUEST",
                        "message": f"El email '{email}' ya se encuentra registrado.",
                    }
                ),
                400,
            )
        # Controlar error de Clave Foránea inexistente (materia_id no válida)
        if err.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return (
                jsonify(
                    {
                        "code": "BAD_REQUEST",
                        "message": f"El 'materia_id' ({materia_id}) especificado no existe en la tabla de materias.",
                    }
                ),
                400,
            )
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


@app.route("/api/v1/docentes/<int:id>", methods=["DELETE"])
def delete_docente(id):
    """Eliminar un docente por ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si existe el docente
        cursor.execute("SELECT id FROM docentes WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return (
                jsonify(
                    {
                        "code": "NOT_FOUND",
                        "message": f"Docente con ID {id} no encontrado.",
                    }
                ),
                404,
            )

        cursor.execute("DELETE FROM docentes WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()

        return "", 204
    except mysql.connector.Error as err:
        return (
            jsonify({"code": "INTERNAL_SERVER_ERROR", "message": str(err)}),
            500,
        )


if __name__ == "__main__":
    # Ejecuta el servidor en el puerto 3000 según la especificación del URL base
    app.run(host="0.0.0.0", port=3000, debug=True)