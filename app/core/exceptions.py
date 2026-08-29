from typing import Optional


class ApiError(Exception):
    status_code: int = 500
    kod: str = "RALAT_TIDAK_DIJANGKA"
    mesej: str = "Ralat tidak dijangka. Sila cuba lagi."
    butiran: Optional[dict[str, list[str]]] = None

    def __init__(
        self,
        mesej: Optional[str] = None,
        butiran: Optional[dict[str, list[str]]] = None,
    ) -> None:
        self.mesej = mesej or self.mesej
        self.butiran = butiran
        super().__init__(self.mesej)


class ResourceNotFoundError(ApiError):
    status_code = 404
    kod = "SUMBER_TIDAK_DIJUMPAI"
    mesej = "Sumber tidak dijumpai."


class ResourceConflictError(ApiError):
    status_code = 409
    kod = "KONFLIK_SUMBER"
    mesej = "Permintaan bercanggah dengan keadaan semasa."


class InvalidStateError(ApiError):
    status_code = 409
    kod = "KEADAAN_TIDAK_SAH"
    mesej = "Keadaan semasa tidak membenarkan tindakan ini."


class InvalidPaginationError(ApiError):
    status_code = 400
    kod = "PARAMETER_TIDAK_SAH"
    mesej = "Parameter halaman tidak sah."


class QuestionLimitReachedError(ResourceConflictError):
    kod = "HAD_SOALAN_DICAPAI"
    mesej = (
        "Had 10 soalan aktif untuk kombinasi Topik, Tahap, dan Jenis ini telah dicapai."
    )


class FillBlankMarkerMissingError(ApiError):
    status_code = 400
    kod = "PENANDA_TEMPAT_KOSONG_TIADA"
    mesej = "Teks soalan mesti mengandungi penanda tempat kosong '______'."


class InsufficientQuestionsError(ApiError):
    status_code = 400
    kod = "SOALAN_TIDAK_MENCUKUPI"
    mesej = "Tidak cukup soalan untuk Topik dan Tahap ini."


class QuizAlreadySubmittedError(InvalidStateError):
    kod = "KUIZ_TELAH_SELESAI"
    mesej = "Kuiz ini telah dihantar."


class QuizNotSubmittedError(InvalidStateError):
    kod = "KUIZ_BELUM_SELESAI"
    mesej = "Kuiz belum dihantar."


class InvalidQuestionError(ApiError):
    status_code = 400
    kod = "SOALAN_TIDAK_SAH"
    mesej = "Soalan tidak tergolong dalam kuiz ini."


class ValidationError(ApiError):
    status_code = 400
    kod = "DATA_TIDAK_SAH"
    mesej = "Data yang dihantar tidak sah."


class InvalidCredentialsError(ApiError):
    status_code = 401
    kod = "KELAYAKAN_TIDAK_SAH"
    mesej = "Nama pengguna atau kata laluan tidak sah."


class SessionExpiredError(ApiError):
    status_code = 401
    kod = "SESI_TAMAT"
    mesej = "Sesi anda telah tamat. Sila log masuk semula."


class NoPermissionError(ApiError):
    status_code = 403
    kod = "TIADA_KEBENARAN"
    mesej = "Anda tidak mempunyai kebenaran untuk tindakan ini."


class AccountDisabledError(ApiError):
    status_code = 403
    kod = "AKAUN_TIDAK_AKTIF"
    mesej = "Akaun anda tidak aktif."


class MustChangePasswordError(ApiError):
    status_code = 403
    kod = "KATA_LALUAN_PERLU_DITUKAR"
    mesej = "Anda mesti menukar kata laluan dahulu."


class UsernameTakenError(ApiError):
    status_code = 409
    kod = "NAMA_PENGGUNA_WUJUD"
    mesej = "Nama pengguna telah wujud."


class InvalidTargetRoleError(NoPermissionError):
    mesej = "Peranan sasaran tidak sah untuk pengguna ini."