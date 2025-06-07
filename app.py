from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="gestor_tareas"
    )

app = Flask(__name__)
app.secret_key = "1234"

def titulo_valido(titulo):
    return titulo.strip() != ""

def descripcion_valida(descripcion, max_len=300):
    return len(descripcion) <= max_len

def fecha_valida(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        return fecha >= datetime.today().date()
    except ValueError:
        return False

def titulo_duplicado(titulo, id_excluir=None):
    conexion = conectar()
    cursor = conexion.cursor()
    if id_excluir:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE titulo=%s AND id != %s", (titulo, id_excluir))
    else:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE titulo=%s", (titulo,))
    (count,) = cursor.fetchone()
    conexion.close()
    return count > 0

@app.route('/index')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tareas")
    tareas = cursor.fetchall()
    conexion.close()
    return render_template('index.html', tareas=tareas)


@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_vencimiento = request.form['fecha_vencimiento']
        estado = request.form['estado']

        if not titulo_valido(titulo):
            flash('El título no puede estar vacío ni ser solo espacios.')
            return redirect(url_for('agregar'))

        if not fecha_valida(fecha_vencimiento):
            flash('La fecha debe ser hoy o una fecha futura válida.')
            return redirect(url_for('agregar'))

        if not descripcion_valida(descripcion):
            flash('La descripción no puede superar 300 caracteres.')
            return redirect(url_for('agregar'))

        if estado not in ['Pendiente', 'Completada']:
            flash('Estado inválido.')
            return redirect(url_for('agregar'))

        if titulo_duplicado(titulo):
            flash('Ya existe una tarea con ese título.')
            return redirect(url_for('agregar'))

        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO tareas (titulo, descripcion, fecha_vencimiento, estado) VALUES (%s, %s, %s, %s)",
            (titulo.strip(), descripcion, fecha_vencimiento, estado)
        )
        conexion.commit()
        conexion.close()

        flash('Tarea agregada correctamente.')
        return redirect(url_for('index'))
    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha_vencimiento = request.form['fecha_vencimiento']
        estado = request.form['estado']

        if not titulo_valido(titulo):
            flash('El título no puede estar vacío ni ser solo espacios.')
            return redirect(url_for('editar', id=id))

        if not fecha_valida(fecha_vencimiento):
            flash('La fecha debe ser hoy o una fecha futura válida.')
            return redirect(url_for('editar', id=id))

        if not descripcion_valida(descripcion):
            flash('La descripción no puede superar 300 caracteres.')
            return redirect(url_for('editar', id=id))

        if estado not in ['Pendiente', 'Completada']:
            flash('Estado inválido.')
            return redirect(url_for('editar', id=id))

        if titulo_duplicado(titulo, id_excluir=id):
            flash('Ya existe otra tarea con ese título.')
            return redirect(url_for('editar', id=id))

        cursor.execute(
            "UPDATE tareas SET titulo=%s, descripcion=%s, fecha_vencimiento=%s, estado=%s WHERE id=%s",
            (titulo.strip(), descripcion, fecha_vencimiento, estado, id)
        )
        conexion.commit()
        conexion.close()
        flash('Tarea actualizada correctamente.')
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM tareas WHERE id = %s", (id,))
    tarea = cursor.fetchone()
    conexion.close()
    if tarea is None:
        flash('Tarea no encontrada.')
        return redirect(url_for('index'))
    return render_template('editar.html', tarea=tarea)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = %s", (id,))
    conexion.commit()
    conexion.close()
    flash('Tarea eliminada correctamente.')
    return redirect(url_for('index'))
@app.route('/')
def home():
    if 'usuario' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']

        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
        resultado = cursor.fetchone()
        conexion.close()

        if resultado:
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

