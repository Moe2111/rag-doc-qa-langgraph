import psycopg
import pytest


@pytest.mark.postgres
def test_pgvector_cosine_distance(database_url: str) -> None:
    with psycopg.connect(database_url) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute("CREATE TEMP TABLE probe (e vector(3))")
        conn.execute("INSERT INTO probe VALUES ('[1,0,0]'), ('[0,1,0]')")
        rows = conn.execute("SELECT e <=> '[1,0,0]' FROM probe ORDER BY 1").fetchall()

    assert [round(r[0], 6) for r in rows] == [0.0, 1.0]
