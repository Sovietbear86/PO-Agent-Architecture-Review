"""Regression checks for read-only SberProject pagination (no network/auth)."""
import importlib.util
from pathlib import Path

import pytest
from fastapi import HTTPException

SOURCE = Path(__file__).resolve().parents[1] / "app" / "routers" / "sberproject_read.py"
SPEC = importlib.util.spec_from_file_location("_sberproject_read_pagination_under_test", SOURCE)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def payload(offset=0, count=20, total=69, next_offset=None):
    rows = [{"id": f"OLP.{i}", "versionNumber": str(i)} for i in range(offset, offset + count)]
    has_more = offset + count < total
    if next_offset is None and has_more:
        next_offset = offset + count
    return {"results": rows, "meta": {
        "offset": offset, "has_more": has_more, "next_offset": next_offset, "total": total
    }}


@pytest.mark.parametrize("offset,count,next_offset", [(0, 20, 20), (20, 20, 40), (40, 20, 60), (60, 9, None)])
def test_real_page_sequence(offset, count, next_offset):
    result = module._catalog_response(payload(offset, count), "OLP", 20, offset)
    assert result["offset"] == offset
    assert result["next_offset"] == next_offset
    assert len(result["versions"]) == count
    assert result["total"] == 69
    assert result["status"] == ("COMPLETE" if next_offset is None else "PARTIAL")


def test_page_one_replay_rejected():
    with pytest.raises(HTTPException) as exc:
        module._catalog_response(payload(0), "OLP", 20, 20)
    assert exc.value.detail["reason"] == "sberproject_page_identity_unverified"


@pytest.mark.parametrize("bad_cursor", [0, 10, 100, True, "20"])
def test_invalid_cursor_rejected(bad_cursor):
    item = payload()
    item["meta"]["next_offset"] = bad_cursor
    with pytest.raises(HTTPException) as exc:
        module._catalog_response(item, "OLP", 20, 0)
    assert exc.value.detail["reason"] == "sberproject_pagination_unknown"


def test_omitted_page_identity_rejected():
    item = payload()
    del item["meta"]["offset"]
    with pytest.raises(HTTPException) as exc:
        module._catalog_response(item, "OLP", 20, 0)
    assert exc.value.detail["reason"] == "sberproject_page_identity_unverified"


def test_no_fake_membership():
    result = module._catalog_response(payload(60, 9), "OLP", 20, 60)
    assert all("task_count" not in row for row in result["versions"])
    assert result["membership_status"] == "SOURCE_UNVERIFIED"
