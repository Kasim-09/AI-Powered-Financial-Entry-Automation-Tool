from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union
from io import BytesIO

from .utils import get_logger

logger = get_logger()

# We support either `pypdf` (preferred) or `PyPDF2` for compatibility.
try:
    from pypdf import PdfReader, PdfWriter  # type: ignore
except Exception:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore
    except Exception as e:  # pragma: no cover
        PdfReader = None  # type: ignore
        PdfWriter = None  # type: ignore
        _IMPORT_ERROR = e
    else:
        _IMPORT_ERROR = None
else:
    _IMPORT_ERROR = None


class PdfEncryptionError(RuntimeError):
    """Raised when a PDF is encrypted and cannot be decrypted with the provided password."""


@dataclass
class DecryptionResult:
    is_encrypted: bool
    was_decrypted: bool
    output_path: Optional[str]
    message: str


def _ensure_crypto_available() -> None:
    if PdfReader is None or PdfWriter is None:
        raise ImportError(
            "Neither 'pypdf' nor 'PyPDF2' could be imported. Install one of them to enable encrypted PDF handling."
        ) from _IMPORT_ERROR


def detect_encrypted_pdf(pdf_path: Union[str, Path]) -> bool:
    """Return True if the PDF is encrypted (password-protected)."""
    _ensure_crypto_available()
    reader = PdfReader(str(pdf_path))
    return bool(getattr(reader, "is_encrypted", False))



def detect_encrypted_pdf_bytes(pdf_bytes: bytes) -> bool:
    """Return True if the PDF bytes represent an encrypted (password-protected) PDF."""
    _ensure_crypto_available()
    reader = PdfReader(BytesIO(pdf_bytes))
    return bool(getattr(reader, "is_encrypted", False))

def remove_pdf_password(
    input_pdf_path: Union[str, Path],
    password: Optional[str] = None,
    output_pdf_path: Optional[Union[str, Path]] = None,
) -> DecryptionResult:
    """
    If `input_pdf_path` is encrypted, try to decrypt it (using password if needed) and write an unencrypted copy.

    - Tries blank password first (some PDFs are "encrypted" but open without a user password).
    - Then tries the provided password.

    Returns a DecryptionResult describing what happened.
    """
    _ensure_crypto_available()
    input_pdf_path = Path(input_pdf_path)

    reader = PdfReader(str(input_pdf_path))
    is_encrypted = bool(getattr(reader, "is_encrypted", False))
    if not is_encrypted:
        return DecryptionResult(
            is_encrypted=False,
            was_decrypted=False,
            output_path=str(input_pdf_path),
            message="PDF is not encrypted.",
        )

    # Attempt decryption.
    decrypt_ok = False
    tried = []

    # 1) Blank password attempt.
    try:
        tried.append("(blank)")
        res = reader.decrypt("")  # type: ignore[attr-defined]
        decrypt_ok = bool(res) or (res is None)  # different libs return int/bool/None
    except Exception:
        decrypt_ok = False

    # 2) User supplied password attempt.
    if not decrypt_ok and password is not None:
        try:
            tried.append("(user)")
            res = reader.decrypt(password)  # type: ignore[attr-defined]
            decrypt_ok = bool(res) or (res is None)
        except Exception:
            decrypt_ok = False

    if not decrypt_ok:
        msg = "Encrypted PDF detected, but decryption failed."
        if password:
            msg += " The provided password did not work."
        else:
            msg += " A password is required."
        msg += f" Attempts: {', '.join(tried)}."
        raise PdfEncryptionError(msg)

    # Write unencrypted copy.
    if output_pdf_path is None:
        output_pdf_path = input_pdf_path.with_suffix(".decrypted.pdf")
    output_pdf_path = Path(output_pdf_path)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Ensure output is unencrypted: do NOT call writer.encrypt(...)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    logger.info("Decrypted PDF written to %s", output_pdf_path)

    return DecryptionResult(
        is_encrypted=True,
        was_decrypted=True,
        output_path=str(output_pdf_path),
        message="Password removed successfully.",
    )


def ensure_unencrypted_pdf(
    input_pdf_path: Union[str, Path],
    password: Optional[str] = None,
    output_pdf_path: Optional[Union[str, Path]] = None,
) -> DecryptionResult:
    """Convenience wrapper: returns a path safe for downstream processors."""
    return remove_pdf_password(input_pdf_path=input_pdf_path, password=password, output_pdf_path=output_pdf_path)
