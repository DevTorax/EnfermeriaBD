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
    Hace upsert en la tabla `registros_urgencias` y devuelve True si todo fue OK.
    """
    # Inicializar la app y el contexto de la base de datos
    app = create_app()
    with app.app_context():
        # 1) Leer el DataFrame (encabezado en la fila 4, índice 3)
        if filepath.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(filepath, header=3, engine='openpyxl')
        else:
            df = pd.read_csv(filepath)

        # 2) Filtrar solo sucursal 60
        if 'Codigo Sucursal Afiliado ID' in df.columns:
            df = df[df['Codigo Sucursal Afiliado ID'] == 60]

        # 3) Renombrar columnas para coincidir con atributos del modelo
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

        # 4) Seleccionar solo columnas que existen en el modelo
        expected_cols = [
            'fechaIngreso', 'codigoDiagnostico', 'nombreDiagnostico',
            'tipoDocumento', 'documento', 'fechaNacimiento',
            'primerNombre', 'segundoNombre', 'primerApellido',
            'segundoApellido', 'sexo', 'prestador', 'dxInformado'
        ]
        # Agregar campo constante antes de selección
        df['origenDatos'] = 'URGENCIAS'
        expected_cols.append('origenDatos')
        df = df[[col for col in expected_cols if col in df.columns]]

        # 5) Control de fechas inválidas: convertir con coerción y eliminar NaT
        if 'fechaIngreso' in df.columns:
            df['fechaIngreso'] = pd.to_datetime(df['fechaIngreso'], errors='coerce')
            df = df[df['fechaIngreso'].notnull()]
            df['fechaIngreso'] = df['fechaIngreso'].dt.date
        if 'fechaNacimiento' in df.columns:
            df['fechaNacimiento'] = pd.to_datetime(df['fechaNacimiento'], errors='coerce')
            df = df[df['fechaNacimiento'].notnull()]
            df['fechaNacimiento'] = df['fechaNacimiento'].dt.date

        # 6) Reemplazar NaN restantes con None para MySQL
        df = df.where(pd.notnull(df), None)

        # 7) Eliminar duplicados por PK compuesta
        if 'fechaIngreso' in df.columns and 'documento' in df.columns:
            df = df.drop_duplicates(subset=['fechaIngreso', 'documento'])

        # 8) Upsert en la base de datos
        for _, row in df.iterrows():
            fecha = row['fechaIngreso']
            documento = str(row['documento']).split('.')[0]

            data = row.to_dict()
            data.pop('fechaIngreso', None)
            data.pop('documento', None)
            data.pop('id', None)

            registro = db.session.query(RegistroUrgencias).filter_by(
                fechaIngreso=fecha,
                documento=documento
            ).first()

            if registro:
                # Actualizar campos
                for key, value in data.items():
                    setattr(registro, key, value)
            else:
                # Crear nuevo registro; id autoincremental se omite
                nuevo = RegistroUrgencias(
                    fechaIngreso=fecha,
                    documento=documento,
                    **data
                )
                db.session.add(nuevo)

        # 9) Confirmar transacciones
        db.session.commit()
        # Devuelve la cantidad de registros procesados
        return len(df)
