"""
Flask Extensions
"""
# from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from passlib.context import CryptContext

csrf = CSRFProtect()
database = SQLAlchemy()
# login_manager = LoginManager()
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "des_crypt"], deprecated="auto")
