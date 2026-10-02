"""
tests/test_week2_contract.py

You did not write these and you may not change them. They check that your
src/ingest.py behaves. None of them asserts that a number is correct.

    python -m pytest -q

The last one is the interesting one. It copies your repository, replaces the CRM
with a worse version, and runs your code again. If your code reports a row count
without checking it, that test passes silently and you have learned nothing. If
your code asserts, it raises, and the test passes for the right reason.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INGEST = ROOT / "src" / "ingest.py"
REPORT = ROOT / "outputs" / "ingest_report.json"
JOINED = ROOT / "outputs" / "orders_joined.csv"
SOURCES = ROOT / "data" / "sources"
VARIANT = Path(__file__).parent / "fixtures" / "crm_customers_variant.xlsx"

SOURCE_HASHES = {
    "web_orders_2025.csv": "88d0a8de17aea467",
    "phone_orders_2025.json": "518a62fae3e3dd03",
    "crm_customers.xlsx": "6ec0da88baa4faaa",
}


def _run(cwd: Path = ROOT):
    return subprocess.run(
        [sys.executable, "src/ingest.py"], cwd=cwd, capture_output=True, text=True
    )


@pytest.fixture(scope="module")
def first_run():
    if not INGEST.exists():
        pytest.fail("src/ingest.py does not exist yet")
    r = _run()
    if r.returncode != 0:
        pytest.fail(f"src/ingest.py exited {r.returncode}\n{r.stderr[-2000:]}")
    return r


def test_ingest_runs_with_no_arguments(first_run):
    assert first_run.returncode == 0


def test_writes_the_report(first_run):
    assert REPORT.exists(), "src/ingest.py must write outputs/ingest_report.json"
    json.loads(REPORT.read_text())


def test_writes_the_joined_table(first_run):
    """
    Weeks 3, 4 and 5 all start from this file, not from the CSV you were handed
    in Week 1. Week 4's contract test fails without it and so does selfcheck.py.
    Producing it is part of this week, not next.
    """
    assert JOINED.exists(), (
        "src/ingest.py must also write outputs/orders_joined.csv, the joined "
        "table itself. Weeks 3, 4 and 5 read it."
    )
    import csv
    with JOINED.open(newline="") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) - 1 == 1996, (
        f"outputs/orders_joined.csv has {len(rows) - 1} data rows, not 1,996. "
        "The correct join produces one row per order."
    )


def test_report_states_every_row_count(first_run):
    """If a number is not in the report, you cannot be asked to defend it."""
    flat = json.dumps(json.loads(REPORT.read_text()))
    for field in ["web", "phone", "crm", "join"]:
        assert field in flat, f"outputs/ingest_report.json says nothing about {field}"


def test_two_runs_produce_identical_output(first_run):
    a = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    assert _run().returncode == 0
    b = hashlib.sha256(REPORT.read_bytes()).hexdigest()
    assert a == b, "two runs of src/ingest.py gave different files"


def test_no_absolute_paths_in_source():
    pattern = re.compile(r"""["'](?:/Users/|/home/|/mnt/|[A-Za-z]:[\\/])""")
    bad = [f"{p.name}:{i}  {line.strip()}"
           for p in (ROOT / "src").rglob("*.py")
           for i, line in enumerate(p.read_text().splitlines(), 1)
           if pattern.search(line)]
    assert not bad, "absolute paths found:\n" + "\n".join(bad)


def test_sources_are_the_ones_we_shipped():
    for name, want in SOURCE_HASHES.items():
        got = hashlib.sha256((SOURCES / name).read_bytes()).hexdigest()[:16]
        assert got == want, f"{name} has been modified. Restore the original."


def test_your_check_fires_when_the_crm_gets_worse(first_run):
    """
    The one that matters.

    A copy of your repository, with a CRM three rows longer than the one you were
    given. Three more customers have a second row, and none of the three placed
    an order in 2025, so every row count downstream is identical and every column
    still reconciles. Nothing breaks.

    That is the point. The only way to notice is to have said, in advance, how
    many rows the CRM should have. If your code passes this test it is because
    you checked. If it fails, you reported a number you did not verify.
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
            "outputs", ".venv", "__pycache__", ".pytest_cache", ".git"))
        shutil.copy(VARIANT, work / "data" / "sources" / "crm_customers.xlsx")

        result = _run(work)

        assert result.returncode != 0, (
            "your ingestion accepted a CRM three rows longer than the one you "
            "were given and ran to the end. The join, the reconstruction and "
            "every column comparison came out the same, so nothing downstream "
            "told you. Say how many rows each source should have, then check."
        )
