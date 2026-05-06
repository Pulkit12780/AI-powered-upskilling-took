import pytest
from app.pdf_loader import safe_extract


def test_empty_bytes_returns_error():
    _, err = safe_extract(b"")
    assert err is not None


def test_garbage_bytes_returns_error():
    _, err = safe_extract(b"not a pdf")
    assert err is not None


# Place a real PDF at tests/fixtures/sample.pdf to run this test
# def test_real_pdf_extracts_text():
#     with open("tests/fixtures/sample.pdf", "rb") as f:
#         text, err = safe_extract(f.read())
#     assert err is None
#     assert len(text) > 50
