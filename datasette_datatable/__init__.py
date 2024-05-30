import re
import urllib.parse
from collections import defaultdict

from datasette import hookimpl
from datasette.utils import validate_sql_select
from datasette.utils.asgi import Request, Response


class InvalidQuery(Exception):
    ...


def _parse_params(params):

    columns = defaultdict(lambda: defaultdict(dict))
    orderings = defaultdict(dict)

    for param, value in params.items():
        if param.startswith(("column", "order")):

            if value.isnumeric():
                value = int(value)
            elif value == "true":
                value = True
            elif value == "false":
                value = False

            _, index_str, *rest = [each for each in re.split(r"[\[\]]+", param) if each]
            index = int(index_str)

            if param.startswith("column"):
                if len(rest) == 1:
                    (flag,) = rest
                    columns[index][flag] = value
                elif len(rest) == 2:
                    flag, option = rest
                    assert flag == "search"
                    if option == "value":
                        columns[index]["search"] = value

            if param.startswith("order"):
                (flag,) = rest
                orderings[index][flag] = value

    return columns, orderings


def adjust_query(wrapped_query, params):

    columns, orderings = _parse_params(params)

    search_clauses = []

    global_search_clauses = []
    if search_value := params.get("search[value]"):
        for field in columns.values():
            if field["searchable"]:
                global_search_clauses.append(f"{field['data']} LIKE '%{search_value}%'")

    if global_search_clauses:
        search_clauses.append(f"({' OR '.join(global_search_clauses)})")

    column_search_clauses = []
    for field in columns.values():
        if (query := field.get("search")) and field["searchable"]:
            column_search_clauses.append(f"{field['data']} LIKE '%{query}%'")

    if column_search_clauses:
        search_clauses.append(" AND ".join(column_search_clauses))

    if search_clauses:
        wrapped_query += f" WHERE {' AND '.join(search_clauses)}"

    filtered_query = wrapped_query

    order_clauses = []
    for key in sorted(orderings.keys()):
        ordering = orderings[key]
        if not columns[ordering["column"]]["orderable"]:
            raise InvalidQuery(
                f"Column {columns[ordering]['column']} that you are trying to order on has not been specified as orderable"
            )

        order_clauses.append(f"{columns[ordering['column']]['data']} {ordering['dir']}")

    if order_clauses:
        wrapped_query += f" ORDER BY {', '.join(order_clauses)}"

    if limit := params.pop("length", 100):
        # check that limit is an integer
        # let's handle all this validation with jsonschema
        wrapped_query += f" limit {limit}"

    if offset := params.pop("start", None):
        # check that start is an integer
        wrapped_query += f" offset {offset}"

    return wrapped_query, filtered_query


async def datatable_table(datasette, request, scope, send, receive):

    url_route = scope["url_route"]["kwargs"]
    url_route["format"] = "datatable"
    table = url_route.pop("table")

    path = f"/{url_route['database']}.datatable"

    scope["path"] = path
    scope["raw_path"] = path.encode("latin-1")

    params = {k: request.args[k] for k in request.args.keys()}
    params["sql"] = f"select * from {table}"

    scope["query_string"] = urllib.parse.urlencode(params).encode("latin-1")

    return await datatable_database(datasette, scope, send, receive)


async def datatable_database(datasette, scope, send, receive):

    from datasette.views.database import DatabaseView

    scope["url_route"]["kwargs"]["format"] = "datatable"

    original_request = Request(scope, receive)
    params = {k: original_request.args[k] for k in original_request.args.keys()}

    original_query = params["sql"]
    validate_sql_select(original_query)

    try:
        wrapped_query, filtered_query = adjust_query(
            f"select * from ({original_query}) as og", params
        )
    except InvalidQuery as exc:
        return Response.json(
            {
                "draw": int(params.get("draw", 0)),
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": str(exc),
            },
            status=400,
        )

    params["original_sql"] = original_query
    params["filtered_sql"] = filtered_query

    params["sql"] = wrapped_query

    scope["query_string"] = urllib.parse.urlencode(params).encode("latin-1")
    new_request = Request(scope, receive)

    return await DatabaseView()(request=new_request, datasette=datasette)


async def render_datatable(sql, rows, request, datasette, database):

    original_query = request.args.get("original_sql")
    total_result = await datasette.execute(
        database, f"select count(*) as total from ({original_query}) as og"
    )
    total = total_result.first()["total"]

    filtered_query = request.args.get("filtered_sql")
    filtered_result = await datasette.execute(
        database, f"select count(*) as filtered from ({filtered_query}) as og"
    )
    filtered = filtered_result.first()["filtered"]

    data = [dict(r) for r in rows]
    response = {
        "draw": int(request.args.get("draw", 0)),
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": data,
    }

    return Response.json(response)


@hookimpl
def register_routes():
    return [
        (
            r"/(?P<database>[^\/\.]+)/(?P<table>[^\/\.]+)\.datatable$",
            datatable_table,
        ),
        (
            r"/(?P<database>[^\/\.]+)\.datatable$",
            datatable_database,
        ),
    ]


@hookimpl
def register_output_renderer():
    return {"extension": "datatable", "render": render_datatable}
