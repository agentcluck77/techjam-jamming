import re
from typing import List

def chunk_by_chapter(text: str) -> List[str]:
    """
    Splits text into chunks whenever a chapter heading appears.
    Chapter headings are expected in the format: "\n\nArticle[number]\n\n".

    :param text: Full text to split
    :return: List of chapter chunks
    """
    if not text:
        return []

    # Pattern to match \n\nArticle[number]\n\n (case insensitive)
    pattern = r'(?<=\n\n)(Article\s*\d+)(?=\n\n)'
    
    # Split while keeping the chapter headers in the chunks
    splits = re.split(pattern, text, flags=re.IGNORECASE)
    
    
    chunks = []
    i = 0
    while i < len(splits):
        if splits[i].strip().lower().startswith('chapter'):
            # Prepend chapter header to the following text
            if i + 1 < len(splits):
                chunks.append(splits[i] + "\n\n" + splits[i+1])
                i += 2
            else:
                chunks.append(splits[i])
                i += 1
        else:
            # If first chunk doesn't start with chapter
            chunks.append(splits[i])
            i += 1

    return chunks


def conditional_chunk(text: str, min_words: int = 500) -> List[str]:
    """
    Only chunk the text if it exceeds `min_words`.
    Otherwise, return the text as a single-element list.
    """
    word_count = len(text.split())
    if word_count > min_words:
        return chunk_by_chapter(text)
    return [text]
