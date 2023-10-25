"""
CLI usuarios
"""
from datetime import datetime, timedelta

import click

from lib.pwgen import generar_api_key
from perseo.app import create_app
from perseo.blueprints.autoridades.models import Autoridad
from perseo.blueprints.bitacoras.models import Bitacora
from perseo.blueprints.distritos.models import Distrito
from perseo.blueprints.entradas_salidas.models import EntradaSalida
from perseo.blueprints.modulos.models import Modulo
from perseo.blueprints.permisos.models import Permiso
from perseo.blueprints.roles.models import Rol
from perseo.blueprints.usuarios.models import Usuario
from perseo.blueprints.usuarios_roles.models import UsuarioRol
from perseo.extensions import database, pwd_context

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Usuarios"""


@click.command()
@click.argument("email", type=str)
@click.option("--dias", default=90, help="Cantidad de días para expirar la API Key")
def nueva_api_key(email, dias):
    """Nueva API key"""
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None:
        click.echo(f"No existe el e-mail {email} en usuarios")
        return
    api_key = generar_api_key(usuario.id, usuario.email)
    api_key_expiracion = datetime.now() + timedelta(days=dias)
    usuario.api_key = api_key
    usuario.api_key_expiracion = api_key_expiracion
    usuario.save()
    click.echo(f"Usuario: {usuario.email}")
    click.echo(f"API key: {usuario.api_key}")
    click.echo(f"Expira:  {usuario.api_key_expiracion.strftime('%Y-%m-%d')}")


@click.command()
@click.argument("email", type=str)
def mostrar_api_key(email):
    """Mostrar API Key"""
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None:
        click.echo(f"No existe el e-mail {email} en usuarios")
        return
    click.echo(f"Usuario: {usuario.email}")
    click.echo(f"API key: {usuario.api_key}")
    click.echo(f"Expira:  {usuario.api_key_expiracion.strftime('%Y-%m-%d')}")


@click.command()
@click.argument("email", type=str)
def nueva_contrasena(email):
    """Nueva contraseña"""
    usuario = Usuario.query.filter_by(email=email).first()
    if usuario is None:
        click.echo(f"No existe el e-mail {email} en usuarios")
        return
    contrasena_1 = input("Contraseña: ")
    contrasena_2 = input("De nuevo la misma contraseña: ")
    if contrasena_1 != contrasena_2:
        click.echo("No son iguales las contraseñas. Por favor intente de nuevo.")
        return
    usuario.contrasena = pwd_context.hash(contrasena_1.strip())
    usuario.save()
    click.echo(f"Se ha cambiado la contraseña de {email} en usuarios")


cli.add_command(nueva_api_key)
cli.add_command(mostrar_api_key)
cli.add_command(nueva_contrasena)