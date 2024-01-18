"""
CLI Timbrados
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import click

from lib.safe_string import QUINCENA_REGEXP, safe_string
from perseo.app import create_app
from perseo.blueprints.nominas.models import Nomina
from perseo.blueprints.personas.models import Persona
from perseo.blueprints.quincenas.models import Quincena
from perseo.extensions import database

XML_TAG_CFD_PREFIX = "{http://www.sat.gob.mx/cfd/4}"
XML_TAG_TFD_PREFIX = "{http://www.sat.gob.mx/TimbreFiscalDigital}"
XML_TAG_NOMINA_PREFIX = "{http://www.sat.gob.mx/nomina12}"

CFDI_EMISOR_RFC = os.environ.get("CFDI_EMISOR_RFC")
CFDI_EMISOR_NOMBRE = os.environ.get("CFDI_EMISOR_NOMBRE")
CFDI_EMISOR_REGFIS = os.environ.get("CFDI_EMISOR_REGFIS")
TIMBRADOS_BASE_DIR = os.environ.get("TIMBRADOS_BASE_DIR")

app = create_app()
app.app_context().push()
database.app = app


@click.group()
def cli():
    """Timbrados"""


@click.command()
@click.argument("quincena_clave", type=str)
@click.argument("tipo", type=str, default="SALARIO")
@click.option("--subdir", type=str, default=None)
def actualizar(quincena_clave: str, tipo: str, subdir: str):
    """Actualizar las nominas con los timbrados de una quincena"""

    # Validar el directorio donde espera encontrar los archivos de explotacion
    if TIMBRADOS_BASE_DIR is None:
        click.echo("ERROR: Variable de entorno TIMBRADOS_BASE_DIR no definida.")
        sys.exit(1)

    # Validar quincena
    if re.match(QUINCENA_REGEXP, quincena_clave) is None:
        click.echo("ERROR: Quincena inválida.")
        sys.exit(1)

    # Validar tipo
    tipo = safe_string(tipo)
    if tipo not in ["AGUINALDO", "SALARIO", "APOYO ANUAL"]:
        click.echo("ERROR: Tipo inválido.")
        sys.exit(1)

    # Por defecto, el directorio es <quincena_clave>
    directorio = quincena_clave

    # Si el tipo es APOYO ANUAL, el directorio es <quincena_clave>ApoyoAnual
    if tipo == "APOYO ANUAL":
        directorio = f"{quincena_clave}ApoyosAnuales"

    # Si el tipo es AGUINALDO, el directorio es <quincena_clave>Aguinaldo
    if tipo == "AGUINALDO":
        directorio = f"{quincena_clave}Aguinaldos"

    # Validar que exista el directorio
    if subdir == "":
        timbrados_dir = Path(TIMBRADOS_BASE_DIR, directorio)
    else:
        timbrados_dir = Path(TIMBRADOS_BASE_DIR, directorio, subdir)
    if not timbrados_dir.exists():
        click.echo(f"ERROR: No existe el directorio {timbrados_dir}")
        sys.exit(1)

    # Inicializar listas de errores
    emisor_rfc_no_coincide = []
    emisor_nombre_no_coincide = []
    emisor_regfis_no_coincide = []
    receptor_rfc_no_encontrado = []
    receptor_rfc_no_coincide = []
    nomina_no_encontrada = []

    # Inicializar contadores
    actualizaciones_contador = 0
    procesados_contador = 0

    # Recorrer los archivos con extension xml
    for archivo in timbrados_dir.glob("*.xml"):
        # Obtener el nombre del archivo
        archivo_nombre = archivo.name
        click.echo(f"  {archivo_nombre}")

        # Ruta al archivo XML
        archivo_xml = Path(timbrados_dir, archivo_nombre)

        # Obtener el RFC que esta en los primeros 13 caracteres del nombre del archivo
        rfc_en_nombre = archivo_nombre[:13]

        # Parsear el archivo XML
        tree = ET.parse(archivo_xml)
        root = tree.getroot()

        # Estructura del CFDI version 4.0
        # - cfdi:Comprobante [xmlns:xsi, xmlns:nomina12, xmlns:cfdi, Version, Serie, Folio, Fecha, SubTotal, Descuento, Moneda,
        #     Total, TipoDeComprobante, Exportacion, MetodoPago, LugarExpedicion, Sello, Certificado]
        #   - cfdi:Emisor [Rfc, Nombre, RegimenFiscal]
        #   - cfdi:Receptor [Rfc, Nombre, DomicilioFiscalReceptor, RegimenFiscalReceptor, UsoCFDI]
        #   - cfdi:Conceptos
        #     - cfdi:Concepto [ClaveProdServ, Cantidad, ClaveUnidad, Descripcion, ValorUnitario, Importe, Descuento, ObjetoImp]
        #   - cfdi:Complemento
        #     - tfd:TimbreFiscalDigital [Version, UUID, FechaTimbrado, RfcProvCertif, SelloCFD, NoCertificadoSAT, SelloSAT]
        #     - nomina12:Nomina [Version, TipoNomina, FechaPago, FechaInicialPago, FechaFinalPago, NumDiasPagados,
        #         TotalDeducciones, TotalOtrosPagos]
        #       - nomina12:Emisor [RegistroPatronal]
        #         - nomina12:EntidadSNCF [OrigenRecurso]
        #       - nomina12:Receptor [Curp, NumSeguridadSocial, FechaInicioRelLaboral, Antigüedad, TipoContrato, Sindicalizado,
        #           TipoJornada, TipoRegimen, NumEmpleado, Departamento, Puesto, RiesgoPuesto, PeriodicidadPago, Banco,
        #           CuentaBancaria, SalarioBaseCotApor, SalarioDiarioIntegrado, ClaveEntFed]
        #       - nomina12:Deducciones [TotalOtrasDeducciones]
        #         - nomina12:Deduccion [TipoDeduccion, Clave, Concepto, Importe]
        #       - nomina12:OtrosPagos
        #         - nomina12:OtroPago [TipoOtroPago, Clave, Concepto, Importe]

        # Validar que el tag raiz sea cfdi:Comprobante
        if root.tag != f"{XML_TAG_CFD_PREFIX}Comprobante":
            click.echo(click.style("    ERROR: Tag raiz no es cfdi:Comprobante", fg="red"))
            continue

        # Obtener datos de cfdi:Comprobante
        cfdi_comprobante_version = None
        if "Version" in root.attrib:
            cfdi_comprobante_version = root.attrib["Version"]
            click.echo(click.style(f"    Version: {cfdi_comprobante_version}", fg="green"))
        cfdi_comprobante_serie = None
        if "Serie" in root.attrib:
            cfdi_comprobante_serie = root.attrib["Serie"]
            click.echo(click.style(f"    Serie: {cfdi_comprobante_serie}", fg="green"))
        cfdi_comprobante_folio = None
        if "Folio" in root.attrib:
            cfdi_comprobante_folio = root.attrib["Folio"]
            click.echo(click.style(f"    Folio: {cfdi_comprobante_folio}", fg="green"))
        cfdi_comprobante_fecha = None
        if "Fecha" in root.attrib:
            cfdi_comprobante_fecha = root.attrib["Fecha"]
            click.echo(click.style(f"    Fecha: {cfdi_comprobante_fecha}", fg="green"))

        # Inicializar variables de los datos que se van a obtener
        cfdi_emisor_rfc = None
        cfdi_emisor_nombre = None
        cfdi_emisor_regimen_fiscal = None
        cfdi_receptor_rfc = None
        cfdi_receptor_nombre = None
        tfd_version = None
        tfd_uuid = None
        tfd_fecha_timbrado = None
        tfd_sello_cfd = None
        tfd_num_cert_sat = None
        tfd_sello_sat = None

        # Bucle por los elementos de root
        for element in root.iter():
            # Mostrar el tag
            # click.echo(click.style(f"    {element.tag}", fg="blue"))

            # Obtener datos de Emisor
            if element.tag == f"{XML_TAG_CFD_PREFIX}Emisor":
                if "Rfc" in element.attrib:
                    cfdi_emisor_rfc = element.attrib["Rfc"]
                    click.echo(click.style(f"      Emisor RFC: {cfdi_emisor_rfc}", fg="green"))
                if "Nombre" in element.attrib:
                    cfdi_emisor_nombre = element.attrib["Nombre"]
                    click.echo(click.style(f"      Emisor Nombre: {cfdi_emisor_nombre}", fg="green"))
                if "RegimenFiscal" in element.attrib:
                    cfdi_emisor_regimen_fiscal = element.attrib["RegimenFiscal"]
                    click.echo(click.style(f"      Emisor Reg. Fis.: {cfdi_emisor_regimen_fiscal}", fg="green"))

            # Obtener datos de Receptor
            if element.tag == f"{XML_TAG_CFD_PREFIX}Receptor":
                if "Rfc" in element.attrib:
                    cfdi_receptor_rfc = element.attrib["Rfc"]
                    click.echo(click.style(f"      Receptor RFC: {cfdi_receptor_rfc}", fg="green"))
                if "Nombre" in element.attrib:
                    cfdi_receptor_nombre = element.attrib["Nombre"]
                    click.echo(click.style(f"      Receptor Nombre: {cfdi_receptor_nombre}", fg="green"))

            # Obtener datos de TimbreFiscalDigital
            if element.tag == f"{XML_TAG_TFD_PREFIX}TimbreFiscalDigital":
                if "Version" in element.attrib:
                    tfd_version = element.attrib["Version"]
                    click.echo(click.style(f"      TFD Version: {tfd_version}", fg="green"))
                if "UUID" in element.attrib:
                    tfd_uuid = element.attrib["UUID"]
                    click.echo(click.style(f"      TFD UUID: {tfd_uuid}", fg="green"))
                if "FechaTimbrado" in element.attrib:
                    tfd_fecha_timbrado = element.attrib["FechaTimbrado"]
                    click.echo(click.style(f"      TFD Fecha Timbrado: {tfd_fecha_timbrado}", fg="green"))
                if "SelloCFD" in element.attrib:
                    tfd_sello_cfd = element.attrib["SelloCFD"]
                    click.echo(click.style(f"      TFD Sello CFD: {tfd_sello_cfd}", fg="green"))
                if "NoCertificadoSAT" in element.attrib:
                    tfd_num_cert_sat = element.attrib["NoCertificadoSAT"]
                    click.echo(click.style(f"      TFD Num. Cert. SAT: {tfd_num_cert_sat}", fg="green"))
                if "SelloSAT" in element.attrib:
                    tfd_sello_sat = element.attrib["SelloSAT"]
                    click.echo(click.style(f"      TFD Sello SAT: {tfd_sello_sat}", fg="green"))

        # Si NO se encontro el Receptor RFC, se agrega a la lista de errores y se omite
        if cfdi_receptor_rfc is None:
            receptor_rfc_no_encontrado.append(archivo_nombre)
            continue

        # Si el Receptor RFC no coincide con el RFC en el nombre del archivo, se agrega a la lista de errores y se omite
        if cfdi_receptor_rfc != rfc_en_nombre:
            receptor_rfc_no_coincide.append(archivo_nombre)
            continue

        # Si el Emisor RFC no coincide con CFDI_EMISOR_RFC, se agrega a la lista de errores y se omite
        if cfdi_emisor_rfc != CFDI_EMISOR_RFC:
            emisor_rfc_no_coincide.append(archivo_nombre)
            continue

        # Si el Emisor Nombre no coincide con CFDI_EMISOR_NOMBRE, se agrega a la lista de errores y se omite
        if cfdi_emisor_nombre != CFDI_EMISOR_NOMBRE:
            emisor_nombre_no_coincide.append(archivo_nombre)
            continue

        # Si el Emisor Regimen Fiscal no coincide con CFDI_EMISOR_REGIMEN_FISCAL, se agrega a la lista de errores y se omite
        if cfdi_emisor_regimen_fiscal != CFDI_EMISOR_REGFIS:
            emisor_regfis_no_coincide.append(archivo_nombre)
            continue

        # Consultar la Nomina
        nomina = (
            Nomina.query.join(Persona)
            .join(Quincena)
            .filter(Persona.rfc == cfdi_receptor_rfc)
            .filter(Quincena.clave == quincena_clave)
            .filter(Nomina.tipo == tipo)
            .filter(Nomina.estatus == "A")
            .order_by(Nomina.id.desc())
            .first()
        )

        # Si NO se encuentra registro en Nomina
        if nomina is None:
            nomina_no_encontrada.append(cfdi_receptor_rfc)
            continue

        # Inicializar bandera hay_cambios
        hay_cambios = False

        # Si tfd_version es diferente, hay_cambios sera verdadero
        if tfd_version is not None and nomina.tfd_version != tfd_version:
            click.echo(click.style(f"    TFD Version: {nomina.tfd_version} != {tfd_version}", fg="yellow"))
            nomina.tfd_version = tfd_version
            hay_cambios = True

        # Si tfd_uuid es diferente, hay_cambios sera verdadero
        if tfd_uuid is not None and nomina.tfd_uuid != tfd_uuid:
            click.echo(click.style(f"    TFD UUID: {nomina.tfd_uuid} != {tfd_uuid}", fg="yellow"))
            nomina.tfd_uuid = tfd_uuid
            hay_cambios = True

        # Para comparar tfd_fecha_timbrado hay que convertir el datetime a string como 2024-01-17T14:19:16
        tfd_fecha_timbrado_str = ""
        if nomina.tfd_fecha_timbrado is not None:
            tfd_fecha_timbrado_str = nomina.tfd_fecha_timbrado.strftime("%Y-%m-%dT%H:%M:%S")

        # Si tfd_fecha_timbrado es diferente, hay_cambios sera verdadero
        if tfd_fecha_timbrado is not None and tfd_fecha_timbrado_str != tfd_fecha_timbrado:
            click.echo(click.style(f"    TFD Fecha Timbrado: {tfd_fecha_timbrado_str} != {tfd_fecha_timbrado}", fg="yellow"))
            nomina.tfd_fecha_timbrado = tfd_fecha_timbrado
            hay_cambios = True

        # Si tfd_sello_cfd es diferente, hay_cambios sera verdadero
        if tfd_sello_cfd is not None and nomina.tfd_sello_cfd != tfd_sello_cfd:
            click.echo(click.style(f"    TFD Sello CFD: {nomina.tfd_sello_cfd} != {tfd_sello_cfd}", fg="yellow"))
            nomina.tfd_sello_cfd = tfd_sello_cfd
            hay_cambios = True

        # Si tfd_num_cert_sat es diferente, hay_cambios sera verdadero
        if tfd_num_cert_sat is not tfd_num_cert_sat and nomina.tfd_num_cert_sat != tfd_num_cert_sat:
            click.echo(click.style(f"    TFD Num. Cert. SAT: {nomina.tfd_num_cert_sat} != {tfd_num_cert_sat}", fg="yellow"))
            nomina.tfd_num_cert_sat = tfd_num_cert_sat
            hay_cambios = True

        # Si tfd_sello_sat es diferente, hay_cambios sera verdadero
        if tfd_sello_sat is not None and nomina.tfd_sello_sat != tfd_sello_sat:
            click.echo(click.style(f"    TFD Sello SAT: {nomina.tfd_sello_sat} != {tfd_sello_sat}", fg="yellow"))
            nomina.tfd_sello_sat = tfd_sello_sat
            hay_cambios = True

        # Si hay_cambios, cargar el contenido XML y actualizar el registro en Nomina
        if hay_cambios:
            # Cargar el contenido XML
            with open(archivo_xml, "r", encoding="utf8") as f:
                nomina.tfd = f.read()

            # Actualizar el registro en Nomina
            nomina.save()
            actualizaciones_contador += 1

        # Incrementar procesados_contador
        procesados_contador += 1

    # Si hubo errores en emisor_rfc_no_coincide, se muestran
    if len(emisor_rfc_no_coincide) > 0:
        click.echo(click.style(f"  En {len(emisor_rfc_no_coincide)} Emisor RFC NO es {CFDI_EMISOR_RFC}", fg="yellow"))
        click.echo(click.style(f"  {', '.join(emisor_rfc_no_coincide)}", fg="yellow"))

    # Si hubo errores en emisor_nombre_no_coincide, se muestran
    if len(emisor_nombre_no_coincide) > 0:
        click.echo(click.style(f"  En {len(emisor_nombre_no_coincide)} Emisor Nombre NO es {CFDI_EMISOR_NOMBRE}", fg="yellow"))
        click.echo(click.style(f"  {', '.join(emisor_nombre_no_coincide)}", fg="yellow"))

    # Si hubo errores en emisor_regimen_fiscal_no_coincide, se muestran
    if len(emisor_regfis_no_coincide) > 0:
        click.echo(click.style(f"  En {len(emisor_regfis_no_coincide)} Emisor RegFis NO es {CFDI_EMISOR_REGFIS}", fg="yellow"))
        click.echo(click.style(f"  {', '.join(emisor_regfis_no_coincide)}", fg="yellow"))

    # Si hubo errores en receptor_rfc_no_encontrado, se muestran
    if len(receptor_rfc_no_encontrado) > 0:
        click.echo(click.style(f"  En {len(receptor_rfc_no_encontrado)} Receptor RFC NO se encuentra", fg="yellow"))
        click.echo(click.style(f"  {', '.join(receptor_rfc_no_encontrado)}", fg="yellow"))

    # Si hubo errores en receptor_rfc_no_coincide, se muestran
    if len(receptor_rfc_no_coincide) > 0:
        click.echo(click.style(f"  En {len(receptor_rfc_no_coincide)} Receptor RFC NO coincide", fg="yellow"))
        click.echo(click.style(f"  {', '.join(receptor_rfc_no_coincide)}", fg="yellow"))

    # Mostrar mensaje de termino
    click.echo(click.style(f"  Se actualizaron {actualizaciones_contador} registros en Nominas.", fg="green"))
    click.echo(click.style(f"  Se procesaron {procesados_contador} archivos XML.", fg="green"))


cli.add_command(actualizar)