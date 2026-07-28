import pdfplumber


class PDFEmptyError(ValueError):
    """Raised when a PDF contains no extractable text."""


def pdf_reader(file_path):
    """
    Extracts and returns clean text from a PDF file.
    Raises PDFEmptyError if no text could be extracted.
    """
    print(f"[PDF Reader] Opening PDF: {file_path}")

    full_text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            if not pdf.pages:
                raise PDFEmptyError("The PDF has no pages.")

            for i, page in enumerate(pdf.pages):
                print(f"[PDF Reader] Extracting page {i + 1}...")
                text = page.extract_text() or ""
                full_text += text + "\n"

    except PDFEmptyError:
        raise
    except Exception as e:
        print(f"[PDF Reader] Error reading PDF: {e}")
        raise ValueError(f"Could not read PDF: {e}") from e

    full_text = full_text.strip()
    if not full_text:
        raise PDFEmptyError(
            "No text could be extracted from this PDF. "
            "It may be image-only — try a PDF with selectable text."
        )

    print("[PDF Reader] Extraction complete.")
    return full_text


def validate_pdf_text(file_path: str, min_chars: int = 50) -> tuple[bool, str]:
    """Quick validation without raising. Returns (ok, message)."""
    try:
        text = pdf_reader(file_path)
        if len(text) < min_chars:
            return False, f"PDF text is too short ({len(text)} chars). The deck may be mostly images."
        return True, ""
    except PDFEmptyError as e:
        return False, str(e)
    except ValueError as e:
        return False, str(e)
