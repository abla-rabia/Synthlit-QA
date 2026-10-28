from unstructured.chunking.title import chunk_by_title


def chunk_elements(elements):
    chunks=chunk_by_title(
        elements=elements, 
        max_characters=3000,
        combine_text_under_n_chars=500, 
        new_after_n_chars=2400
    )
    return chunks
