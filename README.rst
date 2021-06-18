###########
GifSync API
###########

Repository for the Python RESTful API backend written in Flask for the 
GifSync application.

Installation
============

gifsync-api is built with poetry. If you've never used poetry before, install it with:

.. code-block:: console

    pip install --user poetry

Once you have poetry, install the dependencies for gifsync-api (a virtual environment
will be created for you at ``./.venv``):

.. code-block:: console

    # development:
    poetry install -E development
    # production:
    poetry install --no-dev -E production

If you are developing, change the ``.flaskenv`` file to:

.. code-block:: console

    FLASK_APP=gifsync_api:create_app('development')
    FLASK_ENV=development

You must be running Redis and Postgres. Change the ``REDIS_URL`` and 
``SQLALCHEMY_DATABASE_URI`` to point to your Redis and Postgres instances respectively.
A sample environment file is ``.env.sample``. Copy this file to either ``.env.development``,
``.env.testing``, ``.env.production`` depending on how you want to run the app.

A quick and easy way to set up redis db, postgres db, and adminer (for querying postgres)
is to use Docker and docker-compose. For example, the following ``docker-compose.yml`` file::

    version: "3.9"
    services:
    adminer:
        image: adminer
        restart: always
        ports:
        - 8080:8080
    db:
        image: postgres
        restart: always
        ports:
        - 5432:5432
        environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: production
        volumes:
        - ./initdb.sh:/docker-entrypoint-initdb.d/initdb.sh
    redis:
        image: redis
        restart: always
        ports:
        - 6379:6379

With the following ``initdb.sh`` file::

    #!/bin/bash

    set -e

    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE testing;
        CREATE DATABASE development;
    EOSQL

will set up a redis, postgres, and adminer container for you by running::

    docker-compose up -d

To teardown the docker containers::

    docker-compose down

If you are using VSCode, the following settings are recommended::

    {
        "editor.formatOnSave": true,
        "[python]": {
            "editor.defaultFormatter": "ms-python.python",
            "editor.insertSpaces": true,
            "editor.tabSize": 4,
            "editor.codeActionsOnSave": {
            "source.organizeImports": true
            }
        },
        "python.sortImports.args": ["--settings-path", "${workspaceFolder}"],
        "python.formatting.provider": "black",
        "python.linting.pylintEnabled": true,
        "python.linting.pylintArgs": ["--rcfile=${workspaceFolder}/pyproject.toml"],
        "python.sortImports.path": "isort",
        "python.languageServer": "Pylance",
        "python.testing.pytestEnabled": true,
        "python.linting.mypyEnabled": true,
        "python.linting.mypyArgs": ["--config-file=${workspaceFolder}/mypy.ini"],
        "files.associations": {
            "*.toml": "ini"
        }
    }


Testing
=======

Test often during development to check for bugs. This repo is using TDD.

.. code-block:: console

    poetry run pytest

Linting & Formatting
====================

Please lint your code with black, mypy, and pylint:

.. code-block:: console

    poetry run black .
    poetry run mypy .
    poetry run pylint gifsync_api/ tests/ doc/

Please use type annotations for function signatures as often as possible. Docstring
style is Google with Napoleon Sphinx-style references.
