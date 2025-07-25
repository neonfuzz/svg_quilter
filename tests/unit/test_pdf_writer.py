import pytest
from pdf_writer import text_center_offset


def test_text_center_offset_returns_float():
    offset = text_center_offset("Helvetica-Bold", 24)
    assert isinstance(offset, float)
    assert offset > 0
