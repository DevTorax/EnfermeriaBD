# app/etl/importer.py

import os
import pandas as pd
from app import create_app
from app.extensions import db
from app.models import RegistroUrgencias


def import_urgencias_from_file(filepath):
    """
    Importa un Excel o CSV de urgencias ya subido en 'uploads/'.
    Filtra por sucursal 60 y controla fechas inválidas.
    Hace upsert en la tabla `registros_urgencias` y devuelve tupla:
    (total_registros_filtrados, registros_insertados)
    """
    # Inicializar la app y el contexto de la base de datos
    app = create_app()
    with app.app_context():
        # Leer el DataFrame (header en fila 4)
        if filepath.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath, header=3, engine='openpyxl')
        else:
            df = pd.read_csv(filepath)

        # Filtrar solo sucursal 60
        if 'Codigo Sucursal Afiliado ID' in df.columns:
            df = df[df['Codigo Sucursal Afiliado ID'] == 60]

        # Renombrar columnas a atributos del modelo
        rename_map = {
            "Fecha Autorizacion ID": "fechaIngreso",
            "Codigo Diagnostico Eps Op ID": "codigoDiagnostico",
            "Diagnostico Eps Desc ID": "nombreDiagnostico",
            "Codigo Tipo Documento Op ID": "tipoDocumento",
            "Numero De Documento ID": "documento",
            "Fecha Nacimiento ID": "fechaNacimiento",
            "Primer Nombre ID": "primerNombre",
            "Segundo Nombre ID": "segundoNombre",
            "Primer Apellido ID": "primerApellido",
            "Segundo Apellido ID": "segundoApellido",
            "Sexo Cd ID": "sexo",
            "Descripcion Prestacion ID": "prestador",
            "Dx ID": "dxInformado"
        }
        df = df.rename(columns=rename_map)

        # Columnas que usaremos
        expected_cols = [
            'fechaIngreso', 'codigoDiagnostico', 'nombreDiagnostico',
            'tipoDocumento', 'documento', 'fechaNacimiento',
            'primerNombre', 'segundoNombre', 'primerApellido',
            'segundoApellido', 'sexo', 'prestador', 'dxInformado'
        ]
        # Agregar campo constante
        df['origenDatos'] = 'URGENCIAS'
        expected_cols.append('origenDatos')
        df = df[[c for c in expected_cols if c in df.columns]]

        # Control de fechas inválidas
        if 'fechaIngreso' in df.columns:
            df['fechaIngreso'] = pd.to_datetime(df['fechaIngreso'], errors='coerce')
            df = df[df['fechaIngreso'].notnull()]
            df['fechaIngreso'] = df['fechaIngreso'].dt.date
        if 'fechaNacimiento' in df.columns:
            df['fechaNacimiento'] = pd.to_datetime(df['fechaNacimiento'], errors='coerce')
            df = df[df['fechaNacimiento'].notnull()]
            df['fechaNacimiento'] = df['fechaNacimiento'].dt.date

        # Reemplazar NaN por None
        df = df.where(pd.notnull(df), None)

        # Conteo antes del upsert
        total_records = len(df)
        inserted = 0

        # Upsert
        for _, row in df.iterrows():
            fecha = row['fechaIngreso']
            documento = str(row['documento']).split('.')[0]
            data = row.to_dict()
            data.pop('fechaIngreso', None)
            data.pop('documento', None)
            data.pop('id', None)

            existing = db.session.query(RegistroUrgencias).filter_by(
                fechaIngreso=fecha,
                documento=documento
            ).first()
            if existing:
                for k, v in data.items(): setattr(existing, k, v)
            else:
                nuevo = RegistroUrgencias(
                    fechaIngreso=fecha,
                    documento=documento,
                    **data
                )
                db.session.add(nuevo)
                inserted += 1

        db.session.commit()
        # Retornar total y nuevos insertados
        return total_records, inserted
