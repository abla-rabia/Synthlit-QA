import time
from pathlib import Path
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json, elements_from_json


def partition_document(pdf_path, cache_dir="data/extracted_raw", force=False):
    """PDF -> éléments unstructured (hi_res). Résultat mis en cache en JSON."""
    pdf_path = Path(pdf_path)
    cache = Path(cache_dir) / f"{pdf_path.stem}.json"

    if cache.exists() and not force:
        return elements_from_json(filename=str(cache))

    start = time.time()
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="hi_res",
        infer_table_structure=True,
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    elements_to_json(elements, filename=str(cache))
    print(f"{pdf_path.name}: {len(elements)} éléments en {time.time() - start:.0f} s")
    return elements