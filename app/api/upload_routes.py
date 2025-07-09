# app/api/upload_routes.py

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os

from app.etl.importer import import_urgencias_from_file

upload_bp = Blueprint('upload', __name__)
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=('GET', 'POST'))
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            flash('No seleccionaste ningún archivo.', 'error')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Solo se permiten archivos XLSX, XLS o CSV.', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        
        # ——> Aquí disparamos el ETL y obtenemos la cuenta
        try:
            count = import_urgencias_from_file(filepath)
            flash(f'Importación completada: {count} registros procesados.', 'success')
        except Exception as e:
            flash(f'Error en ETL: {e}', 'error')

        return redirect(url_for('upload.upload_file'))

    return render_template('upload.html')
