"""Quick test: hit register endpoint and print the full response."""
import sys
sys.path.insert(0, ".")

# First, test the hash_password directly
print("=== Test 1: hash_password ===")
try:
    from app.core.security import hash_password, verify_password
    h = hash_password("TestPass123!")
    print(f"PASS: hash={h[:40]}...")
    v = verify_password("TestPass123!", h)
    print(f"PASS: verify={v}")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback; traceback.print_exc()

# Second, test the full register flow at the service level
print("\n=== Test 2: Full register flow ===")
try:
    from app.db.database import SessionLocal
    from app.services.auth_service import AuthService
    from app.schemas.auth import RegisterRequest

    db = SessionLocal()
    svc = AuthService(db)
    req = RegisterRequest(
        email="diagtest2@labmind.ai",
        password="TestPass123!",
        full_name="Diag Test",
    )
    try:
        user = svc.register(req, ip="127.0.0.1")
        print(f"PASS: user.id={user.id}, email={user.email}, role={user.role}")
    except Exception as e:
        print(f"FAIL at register: {e}")
        import traceback; traceback.print_exc()
        db.rollback()

    # Cleanup
    try:
        from app.db.models.user import User
        from app.db.models.audit_log import AuditLog
        u = db.query(User).filter(User.email == "diagtest2@labmind.ai").first()
        if u:
            db.query(AuditLog).filter(AuditLog.user_id == u.id).delete()
            db.delete(u)
            db.commit()
            print("(cleaned up test user)")
    except Exception as e2:
        print(f"Cleanup error: {e2}")
    finally:
        db.close()
except Exception as e:
    print(f"FAIL: {e}")
    import traceback; traceback.print_exc()
