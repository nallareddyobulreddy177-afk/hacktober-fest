
import re
import io
import pymupdf
import pytesseract
from PIL import Image


# Tesseract OCR installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_pdf_pages(pdf_bytes):
    """
    Extract text from a PDF.
    If the extracted text is too short, use OCR.
    Works with normal PDFs, scanned PDFs, and ID cards.
    """
    pages = []

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        for page_number, page in enumerate(pdf, start=1):

            # Step 1: Extract normal PDF text
            text = page.get_text("text").strip()

            # Step 2: Use OCR if the text is too short
            if len(text) < 100:
                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(3, 3),
                    alpha=False
                )

                image = Image.open(
                    io.BytesIO(pix.tobytes("png"))
                )

                ocr_text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                ).strip()

                # Keep the result with more text
                if len(ocr_text) > len(text):
                    text = ocr_text

            # Step 3: Save extracted text
            if text:
                pages.append({
                    "page": page_number,
                    "text": text
                })

    return pages


def split_into_chunks(pages, chunk_size=900, overlap=150):
    """
    Split PDF text into smaller sections.
    Overlap helps preserve context between sections.
    """
    chunks = []

    for page in pages:
        text = page["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            chunks.append({
                "page": page["page"],
                "text": text[start:end]
            })

            if end >= len(text):
                break

            start = end - overlap

    return chunks


def search_chunks(question, chunks, top_k=4):
    """
    Find PDF text sections that match the user's question.
    """
    if not chunks:
        return []

    stop_words = {
        "what", "is", "are", "the", "a", "an", "of", "in",
        "to", "for", "and", "how", "why", "does", "do", "can",
        "i", "it", "on", "with", "this", "that", "about",
        "tell", "me", "please", "give", "show", "explain",
        "summarize", "summary", "main", "details", "document",
        "pdf", "important", "information", "find", "from"
    }

    # Extract keywords from the question
    question_words = set(
        re.findall(r"\b[a-z0-9]+\b", question.lower())
    )

    keywords = question_words - stop_words

    # If no keywords remain, return the first sections
    if not keywords:
        return chunks[:top_k]

    results = []
    normalized_question = " ".join(question.lower().split())

    for chunk in chunks:
        text = chunk["text"].lower()

        text_words = set(
            re.findall(r"\b[a-z0-9]+\b", text)
        )

        # Score the section by matching keywords
        score = len(keywords & text_words)

        # Give extra weight to an exact phrase match
        if normalized_question in text:
            score += 5

        if score > 0:
            results.append((score, chunk))

    # Highest-scoring sections first
    results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # Return matching sections
    if not results:
        return chunks[:top_k]

    return [
        chunk for score, chunk in results[:top_k]
    ]
