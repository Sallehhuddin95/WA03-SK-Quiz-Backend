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