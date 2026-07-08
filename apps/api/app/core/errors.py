"""Bilingual error envelope + stable error codes (api-contracts.md).

Every error the API returns uses the shape:
    { "error": { "code": str, "message_ar": str, "message_en": str } }
Codes are stable and must match api-contracts.md. Adding a code requires updating the doc.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

# Stable codes -> default bilingual messages. Never mix scripts on one line.
ERROR_MESSAGES: dict[str, tuple[str, str]] = {
    "unauthorized": ("يلزم تسجيل الدخول", "Authentication required"),
    "forbidden": ("لا تملك صلاحية لهذا الإجراء", "You do not have permission for this action"),
    "not_found": ("العنصر غير موجود", "Resource not found"),
    "validation_failed": ("البيانات المدخلة غير صحيحة", "The submitted data is invalid"),
    # Should never occur — a finding without a source is structurally impossible.
    "citation_required": ("لا يمكن إنشاء ملاحظة بدون مصدر", "A finding cannot exist without a source"),
    "sanitize_failed": ("تعذر تنقية الملف", "The file could not be sanitized"),
    "sanitize_timeout": ("انتهت مهلة تنقية الملف", "File sanitization timed out"),
    "file_too_large": ("حجم الملف يتجاوز الحد المسموح", "The file exceeds the maximum allowed size"),
    "unsupported_file_type": ("نوع الملف غير مدعوم", "This file type is not supported"),
    "egress_denied": ("تم رفض الاتصال الخارجي", "Outbound connection denied"),
    "review_conflict": ("تمت مراجعة هذه الملاحظة مسبقًا", "This finding has already been reviewed"),
}

# Codes -> HTTP status.
STATUS_MAP: dict[str, int] = {
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "validation_failed": 422,
    "citation_required": 409,
    "sanitize_failed": 422,
    "sanitize_timeout": 422,
    "file_too_large": 413,
    "unsupported_file_type": 422,
    "egress_denied": 403,
    "review_conflict": 409,
}


class SanadError(Exception):
    """Raised anywhere in the API to produce the standard bilingual envelope."""

    def __init__(self, code: str, message_ar: str | None = None, message_en: str | None = None) -> None:
        default_ar, default_en = ERROR_MESSAGES.get(code, ("خطأ", "Error"))
        self.code = code
        self.message_ar = message_ar or default_ar
        self.message_en = message_en or default_en
        self.status_code = STATUS_MAP.get(code, 400)
        super().__init__(f"{code}: {self.message_en}")

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={
                "error": {
                    "code": self.code,
                    "message_ar": self.message_ar,
                    "message_en": self.message_en,
                }
            },
        )


async def sanad_error_handler(_: Request, exc: SanadError) -> JSONResponse:
    return exc.to_response()
