# app/models.py
from sqlalchemy.ext.automap import automap_base
from .extensions import db

Base = automap_base()

def init_models():
    """
    Debe llamarse dentro de app.app_context(), después de db.init_app(app).
    """
    # 1) Reflect + Automap en un solo paso
    Base.prepare(db.engine, reflect=True)

    # DEBUG opcional: ver todas las clases automapeadas
    print("Clases automapeadas:", list(Base.classes.keys()))

    # 2) Asignar sólo las que existen, usando get para evitar errores
    globals().update({
        'RegistroUrgencias':       Base.classes.get('registros_urgencias'),
        'Estados':                 Base.classes.get('estados'),
        'Plantillas':              Base.classes.get('plantillas'),
        'Gestiones':               Base.classes.get('gestiones'),
        'Usuarios':                Base.classes.get('usuarios'),
        # **Aquí la tabla con acento**:
        'ClasificacionDiagnostico': Base.classes.get('clasificación_diagnosticos'),
    })
