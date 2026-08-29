"""Cipta akaun super_admin pertama.

Guna: uv run python scripts/bootstrap_super_admin.py
Boleh guna env: SUPER_ADMIN_USERNAME, SUPER_ADMIN_NAMA_FIRST,
SUPER_ADMIN_NAMA_LAST, SUPER_ADMIN_PASSWORD atau flags:
--username --nama-first --nama-last --password.

Idempotent: enggan mencipta jika super_admin sudah wujud, kecuali --force.
Akaun pertama mesti menukar kata laluan selepas log masuk
(mesti_tukar_kata_laluan=true).
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository


def _baca_env(nama: str, default: str = "") -> str:
    return os.environ.get(nama, default)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cipta akaun super_admin pertama")
    parser.add_argument("--username", default=_baca_env("SUPER_ADMIN_USERNAME"))
    parser.add_argument("--nama-first", default=_baca_env("SUPER_ADMIN_NAMA_FIRST"))
    parser.add_argument("--nama-last", default=_baca_env("SUPER_ADMIN_NAMA_LAST"))
    parser.add_argument("--password", default=_baca_env("SUPER_ADMIN_PASSWORD"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.username or not args.nama_first or not args.nama_last or not args.password:
        print(
            "Guna: uv run python scripts/bootstrap_super_admin.py "
            "--username x --nama-first x --nama-last x --password x"
        )
        print(
            "atau set SUPER_ADMIN_USERNAME, SUPER_ADMIN_NAMA_FIRST, "
            "SUPER_ADMIN_NAMA_LAST, SUPER_ADMIN_PASSWORD."
        )
        sys.exit(1)

    if len(args.password) < 8:
        print("Kata laluan mesti sekurang-kurangnya 8 aksara.")
        sys.exit(1)

    db = SessionLocal()
    try:
        repository = UserRepository()
        wujud = db.scalar(select(User).where(User.role == "super_admin").limit(1))
        username = args.username.strip().lower()
        existing_username = repository.get_by_username(db, username)

        if wujud is not None and not args.force:
            print("Super admin sudah wujud. Guna --force untuk kemaskini.")
            return
        if existing_username is not None and not args.force:
            print(f"Nama pengguna '{username}' sudah wujud. Guna --force untuk ganti.")
            return

        if wujud is not None:
            if existing_username is not None and existing_username.id != wujud.id:
                print(
                    f"Nama pengguna '{username}' dipakai akaun lain. "
                    "Pilih nama pengguna lain."
                )
                sys.exit(1)
            wujud.username = username
            wujud.nama_first = args.nama_first.strip()
            wujud.nama_last = args.nama_last.strip()
            wujud.password_hash = hash_password(args.password)
            wujud.aktif = True
            wujud.mesti_tukar_kata_laluan = True
            db.commit()
            db.refresh(wujud)
            print(f"Super admin '{username}' dikemaskini (id={wujud.id}).")
            print("Akaun ini mesti menukar kata laluan selepas log masuk pertama.")
            return

        user = repository.create(
            db,
            username=username,
            nama_first=args.nama_first.strip(),
            nama_last=args.nama_last.strip(),
            password_hash=hash_password(args.password),
            role="super_admin",
            aktif=True,
            mesti_tukar_kata_laluan=True,
            kelas_id=None,
            created_by=None,
        )
        db.commit()
        db.refresh(user)
        print(f"Super admin '{username}' berjaya dicipta (id={user.id}).")
        print("Akaun ini mesti menukar kata laluan selepas log masuk pertama.")
    finally:
        db.close()


if __name__ == "__main__":
    main()