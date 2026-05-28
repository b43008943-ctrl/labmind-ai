"""Check DB schema for lab_cases table."""
from sqlalchemy import create_engine, text

e = create_engine("postgresql+psycopg://labmind:labmind_secret@localhost:5432/labmind_db")
with e.connect() as conn:
    with open("d:/New folder/ai-backend/schema_check.txt", "w") as f:
        # Check columns
        result = conn.execute(text(
            "SELECT column_name, data_type, udt_name "
            "FROM information_schema.columns "
            "WHERE table_name = 'lab_cases' ORDER BY ordinal_position"
        ))
        f.write("=== lab_cases columns ===\n")
        for row in result:
            f.write(f"  {row[0]}: {row[1]} ({row[2]})\n")

        # Check enums
        result2 = conn.execute(text(
            "SELECT t.typname, e.enumlabel "
            "FROM pg_type t "
            "JOIN pg_enum e ON t.oid = e.enumtypid "
            "ORDER BY t.typname, e.enumsortorder"
        ))
        f.write("\n=== PostgreSQL enums ===\n")
        for row in result2:
            f.write(f"  {row[0]}: {row[1]}\n")

        # Check audit_logs ip_address column
        result3 = conn.execute(text(
            "SELECT column_name, data_type, udt_name "
            "FROM information_schema.columns "
            "WHERE table_name = 'audit_logs' ORDER BY ordinal_position"
        ))
        f.write("\n=== audit_logs columns ===\n")
        for row in result3:
            f.write(f"  {row[0]}: {row[1]} ({row[2]})\n")

print("Done")
