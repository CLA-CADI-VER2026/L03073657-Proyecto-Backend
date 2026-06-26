import os
from datetime import datetime
from decimal import Decimal
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import IntegrityError, Error as MySQLError

app = Flask(__name__)
CORS(app, origins="*")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', 'contrasena'),
        database=os.environ.get('DB_NAME', 'tienda_simple'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

# -----------------------------------------------------------------------------
# HELPERS DE SOPORTE (Formateo y Errores)
# -----------------------------------------------------------------------------
def make_error(code, message, status_code):
    """Genera una respuesta de error bajo el esquema unificado del YAML."""
    return jsonify({"code": code, "message": message}), status_code

def format_row(row):
    """Convierte tipos no serializables de MySQL (datetime, Decimal) a tipos estándar."""
    if not row:
        return row
    for key, value in row.items():
        if isinstance(value, datetime):
            row[key] = value.strftime('%Y-%m-%dT%H:%M:%SZ')
        elif isinstance(value, Decimal):
            row[key] = float(value)
    return row

# -----------------------------------------------------------------------------
# ENDPOINTS: CLIENTES
# -----------------------------------------------------------------------------
@app.route('/api/v1/clientes', methods=['GET'])
def get_clientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([format_row(row) for row in rows]), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/clientes', methods=['POST'])
def create_cliente():
    data = request.get_json() or {}
    nombre = data.get('nombre')
    email = data.get('email')
    telefono = data.get('telefono')

    if not nombre or not email:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: nombre y email.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO clientes (nombre, email, telefono) VALUES (%s, %s, %s)"
        cursor.execute(query, (nombre, email, telefono))
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (new_id,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(cliente)), 201
    except IntegrityError as e:
        return make_error("BAD_REQUEST", f"Error de integridad (posible email duplicado): {str(e)}", 400)
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/clientes/<int:id_cliente>', methods=['GET'])
def get_cliente(id_cliente):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()

        if not cliente:
            return make_error("NOT_FOUND", f"Cliente con ID {id_cliente} no encontrado.", 404)

        return jsonify(format_row(cliente)), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/clientes/<int:id_cliente>', methods=['PUT'])
def update_cliente(id_cliente):
    data = request.get_json() or {}
    nombre = data.get('nombre')
    email = data.get('email')
    telefono = data.get('telefono')

    if not nombre or not email:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: nombre y email.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (id_cliente,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Cliente con ID {id_cliente} no encontrado.", 404)

        query = "UPDATE clientes SET nombre = %s, email = %s, telefono = %s WHERE id_cliente = %s"
        cursor.execute(query, (nombre, email, telefono, id_cliente))
        conn.commit()

        cursor.execute("SELECT id_cliente, nombre, email, telefono, created_at FROM clientes WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(cliente)), 200
    except IntegrityError as e:
        return make_error("BAD_REQUEST", f"Error de integridad en la actualización: {str(e)}", 400)
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/clientes/<int:id_cliente>', methods=['DELETE'])
def delete_cliente(id_cliente):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (id_cliente,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Cliente con ID {id_cliente} no encontrado.", 404)

        cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        conn.commit()
        cursor.close()
        conn.close()

        return '', 204
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)


# -----------------------------------------------------------------------------
# ENDPOINTS: PRODUCTOS
# -----------------------------------------------------------------------------
@app.route('/api/v1/productos', methods=['GET'])
def get_productos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([format_row(row) for row in rows]), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/productos', methods=['POST'])
def create_producto():
    data = request.get_json() or {}
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    stock = data.get('stock', 0)

    if not nombre or precio is None:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: nombre y precio.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (nombre, descripcion, precio, stock))
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (new_id,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(producto)), 201
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/productos/<int:id_producto>', methods=['GET'])
def get_producto(id_producto):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (id_producto,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()

        if not producto:
            return make_error("NOT_FOUND", f"Producto con ID {id_producto} no encontrado.", 404)

        return jsonify(format_row(producto)), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/productos/<int:id_producto>', methods=['PUT'])
def update_producto(id_producto):
    data = request.get_json() or {}
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    precio = data.get('precio')
    stock = data.get('stock', 0)

    if not nombre or precio is None:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: nombre y precio.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Producto con ID {id_producto} no encontrado.", 404)

        query = "UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, stock = %s WHERE id_producto = %s"
        cursor.execute(query, (nombre, descripcion, precio, stock, id_producto))
        conn.commit()

        cursor.execute("SELECT id_producto, nombre, descripcion, precio, stock FROM productos WHERE id_producto = %s", (id_producto,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(producto)), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/productos/<int:id_producto>', methods=['DELETE'])
def delete_producto(id_producto):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Producto con ID {id_producto} no encontrado.", 404)

        cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
        conn.commit()
        cursor.close()
        conn.close()

        return '', 204
    except IntegrityError as e:
        return make_error("BAD_REQUEST", f"No se puede eliminar el producto porque está referenciado en un pedido (RESTRICT): {str(e)}", 400)
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)


# -----------------------------------------------------------------------------
# ENDPOINTS: PEDIDOS
# -----------------------------------------------------------------------------
@app.route('/api/v1/pedidos', methods=['GET'])
def get_pedidos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([format_row(row) for row in rows]), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/pedidos', methods=['POST'])
def create_pedido():
    data = request.get_json() or {}
    id_cliente = data.get('id_cliente')
    id_producto = data.get('id_producto')
    cantidad = data.get('cantidad', 1)
    total = data.get('total')

    if not id_cliente or not id_producto or total is None:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: id_cliente, id_producto y total.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO pedidos (id_cliente, id_producto, cantidad, total) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (id_cliente, id_producto, cantidad, total))
        conn.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (new_id,))
        pedido = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(pedido)), 201
    except IntegrityError as e:
        return make_error("BAD_REQUEST", f"Error de clave foránea. Verifique que id_cliente e id_producto existan: {str(e)}", 400)
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/pedidos/<int:id_pedido>', methods=['GET'])
def get_pedido(id_pedido):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        pedido = cursor.fetchone()
        cursor.close()
        conn.close()

        if not pedido:
            return make_error("NOT_FOUND", f"Pedido con ID {id_pedido} no encontrado.", 404)

        return jsonify(format_row(pedido)), 200
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/pedidos/<int:id_pedido>', methods=['PUT'])
def update_pedido(id_pedido):
    data = request.get_json() or {}
    id_cliente = data.get('id_cliente')
    id_producto = data.get('id_producto')
    cantidad = data.get('cantidad', 1)
    total = data.get('total')

    if not id_cliente or not id_producto or total is None:
        return make_error("BAD_REQUEST", "Faltan campos obligatorios: id_cliente, id_producto y total.", 400)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id_pedido FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Pedido con ID {id_pedido} no encontrado.", 404)

        query = "UPDATE pedidos SET id_cliente = %s, id_producto = %s, cantidad = %s, total = %s WHERE id_pedido = %s"
        cursor.execute(query, (id_cliente, id_producto, cantidad, total, id_pedido))
        conn.commit()

        cursor.execute("SELECT id_pedido, id_cliente, id_producto, cantidad, total, fecha FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        pedido = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify(format_row(pedido)), 200
    except IntegrityError as e:
        return make_error("BAD_REQUEST", f"Error de clave foránea en la actualización: {str(e)}", 400)
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)

@app.route('/api/v1/pedidos/<int:id_pedido>', methods=['DELETE'])
def delete_pedido(id_pedido):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_pedido FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return make_error("NOT_FOUND", f"Pedido con ID {id_pedido} no encontrado.", 404)

        cursor.execute("DELETE FROM pedidos WHERE id_pedido = %s", (id_pedido,))
        conn.commit()
        cursor.close()
        conn.close()

        return '', 204
    except MySQLError as e:
        return make_error("INTERNAL_SERVER_ERROR", str(e), 500)


if __name__ == '__main__':
    # La API correrá en el puerto 3000 tal como define el base server del YAML
    app.run(host='0.0.0.0', port=3000, debug=True)