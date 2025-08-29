import fitz

pdf_path = "example.pdf"
doc = fitz.open(pdf_path)

all_text = []

for page_number in range(len(doc)):
    page = doc[page_number]
    page_dict = page.get_text("dict")  # structured format

    page_paragraphs = []

    for block in page_dict["blocks"]:
        if block["type"] != 0:  # skip non-text blocks
            continue

        block_lines = []
        for line in block["lines"]:
            line_text = " ".join([span["text"] for span in line["spans"]]).strip()
            if line_text:
                block_lines.append(line_text)

        if block_lines:
            paragraph = " ".join(block_lines)  # merge lines in a block
            page_paragraphs.append(paragraph)

    # join paragraphs with double line breaks
    page_text = "\n\n".join(page_paragraphs)
    all_text.append(page_text)

# Combine all pages into one string
final_text = "\n\n".join(all_text)
print(final_text)
