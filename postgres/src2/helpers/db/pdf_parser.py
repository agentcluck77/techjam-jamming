import fitz
from pathlib import Path
from typing import Union

def parse_pdf(pdf_path: Union[str, Path]) -> str:
    """
    Extracts text from a PDF file and returns it as a single string with paragraphs.

    Args:
        pdf_path (str | Path): Path to the PDF file.

    Returns:
        str: Extracted text with paragraphs separated by double line breaks.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Invalid PDF path: {pdf_path}")

    doc = fitz.open(pdf_path)
    all_text = []

    for page in doc:
        page_dict = page.get_text("dict")
        page_paragraphs = []

        for block in page_dict["blocks"]:
            if block["type"] != 0:  # skip non-text blocks
                continue

            block_lines = [
                " ".join([span["text"] for span in line["spans"]]).strip()
                for line in block["lines"]
                if "spans" in line and line["spans"]
            ]

            if block_lines:
                paragraph = " ".join(block_lines)
                page_paragraphs.append(paragraph)

        page_text = "\n\n".join(page_paragraphs)
        all_text.append(page_text)

    return "\n\n".join(all_text)


if __name__ == "__main__":
    text = parse_pdf("example.pdf")
    print(text)
