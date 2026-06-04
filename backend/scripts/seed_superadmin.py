from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.roles import Role
from app.core.security import hash_password
from app.db.models import User

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, future=True)

def main():
    if not settings.SUPERADMIN_EMAIL or not settings.SUPERADMIN_PASSWORD:
        raise SystemExit("Set SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD in .env")

    with Session(engine) as db:
        existing = db.scalar(select(User).where(User.email == settings.SUPERADMIN_EMAIL))
        if existing:
            existing.role = Role.SUPERADMIN
            print("Updated existing user to superadmin")
        else:
            admin = User(
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
                role=Role.SUPERADMIN,
            )
            db.add(admin)
            print("Created superadmin user")
        db.commit()

if __name__ == "__main__":
    main()