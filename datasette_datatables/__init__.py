from datasette import hookimpl
from datasette.utils.asgi import Response
import json


def render_datatable(rows, sql):
    data = [dict(r) for r in rows]
    response = {
        "draw": 0,
        "recordsTotal": len(data),
        "recordsFiltered": len(data),
        "data": data,
    }

    return Response.text(json.dumps(response, sort_keys=False))


@hookimpl
def register_output_renderer():
    return {"extension": "datatable", "render": render_datatable}
