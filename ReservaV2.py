import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

# Nombre del objeto flask.
app = Flask(__name__)
CORS(app)

# Configurar la conexión a la base de datos SQLite
DATABASE = 'turnero.db'


class Turnero:

    @staticmethod
    def conectar():
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

    # Crear la tabla de turnos
    @staticmethod
    def crear_tabla_turnos():
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS turnos (
                            id_turno INTEGER PRIMARY KEY,
                            fecha_turno TEXT,
                            hora_inicio_turno TEXT,
                            id_paciente INTEGER,
                            id_profesional INTEGER,
                            FOREIGN KEY (id_paciente) REFERENCES pacientes(id_paciente),
                            FOREIGN KEY (id_profesional) REFERENCES profesionales(id_profesional)
                        )''')
        conn.commit()
        cursor.close()
        conn.close()

    # Crear la tabla de pacientes
    @staticmethod
    def crear_tabla_pacientes():
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                            id_paciente INTEGER PRIMARY KEY ,
                            nombre_paciente TEXT,
                            apellido_paciente TEXT,
                            telefono INTEGER
                        )''')
        conn.commit()
        cursor.close()
        conn.close()

    # Crear la tabla de profesionales
    @staticmethod
    def crear_tabla_profesionales():
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS profesionales (
                            id_profesional INTEGER PRIMARY KEY ,
                            nombre_profesional TEXT,
                            apellido_profesional TEXT,
                            id_especialidad INTEGER,
                            FOREIGN KEY (id_especialidad) REFERENCES especialidades(id_especialidad)
                        )''')
        conn.commit()
        cursor.close()
        conn.close()

    # Crear la tabla de especialidades
    @staticmethod
    def crear_tabla_especialidades():
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS especialidades (
                            id_especialidad INTEGER PRIMARY KEY ,
                            nombre TEXT
                        )''')
        conn.commit()
        cursor.close()
        conn.close()

    # Crear la tabla de agenda
    @staticmethod
    def crear_tabla_agenda():
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS agenda (
                            id INTEGER PRIMARY KEY ,
                            id_profesional INTEGER,
                            fecha TEXT,
                            hora_inicio TEXT,
                            FOREIGN KEY (id_profesional) REFERENCES profesionales(id_profesional)
                        )''')
        conn.commit()
        cursor.close()
        conn.close()

    # Insertar un turno en la base de datos
    @staticmethod
    @app.route('/turnos', methods=['POST'])
    def agregar_turno():
        data = request.get_json() #Diccionario
        if 'id_turno' not in data or 'fecha_turno' not in data or 'hora_inicio_turno' not in data or 'id_paciente' not in data or 'id_profesional' not in data:
            return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
         # Validar si los datos existen en la tabla "agenda"
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agenda WHERE id_profesional = ? AND fecha = ? AND hora_inicio = ?",
                   (data['id_profesional'], data['fecha_turno'], data['hora_inicio_turno']))
        agenda_data = cursor.fetchone()
        if agenda_data is None:
           conn.close()
           return jsonify({'error': 'Los datos no existen en la tabla agenda'}), 400
        
        cursor.execute("SELECT * FROM turnos WHERE id_profesional = ? AND fecha_turno = ? AND hora_inicio_turno = ?",
                   (data['id_profesional'], data['fecha_turno'], data['hora_inicio_turno']))
        agenda_data = cursor.fetchone()
        if agenda_data is not None:
           conn.close()
           return jsonify({'error': 'Los datos  existen en la tabla turnos'}), 400

        try:
            conn = Turnero.conectar()
            cursor = conn.cursor()
            # Verificar si el paciente existe en la tabla "pacientes"
            cursor.execute("SELECT COUNT(*) FROM pacientes WHERE id_paciente = ?", (data['id_paciente'],))
            count = cursor.fetchone()[0]
            if count == 0:
               return jsonify({'error': 'El paciente no existe'}), 400
            cursor.execute("SELECT COUNT(*) FROM turnos WHERE id_turno = ?", (data['id_turno'],))
            count = cursor.fetchone()[0]
            if count == 1:
               return jsonify({'error': 'El ID turno ya existe, ingrese otro'}), 400
            cursor.execute("""
                            INSERT INTO turnos (id_turno,fecha_turno, hora_inicio_turno, id_paciente, id_profesional)
                            VALUES (?, ?, ?, ?,?)
                            """, (data['id_turno'],data['fecha_turno'], data['hora_inicio_turno'], data['id_paciente'], data['id_profesional']))
            conn.commit()
            
            cursor.execute("""
                        DELETE FROM agenda WHERE id_profesional = ? AND fecha = ? and hora_inicio=?""", 
                          (data['id_profesional'], data['fecha_turno'], data['hora_inicio_turno']))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Turno agregado correctamente'}), 200
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        
    # Insertar un paciente en la base de datos
    @staticmethod
    @app.route('/pacientes', methods=['POST'])
    def agregar_paciente():
        data = request.get_json()
        if 'id_paciente' not in data or 'nombre_paciente' not in data or 'apellido_paciente' not in data or 'telefono' not in data:
            return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
        
        try:
            conn = Turnero.conectar()
            cursor = conn.cursor()
            # Verificar si el paciente existe en la tabla "pacientes"
            cursor.execute("SELECT COUNT(*) FROM pacientes WHERE id_paciente = ?", (data['id_paciente'],))
            count = cursor.fetchone()[0]
            if count == 1:
               return jsonify({'error': 'El paciente ya existe'}), 400
            
            
            cursor.execute("""
                            INSERT INTO pacientes (id_paciente, nombre_paciente, apellido_paciente, telefono)
                            VALUES (?, ?, ?, ?)
                            """, (data['id_paciente'], data['nombre_paciente'], data['apellido_paciente'], data['telefono']))
            conn.commit()
            conn.close()
            return jsonify({'message': 'Paciente agregado correctamente'}), 200
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        
    # Consultar y mostrar la agenda de turnos disponibles para un profesional
    @app.route('/agenda/<int:id_profesional>', methods=['GET'])
    def consultar_agenda_profesional(id_profesional):
      try:
       conn = Turnero.conectar()
       cursor = conn.cursor()
       cursor.execute("SELECT DISTINCT a.fecha, a.hora_inicio,  p.nombre_profesional, p.apellido_profesional FROM agenda AS a INNER JOIN profesionales AS p ON a.id_profesional = p.id_profesional WHERE a.id_profesional = ?",
                      (id_profesional,))
       rows = cursor.fetchall()
       if not rows:
        return jsonify({'error': 'Profesional no encontrado'}), 404

       agenda_profesional = []
       for row in rows:
        agenda_profesional.append({
            'fecha': row[0],
            'hora': row[1],
            'nombre profesional': row[2],
            'apellido profesional': row[3]
        })

       return jsonify(agenda_profesional)
      except:
       return jsonify({'error': 'Error al consultar la agenda'}), 500

    # Consultar y mostrar la agenda de todos los profesionales
    @app.route('/agenda', methods=['GET'])
    def consultar_agenda():
      try:
       conn = Turnero.conectar()
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM agenda")
       rows = cursor.fetchall()
       if not rows:
        return jsonify({'error': 'Datos no encontrados'}), 404

       agenda_profesional = []
       for row in rows:
        agenda_profesional.append({
            'Profesional': row['id_profesional'],
            'fecha': row['fecha'],
            'Hora': row['hora_inicio']
            
        })

       return jsonify(agenda_profesional)
      except:
       return jsonify({'error': 'Error al consultar la agenda'}), 500
      
    #Consulta especialidades   
    @app.route('/especialidades', methods=['GET'])
    def consultar_tabla_especialidades():
       try:
         conn = Turnero.conectar()
         cursor = conn.cursor()
         cursor = conn.execute("SELECT  * FROM especialidades ")
         rows = cursor.fetchall()
         if not rows:
            return jsonify({'error': 'Especialidad no encontrado'}), 404
         else:
            especialidades = []
         for row in rows:
            especialidad = {
                'Especialidad': row['id_especialidad'],
                'Nombre': row['nombre']
            }
            especialidades.append(especialidad)

         return jsonify(especialidades)
       except:
         return jsonify({'error': 'Error al consultar especialidades'}), 500
       
    #Consulta pacientes  
    @app.route('/consultapacientes', methods=['GET'])
    def consultar_tabla_pacientes():
       try:
         conn = Turnero.conectar()
         cursor = conn.cursor()
         cursor = conn.execute("SELECT  * FROM pacientes ")
         rows = cursor.fetchall()
         if not rows:
            return jsonify({'error': 'Paciente no encontrado'}), 404
         else:
            pacientes = []
         for row in rows:
            paciente = {
                'Paciente': row['id_paciente'],
                'Nombre': row['nombre_paciente'],
                'Apellido': row['apellido_paciente'],
                'Telefono': row['telefono']
            } #agrega en el arreglo a paciente
            pacientes.append(paciente)

         return jsonify(pacientes)
       except:
         return jsonify({'error': 'Error al consultar pacientes'}), 500
         
       
    # Obtener todos los turnos de la base de datos
    @staticmethod
    @app.route('/consultaturnos', methods=['GET'])
    def consultar_tabla_turnos():
      try:
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM turnos")
        rows = cursor.fetchall()
        if not rows:
            return jsonify({'error': 'Turnos no encontrados'}), 404
        else:
            turnos = []
            for row in rows:
                turno = {
                    'turno': row['id_turno'],
                    'fecha': row['fecha_turno'],
                    'hora': row['hora_inicio_turno'],
                    'paciente': row['id_paciente'],
                    'profesional': row['id_profesional']
                }
                turnos.append(turno)
            return jsonify(turnos)
      except:
        return jsonify({'error': 'Error al consultar turnos'}), 500


    # Obtener un turno específico por su ID
    @staticmethod
    @app.route('/turnos/<int:id_turno>', methods=['GET'])
    def obtener_turno_por_id(id_turno):
        try:
            conn = Turnero.conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM turnos WHERE id_turno = ?", (id_turno,))
            turno = cursor.fetchone()
            cursor.close()
            conn.close()
            if turno:
                return jsonify(turno), 200
            else:
                return jsonify({'message': 'Turno no encontrado'}), 404
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500

    # Eliminar un turno específico por su ID
    @staticmethod
    @app.route('/eliminaturnos/<int:id_turno>', methods=['DELETE'])
    def eliminar_turno(id_turno):
        try:
            conn = Turnero.conectar()
            cursor = conn.cursor()

        # Obtener los datos del turno antes de eliminarlo
            cursor.execute("SELECT id_profesional, fecha_turno, hora_inicio_turno FROM turnos WHERE id_turno = ?", (id_turno,))
            turno = cursor.fetchone()

        # Eliminar el turno de la tabla "turnos"
            cursor.execute("DELETE FROM turnos WHERE id_turno = ?", (id_turno,))
            conn.commit()

        # Insertar los datos en la tabla "agenda"
            cursor.execute("""
            INSERT INTO agenda (id_profesional, fecha, hora_inicio)
            VALUES (?, ?, ?)
        """, (turno['id_profesional'], turno['fecha_turno'], turno['hora_inicio_turno']))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({'message': 'Turno eliminado correctamente y agregado a la agenda'}), 200
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500

          
        
    # Consultar profesional por ID
    @app.route('/profesionales/<int:id_profesional>', methods=['GET'])
    def consultar_por_profesional(id_profesional):
      try:
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT *
            FROM profesionales
            WHERE id_profesional = ?""",
                       (id_profesional,))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({'error': 'Profesional no encontrado'}), 404
        else:
            profesionales = []
            for row in rows:
                profesional = {
                    'ID Profesional': row[0],
                    'Nombre': row[1],
                    'Apellido': row[2],
                    'Especialidad': row[3]
                }
                profesionales.append(profesional)

            return jsonify(profesionales)
      except:
        return jsonify({'error': 'Error al consultar profesional'}), 500



        
    #Consulta tabla profesionales
    @app.route('/profesionales', methods=['GET'])
    def consultar_tabla_profesionales():
     try:
        conn = Turnero.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profesionales")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not rows:
            return jsonify({'error': 'No se encontraron profesionales'}), 404
        
        profesionales = []
        for row in rows:
            profesional = {
                'Profesional': row['id_profesional'],
                'Nombre': row['nombre_profesional'],
                'Apellido': row['apellido_profesional'],
                'Especialidad': row['id_especialidad']
            }
            profesionales.append(profesional)
        
        return jsonify(profesionales), 200
     except:
        return jsonify({'error': 'Error al consultar profesionales'}), 500

       
    #Actualiza la agenda del profesional   
    @app.route('/actualizarAgenda/<int:id_profesional>,<fecha>,<hora_inicio>', methods=['DELETE']) 
    def eliminar_fecha_agenda( id_profesional, fecha, hora_inicio):
        data = request.get_json()
        if 'id_profesional' not in data or 'fecha' not in data or 'hora_inicio' not in data :
          return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
        try:
         conn = Turnero.conectar()
         cursor = conn.cursor()
         cursor.execute("""
                        DELETE FROM agenda WHERE id_profesional = ? AND fecha = ? and hora_inicio=?""", 
                          (data['id_profesional'], data['fecha'], data['hora_inicio']))
         conn.commit()
         cursor.close()
         conn.close()
         return jsonify({'mensaje': 'Fecha eliminada correctamente'}), 201
        except:
         return jsonify({'error': 'Error al eliminar'}), 500
    
    #Busca una especialidad
    @app.route('/buscarEspecialidad/<int:id_especialidad>', methods=['GET'])
    def busca_por_especialidad(id_especialidad):
        try:
         conn = Turnero.conectar()
         cursor = conn.cursor()
         cursor = conn.execute("SELECT DISTINCT a.fecha, a.hora_inicio,  p.nombre_profesional, p.apellido_profesional, p.id_especialidad FROM agenda AS a INNER JOIN profesionales AS p ON a.id_profesional = p.id_profesional WHERE p.id_especialidad = ?")
         rows = cursor.fetchone()
         if rows is None:
            return jsonify({'error': 'Especialidad no encontrada'}), 404
         else:
            return jsonify({
                'fecha': rows['fecha'],
                'hora': rows['hora_inicio'],
                'Nombre': rows['nombre_profesional'],
                'Apellido': rows['apellido_profesional'],
                'Especialidad': rows['id_especialidad']
            })
        except:
          return jsonify({'error': 'Error al consultar especialidad'}), 500
        
    #Modificar paciente
    @app.route('/modificapaciente/<int:id_paciente>', methods=['PUT'])
    def modificar_paciente(id_paciente):
         data = request.get_json()
         if 'nombre_paciente' not in data or 'apellido_paciente' not in data or 'telefono' not in data:
          return jsonify({'error': 'Falta uno o más campos requeridos'}), 400
         try:
           conn = Turnero.conectar()
           cursor = conn.cursor()
           cursor.execute("""SELECT * FROM pacientes WHERE id_paciente=?""", (id_paciente,))
           paciente = cursor.fetchone()
           if paciente is None:
            return jsonify({'error': 'Paciente no encontrado'}), 404
           else:
            cursor.execute("""UPDATE pacientes SET nombre_paciente=?, apellido_paciente=?, telefono=?
                                WHERE id_paciente=?""", (data['nombre_paciente'], data['apellido_paciente'], data['telefono'], id_paciente))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'mensaje': 'Paciente modificado correctamente'}), 200
         except:
           return jsonify({'error': 'Error al modificar al paciente'}), 500




    @app.route('/insertarDatos', methods=['POST'])
    def insertar_datos(conn):
        try:
         conn = Turnero.conectar()
         cursor = conn.cursor()
        
         cursor.execute("INSERT INTO pacientes (id_paciente,nombre_paciente, apellido_paciente, telefono) VALUES (?, ?, ?,?)",
                 (1,"Juan", "Pérez", "123456789"))
         cursor.execute("INSERT INTO pacientes (id_paciente,nombre_paciente, apellido_paciente, telefono) VALUES (?, ?, ?,?)",
                 (2,"María", "Gómez", "987654321"))
         cursor.execute("INSERT INTO pacientes (id_paciente,nombre_paciente, apellido_paciente, telefono) VALUES (?, ?, ?,?)",
                 (3,"Anibal", "Roque", "123456789"))
         cursor.execute("INSERT INTO pacientes (id_paciente,nombre_paciente, apellido_paciente, telefono) VALUES (?, ?, ?,?)",
                 (4,"Evelyn", "Juarez", "123456789"))
         cursor.execute("INSERT INTO pacientes (id_paciente,nombre_paciente, apellido_paciente, telefono) VALUES (?, ?, ?,?)",
                 (5,"Marisa", "Rojas", "123456789"))

         cursor.execute("INSERT INTO especialidades (id_especialidad,nombre) VALUES (?,?)", (45,"Diabetologia",))
         cursor.execute("INSERT INTO especialidades  (id_especialidad,nombre) VALUES (?,?)", (12,"Cardiología",))
         cursor.execute("INSERT INTO especialidades  (id_especialidad,nombre) VALUES (?,?)", (28,"Endocrinologia",))
         cursor.execute("INSERT INTO especialidades  (id_especialidad,nombre) VALUES (?,?)", (31,"Traumatologia",))

         cursor.execute("INSERT INTO profesionales (id_profesional,nombre_profesional, apellido_profesional, id_especialidad) VALUES (?, ?, ?,?)",
                 (1,"Gonzalo", "Rodríguez", 45))
         cursor.execute("INSERT INTO profesionales (id_profesional,nombre_profesional, apellido_profesional, id_especialidad) VALUES (?, ?, ?,?)",
                 (2,"Marina", "Ferrero", 12))
         cursor.execute("INSERT INTO profesionales (id_profesional,nombre_profesional, apellido_profesional, id_especialidad) VALUES (?, ?, ?,?)",
                 (3,"Eugenia", "Moreno", 28))
         cursor.execute("INSERT INTO profesionales (id_profesional,nombre_profesional, apellido_profesional, id_especialidad) VALUES (?, ?, ?,?)",
                 (4,"Carlos", "Bustamante", 31))
         cursor.execute("INSERT INTO profesionales (id_profesional,nombre_profesional, apellido_profesional, id_especialidad) VALUES (?, ?, ?,?)",
                 (5,"Valeria", "Ferri", 12))

         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (1, "2023-07-07", "09:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (1, "2023-07-10", "10:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (2, "2023-07-10", "09:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (2, "2023-07-11", "10:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (3, "2023-07-11", "15:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (3, "2023-07-11", "17:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (4, "2023-07-12", "11:00"))
         cursor.execute("INSERT INTO agenda (id_profesional, fecha, hora_inicio) VALUES (?, ?, ?)",
                 (4 ,"2023-07-12", "15:00"))
         conn.commit()
         cursor.close()
         conn.close()
         return jsonify({'message': 'Datos insertados correctamente'}), 200
        except:
         return jsonify({'error': 'Error al insertar datos'}), 500

if __name__ == '__main__':
    with app.app_context():
        conn = Turnero.conectar()
        Turnero.crear_tabla_turnos()
        Turnero.crear_tabla_pacientes()
        Turnero.crear_tabla_profesionales()
        Turnero.crear_tabla_especialidades()
        Turnero.crear_tabla_agenda()
        Turnero.insertar_datos(conn)

    app.run()



