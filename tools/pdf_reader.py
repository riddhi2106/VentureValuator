import pdfplumber

def pdf_reader(file_path):
    """
    PDF Reader Tool
    ----------------
    Extracts and returns clean text from a PDF file.

    Parameters
    ----------
    file_path: str
        Path to the PDF file.

    Returns
    -------
    str
        Extracted text from all pages of the PDF.
    """

    print(f"[PDF Reader] Opening PDF: {file_path}")

    full_text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"[PDF Reader] Extracting page {i+1}...")
                text = page.extract_text() or ""
                full_text += text + "\n"

    except Exception as e:
        print(f"[PDF Reader] Error reading PDF: {e}")
        return ""

    print("[PDF Reader] Extraction complete.")
    return full_text.strip()
