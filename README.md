# pjecz-perseo-flask

PJECZ Perseo es un sistema web hecho con Flask.

## Docker

Ejecutar con contenedores **Docker** en la raíz del proyecto.

```bash
docker-compose up
```

Levantará los servicios de **Flask**, **PostgreSQL** y **Redis**.

Lea el archivo [docker-compose.yml](docker-compose.yml) para más información.

## Requerimientos

Los requerimiento son

- Python 3.11
- PostgreSQL 15
- Redis

## Instalación

Bajar una copia del repositorio

```bash
git clone https://github.com/PJECZ/pjecz-perseo-flask.git
```

Cambiar al directorio del proyecto

```bash
cd pjecz-perseo-flask
```

Crear el entorno virtual

```bash
python3.11 -m venv .venv
```

Ingresar al entorno virtual

```bash
source venv/bin/activate
```

Actualizar el gestor de paquetes **pip**

```bash
pip install --upgrade pip
```

Instalar el paquete **wheel** para compilar las dependencias

```bash
pip install wheel
```

Instalar **poetry** en el entorno virtual si no lo tiene desde el sistema operativo

```bash
pip install poetry
```

Configurar **poetry** para que use el entorno virtual dentro del proyecto

```bash
poetry config virtualenvs.in-project true
```

Instalar las dependencias por medio de **poetry**

```bash
poetry install
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las variables

```bash
# Flask
FLASK_APP=perseo.app
FLASK_DEBUG=1
SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Database
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=pjecz_perseo
DB_USER=adminpjeczperseo
DB_PASS=XXXXXXXX
SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://adminpjeczperseo:XXXXXXXX@127.0.0.1:5432/pjecz_perseo"

# Host
HOST=http://localhost:5000

# Redis
REDIS_URL=redis://127.0.0.1
TASK_QUEUE=pjecz_perseo

# Salt sirve para cifrar el ID con HashID, debe ser igual en la API
SALT=XXXXXXXXXXXXXXXX

# Si esta en PRODUCTION se evita reiniciar la base de datos
DEPLOYMENT_ENVIRONMENT=develop

# Directorio donde se encuentran las quincenas y sus respectivos archivos de explotacion
EXPLOTACION_BASE_DIR=/home/USUARIO/Descargas/NOMINAS
```

Crear un archivo `.bashrc` que se ejecute al iniciar la terminal

```bash
if [ -f ~/.bashrc ]
then
    . ~/.bashrc
fi

if command -v figlet &> /dev/null
then
    figlet Perseo Flask
else
    echo "== Perseo Flask"
fi
echo

if [ -f .env ]
then
    echo "-- Variables de entorno"
    export $(grep -v '^#' .env | xargs)
    echo "   DB_HOST: ${DB_HOST}"
    echo "   DB_PORT: ${DB_PORT}"
    echo "   DB_NAME: ${DB_NAME}"
    echo "   DB_USER: ${DB_USER}"
    echo "   DB_PASS: ${DB_PASS}"
    echo "   DEPLOYMENT_ENVIRONMENT: ${DEPLOYMENT_ENVIRONMENT}"
    echo "   EXPLOTACION_BASE_DIR: ${EXPLOTACION_BASE_DIR}"
    echo "   FLASK_APP: ${FLASK_APP}"
    echo "   HOST: ${HOST}"
    echo "   REDIS_URL: ${REDIS_URL}"
    echo "   SALT: ${SALT}"
    echo "   SECRET_KEY: ${SECRET_KEY}"
    echo "   SQLALCHEMY_DATABASE_URI: ${SQLALCHEMY_DATABASE_URI}"
    echo "   TASK_QUEUE: ${TASK_QUEUE}"
    echo
    export PGHOST=$DB_HOST
    export PGPORT=$DB_PORT
    export PGDATABASE=$DB_NAME
    export PGUSER=$DB_USER
    export PGPASSWORD=$DB_PASS
fi

if [ -d .venv ]
then
    echo "-- Python Virtual Environment"
    source .venv/bin/activate
    echo "   $(python3 --version)"
    export PYTHONPATH=$(pwd)
    echo "   PYTHONPATH: ${PYTHONPATH}"
    echo
    echo "-- Arrancar Flask o RQ Worker"
    alias arrancar="flask run --port=5000"
    alias fondear="rq worker ${TASK_QUEUE}"
    echo "   arrancar = flask run --port=5000"
    echo "   fondear = rq worker ${TASK_QUEUE}"
    echo
    if [ -f cli/app.py ]
    then
        echo "-- Ejecutar el CLI"
        alias cli="python3 ${PWD}/cli/app.py"
        echo "   cli --help"
        echo
    fi
fi
```

## Cargar las variables de entorno y el entorno virtual

Antes de usar el CLI o de arrancar el servidor de **Flask** debe cargar las variables de entorno y el entorno virtual.

```bash
. .bashrc
```

## Base de datos

Previamente debe crear el directorio `seed` y colocar allí los archivos `.csv` para alimentar las tablas principales.

Puede inicializar (eliminar las tablas y crearlas) y alimentar con el **CLI**:

```bash
cli db inicializar
cli db alimentar
```

O puede reiniciar (eliminar las tablas, crearlas y alimentarlas) con:

```bash
cli db reiniciar
```

Alimentar los conceptos

```bash
cli conceptos alimentar
```

Alimentar los bancos

```bash
cli bancos alimentar
```

Alimentar las nominas de la quincena **202320**

```bash
cli nominas alimentar 202320
```

Alimentar las percepciones-deducciones de la quincena **202320**

```bash
cli percepciones_deducciones alimentar 202320
```

Alimentar las cuentas de la quincena **202320**

```bash
cli cuentas alimentar 202320
```

## Tareas en el fondo

Abrir una terminal _Bash_, cargar el `.bashrc` y ejecutar

```bash
fondear
```

Así se ejecutarán las tareas en el fondo con **RQ Worker**.

## Arrancar

Abrir otra terminal _Bash_, cargar el `.bashrc` y ejecutar

```bash
arrancar
```

Así se arrancará el servidor de **Flask**.

Abrir en su navegador de internet <http://localhost:5000>
