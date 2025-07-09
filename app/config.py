from dotenv import load_dotenv
import os


load_dotenv()  # Carga .env al entorno

class Config:
    # URI de la base de datos en formato SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'cambia_esta_clave')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # límite 16MB (opcional)