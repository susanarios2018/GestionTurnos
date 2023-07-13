#----------------------------------------------
# Importamos el módulo necesario para gestionar
# la base de datos, y los elementos necesarios
# del framework Flask.
#----------------------------------------------
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

# Nombre del objeto flask.
app = Flask(__name__)
CORS(app)


# Nombre del archivo que contiene la base de datos.
DATABASE = "pruebas.db"


#----------------------------------------------
# Conectamos con la base de datos. 
# Retornamos el conector (conn)
#----------------------------------------------
def conectar():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


#----------------------------------------------
# Esta funcion crea la tabla "productos" en la
# base de datos, en caso de que no exista.
#----------------------------------------------
def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    codigo INT PRIMARY KEY,
                    descripcion VARCHAR(255),
                    stock INT,
                    precio FLOAT)
            """)
    conn.commit()
    cursor.close()
    conn.close()


#----------------------------------------------
# Esta funcion da de alta un producto en la
# base de datos.
#----------------------------------------------
@app.route('/productos', methods=['POST'])
def alta_producto():
    data = request.get_json()
    if 'codigo' not in data or 'descripcion' not in data or 'stock' not in data or 'precio' not in data:
        return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
                    INSERT INTO productos(codigo, descripcion, stock, precio)
                    VALUES(?,?,?,?) """,
                    (data['codigo'], data['descripcion'], data['stock'], data['precio']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'mensaje': 'Alta efectuada correctamente'}), 201
    except:
        return jsonify({'error': 'Error al dar de alta el producto'}), 500
    

#----------------------------------------------
# Muestra en la pantalla los datos de un  
# producto a partir de su código.
#----------------------------------------------
@app.route('/productos/<int:codigo>', methods=['GET'])
def consultar_producto(codigo):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos 
                            WHERE codigo=?""", (codigo,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404
        else:
            return jsonify({
                'codigo': producto['codigo'],
                'descripcion': producto['descripcion'],
                'stock': producto['stock'],
                'precio': producto['precio']
            })
    except:
        return jsonify({'error': 'Error al consultar el producto'}), 500


#----------------------------------------------
# Modifica los datos de un producto a partir
# de su código.
#----------------------------------------------
@app.route('/productos/<int:codigo>', methods=['PUT'])
def modificar_producto(codigo):
    data = request.get_json()
    if 'descripcion' not in data or 'stock' not in data or 'precio' not in data:
        return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM productos WHERE codigo=?""", (codigo,))
        producto = cursor.fetchone()
        if producto is None:
            return jsonify({'error': 'Producto no encontrado'}), 404
        else:
            cursor.execute("""UPDATE productos SET descripcion=?, stock=?, precio=?
                                WHERE codigo=?""", (data['descripcion'], data['stock'], data['precio'], codigo))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'mensaje': 'Producto modificado correctamente'}), 200
    except:
        return jsonify({'error': 'Error al modificar el producto'}), 500


#----------------------------------------------
# Lista todos los productos en la base de datos.
#----------------------------------------------
@app.route('/productos', methods=['GET'])
def listar_productos():
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        response = []
        for producto in productos:
            response.append({
                'codigo': producto['codigo'],
                'descripcion': producto['descripcion'],
                'stock': producto['stock'],
                'precio': producto['precio']
            })
        return jsonify(response)
    except:
        return jsonify({'error': 'Error al listar los productos'}), 500



#----------------------------------------------
# Ejecutamos la app
#----------------------------------------------
if __name__ == '__main__':
    crear_tabla()
    app.run()