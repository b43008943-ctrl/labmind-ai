"""Test if psycopg TypeInfo works with our DB."""
from sqlalchemy import create_engine, event, text

DB_URL = "postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db"
eng = create_engine(DB_URL, echo=False)

@event.listens_for(eng, "connect")
def on_connect(dbapi_conn, conn_record):
    print(f"dbapi_conn type: {type(dbapi_conn)}")
    try:
        from psycopg.types import TypeInfo
        info = TypeInfo.fetch(dbapi_conn, "department_enum")
        if info:
            print(f"  department_enum OID: {info.oid}")
            info.register(dbapi_conn)
            print("  Registered OK")
        else:
            print("  department_enum NOT found")
    except Exception as ex:
        print(f"  ERROR: {type(ex).__name__}: {ex}")

with eng.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(f"Query OK: {result.scalar()}")

    # Now try an actual insert-like operation
    result2 = conn.execute(text("SELECT 'hematology'::department_enum"))
    print(f"Enum cast OK: {result2.scalar()}")
