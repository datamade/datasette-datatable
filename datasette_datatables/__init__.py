import urllib.parse
import re
from collections import defaultdict

from datasette import hookimpl
from datasette.utils.asgi import Request, Response


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

    original_request = Request(scope, receive)
    params = {k: original_request.args[k] for k in original_request.args.keys()}

    wrapped_query = f"select * from ({params['sql']}) as og"

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
                    columns[index]["search"][flag] = value

            if param.startswith("order"):
                (flag,) = rest
                orderings[index][flag] = value

    order_clauses = []
    for key in sorted(orderings.keys()):
        ordering = orderings[key]
        assert columns[ordering["column"]]["orderable"]
        order_clauses.append(f"{ordering['column'] + 1} {ordering['dir']}")

    if order_clauses:
        wrapped_query += f" ORDER BY {', '.join(order_clauses)}"

    if limit := params.pop("length", None):
        wrapped_query += f" limit {limit}"

    if offset := params.pop("start", None):
        if limit:
            wrapped_query += f" offset {offset}"
        else:
            return Response.json(
                {
                    "draw": int(original_request.args.get("draw", 0)),
                    "recordsTotal": 0,
                    "recordsFiltered": 0,
                    "data": [],
                    "error": "Can't use the start param without setting the length parameter",
                },
                status=400,
            )

    params["sql"] = wrapped_query

    scope["query_string"] = urllib.parse.urlencode(params).encode("latin-1")
    new_request = Request(scope, receive)

    return await DatabaseView()(request=new_request, datasette=datasette)


def render_datatable(rows, sql, data, request):
    data = [dict(r) for r in rows]
    response = {
        "draw": int(request.args.get("draw", 0)),
        "recordsTotal": len(data),
        "recordsFiltered": len(data),
        "data": data,
    }

    return Response.json(response)


@hookimpl
def register_routes():
    return [
        (
            r"/(?P<database>[^\/\.]+)/(?P<table>[^\/\.]+)(\.datatable)?$",
            datatable_table,
        ),
        (r"/(?P<database>[^\/\.]+)(\.(?P<format>\w+))?$", datatable_database),
    ]


@hookimpl
def register_output_renderer():
    return {"extension": "datatable", "render": render_datatable}
