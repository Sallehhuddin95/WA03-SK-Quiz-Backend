from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import KELAS_SCOPE_ALL, resolve_kelas_scope
from app.core.exceptions import (
    NoPermissionError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.kelas import Kelas
from app.models.user import User
from app.repositories.kelas import KelasRepository
from app.schemas.kelas import (
    CreateKelasRequest,
    GuruBrief,
    KelasResponse,
    UpdateKelasRequest,
)
from app.schemas.user import GuruDirectoryResponse


class KelasService:
    def __init__(self, kelas_repository: KelasRepository) -> None:
        self._repository = kelas_repository

    def list(self, db: Session, requester: User) -> list[KelasResponse]:
        scope = resolve_kelas_scope(db, requester)
        if scope is KELAS_SCOPE_ALL:
            kelas_list = self._repository.list_kelas(db)
        else:
            kelas_list = self._repository.list_kelas(db, kelas_ids=set(scope.visible))
        return self._build_responses(db, kelas_list)

    def create(
        self, db: Session, requester: User, payload: CreateKelasRequest
    ) -> KelasResponse:
        self._semak_duplikat(db, payload.nama.strip(), payload.darjah, exclude_id=None)
        kelas = self._repository.create(
            db, nama=payload.nama.strip(), darjah=payload.darjah
        )
        db.commit()
        db.refresh(kelas)
        return self._build_responses(db, [kelas])[0]

    def update(
        self,
        db: Session,
        requester: User,
        kelas_id: int,
        payload: UpdateKelasRequest,
    ) -> KelasResponse:
        kelas = self._get_kelas_atau_404(db, kelas_id)
        nama = payload.nama.strip() if payload.nama is not None else kelas.nama
        darjah = payload.darjah if payload.darjah is not None else kelas.darjah
        self._semak_duplikat(db, nama, darjah, exclude_id=kelas_id)
        updated = self._repository.update(db, kelas, nama=nama, darjah=darjah)
        db.commit()
        db.refresh(updated)
        return self._build_responses(db, [updated])[0]

    def share(
        self, db: Session, requester: User, kelas_id: int, guru_ids: list[int]
    ) -> KelasResponse:
        kelas = self._get_kelas_atau_404(db, kelas_id)
        scope = resolve_kelas_scope(db, requester)
        if requester.role != "super_admin":
            own = scope.own if scope is not KELAS_SCOPE_ALL else frozenset()
            if kelas_id not in own:
                raise NoPermissionError()

        unik_ids = list(dict.fromkeys(guru_ids))
        sasaran = self._repository.get_users_by_ids(db, unik_ids)
        sasaran_by_id = {user.id: user for user in sasaran}
        for guru_id in unik_ids:
            user = sasaran_by_id.get(guru_id)
            if user is None or user.role != "admin" or not user.aktif:
                raise ValidationError(
                    "Setiap guru_id mesti merujuk akaun admin yang aktif."
                )

        pemilik = self._repository.get_owner_ids(db, kelas_id)
        bertindih = set(unik_ids) & pemilik
        if bertindih:
            raise ResourceConflictError(
                "Guru yang sudah memiliki kelas tidak boleh menjadi penerima kongsi."
            )

        self._repository.share_kelas(db, kelas_id, unik_ids)
        db.commit()
        return self._build_responses(db, [kelas])[0]

    def list_gurus(
        self, db: Session, requester: User
    ) -> list[GuruDirectoryResponse]:
        gurus = self._repository.list_gurus_for_directory(db)
        return [
            GuruDirectoryResponse(
                id=guru.id,
                nama_first=guru.nama_first,
                nama_last=guru.nama_last,
            )
            for guru in gurus
        ]

    def _get_kelas_atau_404(self, db: Session, kelas_id: int) -> Kelas:
        kelas = self._repository.get_by_id(db, kelas_id)
        if kelas is None:
            raise ResourceNotFoundError("Kelas tidak dijumpai.")
        return kelas

    def _semak_duplikat(
        self, db: Session, nama: str, darjah: int, *, exclude_id: int | None
    ) -> None:
        stmt = select(Kelas).where(Kelas.nama == nama, Kelas.darjah == darjah)
        if exclude_id is not None:
            stmt = stmt.where(Kelas.id != exclude_id)
        if db.scalar(stmt) is not None:
            raise ResourceConflictError(
                "Kelas dengan darjah dan nama yang sama sudah wujud."
            )

    def _build_responses(
        self, db: Session, kelas_list: list[Kelas]
    ) -> list[KelasResponse]:
        if not kelas_list:
            return []
        kelas_ids = [kelas.id for kelas in kelas_list]
        owners_map = self._repository.list_owners_for_kelas(db, kelas_ids)
        shares_map = self._repository.list_shares_for_kelas(db, kelas_ids)
        responses = []
        for kelas in kelas_list:
            owners = [
                GuruBrief(id=u.id, nama_first=u.nama_first, nama_last=u.nama_last)
                for u in owners_map.get(kelas.id, [])
            ]
            shared = [
                GuruBrief(id=u.id, nama_first=u.nama_first, nama_last=u.nama_last)
                for u in shares_map.get(kelas.id, [])
            ]
            responses.append(
                KelasResponse(
                    id=kelas.id,
                    nama=kelas.nama,
                    darjah=kelas.darjah,
                    guru_owners=owners,
                    shared_with=shared,
                    created_at=kelas.created_at,
                )
            )
        return responses