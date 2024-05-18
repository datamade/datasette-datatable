from datasette.app import Datasette
import httpx
import pytest
import sqlite_utils
import textwrap


@pytest.mark.asyncio
async def test_plugin_is_installed():
    app = Datasette([], memory=True).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/plugins.json")
        assert 200 == response.status_code
        installed_plugins = {p["name"] for p in response.json()}
        assert "datasette-datatables" in installed_plugins


@pytest.mark.asyncio
async def test_datasette_datatables(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "test.db"
    db = sqlite_utils.Database(db_path)
    db["dogs"].insert_all(
        [
            {"id": 1, "name": "Cleo", "age": 5, "weight": 48.4},
            {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
        ],
        pk="id",
    )
    app = Datasette([str(db_path)]).app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/test/dogs.datatable")
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 0,
            "recordsTotal": 2,
            "recordsFiltered": 2,
            "data": [
                {"id": 1, "name": "Cleo", "age": 5, "weight": 48.4},
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
            ],
        }

        response = await client.get(
            "http://localhost/test/dogs.datatable?start=1&length=1"
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 0,
            "recordsTotal": 1,
            "recordsFiltered": 1,
            "data": [
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
            ],
        }

        response = await client.get(
            "http://localhost/test.datatable?sql=select id, name, age, weight from dogs order by id limit 101"
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 0,
            "recordsTotal": 2,
            "recordsFiltered": 2,
            "data": [
                {"id": 1, "name": "Cleo", "age": 5, "weight": 48.4},
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
            ],
        }

        response = await client.get(
            "http://localhost/test.datatable?sql=select id, name, age, weight from dogs order by id limit 101&start=1&length=1&draw=10"
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 10,
            "recordsTotal": 1,
            "recordsFiltered": 1,
            "data": [
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
            ],
        }

        response = await client.get(
            "http://localhost/test.datatable?sql=select id, name, age, weight from dogs order by id limit 101&start=1&draw=10"
        )
        assert response.status_code == 400
        assert response.json()
        assert response.json() == {
            "draw": 10,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": [],
            "error": "Can't use the start param without setting the length parameter",
        }

        response = await client.get(
            "http://localhost/test.datatable?sql=select id, name, age, weight from dogs order by id limit 101&start=1&length=1&draw=10"
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 10,
            "recordsTotal": 1,
            "recordsFiltered": 1,
            "data": [
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
            ],
        }

        response = await client.get(
            "http://localhost/test.datatable?sql=select id, name, age, weight from dogs order by id limit 101&draw=10&columns[2][orderable]=true&order[0][column]=2&order[0][dir]=asc&columns[0][orderable]=true&order[1][column]=0&order[1][dir]=asc"
        )
        assert response.status_code == 200
        assert response.json()
        assert response.json() == {
            "draw": 10,
            "recordsTotal": 2,
            "recordsFiltered": 2,
            "data": [
                {"id": 2, "name": "Pancakes", "age": 4, "weight": 33.2},
                {"id": 1, "name": "Cleo", "age": 5, "weight": 48.4},
            ],
        }
