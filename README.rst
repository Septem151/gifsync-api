###########
GifSync API
###########

Repository for the Python RESTful API backend written in Flask for the 
GifSync application.

Installation
============

gifsync-api is built with poetry. If you've never used poetry before, install it with:

..code-block:: console

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

