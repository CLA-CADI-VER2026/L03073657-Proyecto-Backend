import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
from decimal import Decimal
from datetime import datetime

app = Flask(__name__)
# Habilitar CORS para todos los orígenes según el requisito
CORS(app, origins="*")

# Configuración de base de datos mediante variables de entorno con valores por defecto
DB_HOST = os.environ.get('MYSQL_HOST', 'localhost')
DB_USER = os.environ.get('MYSQL_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'contrasena')
DB_NAME = os.environ.get('MYSQL_DATABASE', 'tienda_simple')
DB_PORT = int(os.environ.get('MYSQL_PORT', 3306))

def get_db_connection():
    """Establece y retorna una conexión a la base de datos MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

def make_error_response(code, message):
    """Estructura las respuestas de error usando el esquema 'Error' del YAML."""
    return jsonify({"code": code, "message": message}), code

def serialize_row(row, date_fields=[], decimal_fields=[]):
    """Convierte tipos de datos de MySQL (datetime, Decimal) a formatos válidos para JSON."""
    if not row:
        return row
    for field in date_fields:
        if row.get(field) and isinstance(row[field], (datetime,)):
            # Formato ISO 8601 requerido por OpenAPI (ej. 2026-06-25T09:00:00Z)
            row[field] = row[field].strftime('%Y-%m-%dT%H:%M:%SZ')
    for field in decimal_fields:
        if row.get(field) is not None and isinstance(row[field], Decimal):
            row[field] = float(row[field])
    return row

# Global Error Handlers para asegurar que siempre respondamos con el esquema Error
@app.errorhandler(400)
def bad_request(e):
    return make_error_response(400, "La sintaxis de la solicitud es inválida o faltan campos obligatorios.")

@app.errorhandler(404)
def not_found(e):
    return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")

@app.errorhandler(500)
def internal_server_error(e):
    return make_error_response(500, f"Ocurrió un error inesperado en el servidor: {str(e)}")


# ==============================================================================
# ENDPOINTS: CLIENTES
# ==============================================================================

@app.route('/api/v1/clientes', methods=['GET'])
def get_clientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        clientes = [serialize_row(row, date_fields=['created_at']) for row in rows]
        return jsonify(clientes), 200
    except mysql.connector.Error as err:
        return make_error_response(400, f"Error en la base de datos: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/clientes', methods=['POST'])
def create_cliente():
    data = request.get_json(silent=True)
    if not data or 'nombre' not in data or 'email' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'nombre' y/o 'email'.")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "INSERT INTO clientes (nombre, email, telefono) VALUES (%s, %s, %s)"
        values = (data['nombre'], data['email'], data.get('telefono'))
        cursor.execute(query, values)
        conn.commit()
        
        new_id = cursor.lastrowid
        
        # Obtener el cliente recién creado para retornar el objeto completo con su fecha
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (new_id,))
        cliente = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify(serialize_row(cliente, date_fields=['created_at'])), 201
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return make_error_response(400, "El email proporcionado ya está registrado por otro cliente.")
        return make_error_response(400, f"Error al insertar en la base de datos: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/clientes/<int:id>', methods=['GET'])
def get_cliente_by_id(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (id,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not cliente:
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        return jsonify(serialize_row(cliente, date_fields=['created_at'])), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    data = request.get_json(silent=True)
    if not data or 'nombre' not in data or 'email' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'nombre' y/o 'email'.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si existe el cliente
        cursor.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        query = "UPDATE clientes SET nombre = %s, email = %s, telefono = %s WHERE id_cliente = %s"
        values = (data['nombre'], data['email'], data.get('telefono'), id)
        cursor.execute(query, values)
        conn.commit()
        
        # Obtener datos actualizados
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (id,))
        cliente = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return jsonify(serialize_row(cliente, date_fields=['created_at'])), 200
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DUP_ENTRY:
            return make_error_response(400, "El email proporcionado ya está en uso por otro cliente.")
        return make_error_response(400, f"Error al actualizar la base de datos: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        # ON DELETE CASCADE en MySQL se encargará de los pedidos vinculados
        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return '', 204
    except Exception as e:
        return make_error_response(500, str(e))


# ==============================================================================
# ENDPOINTS: PRODUCTOS
# ==============================================================================

@app.route('/api/v1/productos', methods=['GET'])
def get_productos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        productos = [serialize_row(row, decimal_fields=['precio']) for row in rows]
        return jsonify(productos), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/productos', methods=['POST'])
def create_producto():
    data = request.get_json(silent=True)
    if not data or 'nombre' not in data or 'precio' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'nombre' y/o 'precio'.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (%s, %s, %s, %s)"
        values = (data['nombre'], data.get('descripcion'), data['precio'], data.get('stock', 0))
        cursor.execute(query, values)
        conn.commit()
        
        new_id = cursor.lastrowid
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (new_id,))
        producto = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return jsonify(serialize_row(producto, decimal_fields=['precio'])), 201
    except mysql.connector.Error as err:
        return make_error_response(400, f"Error en los datos suministrados: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/productos/<int:id>', methods=['GET'])
def get_producto_by_id(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (id,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not producto:
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        return jsonify(serialize_row(producto, decimal_fields=['precio'])), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    data = request.get_json(silent=True)
    if not data or 'nombre' not in data or 'precio' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'nombre' y/o 'precio'.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        query = "UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, stock = %s WHERE id_producto = %s"
        values = (data['nombre'], data.get('descripcion'), data['precio'], data.get('stock', 0), id)
        cursor.execute(query, values)
        conn.commit()
        
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (id,))
        producto = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return jsonify(serialize_row(producto, decimal_fields=['precio'])), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return '', 204
    except mysql.connector.Error as err:
        # Captura específica para la violación de clave foránea RESTRICT definida en el SQL de 'pedidos'
        if err.errno == errorcode.ER_ROW_IS_REFERENCED_2:
            return make_error_response(400, "No se puede eliminar el producto porque tiene pedidos activos vinculados.")
        return make_error_response(400, f"Error en la solicitud: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))


# ==============================================================================
# ENDPOINTS: PEDIDOS
# ==============================================================================

@app.route('/api/v1/pedidos', methods=['GET'])
def get_pedidos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        pedidos = [serialize_row(row, date_fields=['fecha'], decimal_fields=['total']) for row in rows]
        return jsonify(pedidos), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/pedidos', methods=['POST'])
def create_pedido():
    data = request.get_json(silent=True)
    if not data or 'id_cliente' not in data or 'id_producto' not in data or 'total' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'id_cliente', 'id_producto' y/o 'total'.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "INSERT INTO pedidos (id_cliente, id_producto, cantidad, total) VALUES (%s, %s, %s, %s)"
        values = (data['id_cliente'], data['id_producto'], data.get('cantidad', 1), data['total'])
        cursor.execute(query, values)
        conn.commit()
        
        new_id = cursor.lastrowid
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (new_id,))
        pedido = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return jsonify(serialize_row(pedido, date_fields=['fecha'], decimal_fields=['total'])), 201
    except mysql.connector.Error as err:
        # Validación de Claves Foráneas de Clientes o Productos inexistentes
        if err.errno in (errorcode.ER_NO_REFERENCED_ROW, errorcode.ER_NO_REFERENCED_ROW_2):
            return make_error_response(400, "No se pudo registrar el pedido. El id_cliente o id_producto especificado no existe.")
        return make_error_response(400, f"Error en los datos del pedido: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/pedidos/<int:id>', methods=['GET'])
def get_pedido_by_id(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (id,))
        pedido = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not pedido:
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        return jsonify(serialize_row(pedido, date_fields=['fecha'], decimal_fields=['total'])), 200
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/pedidos/<int:id>', methods=['PUT'])
def update_pedido(id):
    data = request.get_json(silent=True)
    if not data or 'id_cliente' not in data or 'id_producto' not in data or 'total' not in data:
        return make_error_response(400, "Faltan campos requeridos obligatorios: 'id_cliente', 'id_producto' y/o 'total'.")
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_pedido FROM pedidos WHERE id_pedido = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        query = "UPDATE pedidos SET id_cliente = %s, id_producto = %s, cantidad = %s, total = %s WHERE id_pedido = %s"
        values = (data['id_cliente'], data['id_producto'], data.get('cantidad', 1), data['total'], id)
        cursor.execute(query, values)
        conn.commit()
        
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (id,))
        pedido = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return jsonify(serialize_row(pedido, date_fields=['fecha'], decimal_fields=['total'])), 200
    except mysql.connector.Error as err:
        if err.errno in (errorcode.ER_NO_REFERENCED_ROW, errorcode.ER_NO_REFERENCED_ROW_2):
            return make_error_response(400, "No se pudo actualizar el pedido. El id_cliente o id_producto especificado no existe.")
        return make_error_response(400, f"Error en los datos provistos: {err.msg}")
    except Exception as e:
        return make_error_response(500, str(e))

@app.route('/api/v1/pedidos/<int:id>', methods=['DELETE'])
def delete_pedido(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_pedido FROM pedidos WHERE id_pedido = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error_response(404, "El recurso solicitado con el ID provisto no existe.")
            
        cursor.execute("DELETE FROM pedidos WHERE id_pedido = %s", (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return '', 204
    except Exception as e:
        return make_error_response(500, str(e))


if __name__ == '__main__':
    # Ejecución de la app en el puerto 3000 especificado en el OpenAPI YAML
    app.run(host='0.0.0.0', port=3000, debug=True)