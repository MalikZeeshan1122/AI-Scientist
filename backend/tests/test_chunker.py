from ai_scientist.ingestion import chunk_text


def test_chunk_text_splits_by_section():
    text = (
        "Abstract\nThis paper introduces foo.\n\n"
        "Introduction\nFoo is great. " * 5 + "\n\n"
        "Methods\nWe compute bar. " * 5 + "\n\n"
        "Conclusion\nDone."
    )
    chunks = chunk_text("paper:1", text, chunk_size=20, overlap=5)
    sections = {c.section for c in chunks}
    assert sections >= {"abstract", "introduction", "methods", "conclusion"}
    assert all(c.paper_id == "paper:1" for c in chunks)
    indices = [c.chunk_index for c in chunks]
    assert indices == sorted(indices)
    assert len(set(indices)) == len(indices)


def test_chunk_text_empty():
    assert chunk_text("p", "") == []
