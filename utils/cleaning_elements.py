
import re


def normalize_text(text):
    """Normalize text for duplicate detection."""
    text = re.sub(r"\s+", " ", text or "").strip()
    return text.casefold()


def clean(elements):
    """
    Clean unstructured elements:
    1. Remove the bibliography and everything after it.
    2. Remove duplicate text elements on the same page.

    Keeps the original element objects and their metadata.
    """

    # 1. Detect the beginning of the bibliography
    reference_heading = re.compile(
        r"^(references|bibliography|reference list)\s*[:.]?$",
        re.IGNORECASE,
    )

    cutoff = len(elements)

    for i, el in enumerate(elements):
        text = (getattr(el, "text", "") or "").strip()
        category = type(el).__name__

        if (
            category in {"Title", "SectionHeader", "Header"}
            and reference_heading.fullmatch(text)
        ):
            cutoff = i
            break

    elements = elements[:cutoff]

    # 2. Remove duplicates on the same page
    seen = set()
    unique_elements = []

    for el in elements:
        text = normalize_text(getattr(el, "text", ""))

        metadata = getattr(el, "metadata", None)
        page = getattr(metadata, "page_number", None)

        if not text:
            unique_elements.append(el)
            continue

        key = (page, text)

        if key in seen:
            continue

        seen.add(key)
        unique_elements.append(el)

    return unique_elements
