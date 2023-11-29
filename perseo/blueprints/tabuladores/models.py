"""
Tabuladores, modelos
"""
from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from lib.universal_mixin import UniversalMixin
from perseo.extensions import database


class Tabulador(database.Model, UniversalMixin):
    """Tabulador"""

    # Nombre de la tabla
    __tablename__ = "tabuladores"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Clave foránea
    puesto_id = Column(Integer, ForeignKey("puestos.id"), index=True, nullable=False)
    puesto = relationship("Puesto", back_populates="tabuladores")

    # Columnas que hacen una combinación única
    modelo = Column(Integer, nullable=False)
    nivel = Column(Integer, nullable=False)
    quinquenio = Column(Integer, nullable=False)

    # Columnas independientes
    sueldo_base = Column(Numeric(precision=24, scale=4), nullable=False)
    incentivo = Column(Numeric(precision=24, scale=4), nullable=False)
    monedero = Column(Numeric(precision=24, scale=4), nullable=False)
    rec_cul_dep = Column(Numeric(precision=24, scale=4), nullable=False)
    sobresueldo = Column(Numeric(precision=24, scale=4), nullable=False)
    rec_dep_cul_gravado = Column(Numeric(precision=24, scale=4), nullable=False)
    rec_dep_cul_excento = Column(Numeric(precision=24, scale=4), nullable=False)
    ayuda_transp = Column(Numeric(precision=24, scale=4), nullable=False)
    monto_quinquenio = Column(Numeric(precision=24, scale=4), nullable=False)
    total_percepciones = Column(Numeric(precision=24, scale=4), nullable=False)
    salario_diario = Column(Numeric(precision=24, scale=4), nullable=False)
    prima_vacacional_mensual = Column(Numeric(precision=24, scale=4), nullable=False)
    aguinaldo_mensual = Column(Numeric(precision=24, scale=4), nullable=False)
    prima_vacacional_mensual_adicional = Column(Numeric(precision=24, scale=4), nullable=False)
    total_percepciones_integrado = Column(Numeric(precision=24, scale=4), nullable=False)
    salario_diario_integrado = Column(Numeric(precision=24, scale=4), nullable=False)
    fecha = Column(Date(), nullable=False)

    # Hijos
    personas = relationship("Persona", back_populates="tabulador")

    def __repr__(self):
        """Representación"""
        return f"<Tabulador {self.id}>"