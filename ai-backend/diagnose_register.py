"""
Quick diagnostic to find the exact 500 error in the register flow.
Run from ai-backend/ with venv active:
  python diagnose_register.py
"""
import traceback
import sys

print("=" * 50)
print("  LabMind Register Diagnostic")
print("=" * 50)

# Test 1: bcrypt + passlib
print("\n[TEST 1] passlib + bcrypt hash_password")
try:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    h = ctx.hash("test_password")
    print(f"  PASS — hash: {h[:30]}...")
    v = ctx.verify("test_password", h) 
    print(f"  PASS — verify: {v}")
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}")
    traceback.print_exc()

# Test 2: DB connection
print("\n[TEST 2] Database connection")
try:
    from app.db.database import engine
    with engine.connect() as conn:
        result = conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        print(f"  PASS — SELECT 1 returned: {result.scalar()}")
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}")
    traceback.print_exc()

# Test 3: User insert
print("\n[TEST 3] Create user via the actual register flow")
try:
    from app.db.database import SessionLocal
    from app.services.auth_service import AuthService
    from app.schemas.auth import RegisterRequest

    db = SessionLocal()
    try:
        svc = AuthService(db)
        req = RegisterRequest(
            email="diag_test@labmind.ai",
            password="DiagTest123!",
            full_name="Diagnostic User",
        )
        user = svc.register(req, ip="127.0.0.1")
        print(f"  PASS — User created: id={user.id}, email={user.email}")
    except Exception as e:
        print(f"  FAIL — {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            from app.db.models.user import User
            u = db.query(User).filter(User.email == "diag_test@labmind.ai").first()
            if u:
                db.delete(u)
                db.commit()
                print("  (cleanup: test user deleted)")
        except:
            pass
        db.close()
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}")
    traceback.print_exc()

# Test 4: Audit log INET type with IPv6
print("\n[TEST 4] Audit log with IPv6 loopback (::1)")
try:
    from app.db.database import SessionLocal
    from app.db.models.audit_log import AuditLog
    db = SessionLocal()
    try:
        log = AuditLog(
            action="test.diagnostic",
            ip_address="::1",
        )
        db.add(log)
        db.commit()
        print(f"  PASS — audit log inserted with ::1, id={log.id}")
        db.delete(log)
        db.commit()
        print("  (cleanup: test audit log deleted)")
    except Exception as e:
        print(f"  FAIL — {type(e).__name__}: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
except Exception as e:
    print(f"  FAIL — {type(e).__name__}: {e}")
    traceback.print_exc()

print("\n" + "=" * 50)
print("  DIAGNOSTIC COMPLETE")
print("=" * 50)
