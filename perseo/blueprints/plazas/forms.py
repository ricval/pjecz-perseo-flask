"""
Plazas, formularios
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

from lib.safe_string import CLAVE_REGEXP


class PlazaForm(FlaskForm):
    """Formulario Plaza"""

    clave = StringField("Clave (hasta 16 caracteres)", validators=[DataRequired(), Regexp(CLAVE_REGEXP)])
    descripcion = StringField("Descripción", validators=[DataRequired(), Length(max=256)])
    guardar = SubmitField("Guardar")
