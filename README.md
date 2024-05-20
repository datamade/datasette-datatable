# datasette-datatable

Export Datasette records in a form that the [DataTables library](https://datatables.net/) understands.

## Installation

Install this plugin in the same environment as Datasette. Note that this plugin is built
against the development version of datasette, not the one released on PyPi.

    $ datasette install datasette-datatable

## Usage

Having installed this plugin, every table and query will gain a new `.datatable` export link.

You can also construct these URLs directly: `/dbname/tablename.datatable`

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-datatable
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install https://github.com/simonw/datasette/archive/refs/heads/main.zip
    pip install -e '.[test]'

To run the tests:

    pytest
