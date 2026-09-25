"""
tests/test_week1_contract.py

You did not write these tests and you may not change them. They check that your
src/run.py behaves, not that it is right. None of them asserts a ROC-AUC.

Run them with

    python -m pytest -q

Six of the seven should pass by the end of the seminar. The seventh is the one
that catches the fault the notebook was hiding, and it is meant to fail until
you have dealt with it.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "src" / "run.py"
METRICS = ROOT / "outputs" / "metrics.json"
DATA = ROOT / "data" / "retail_orders_week1.csv"


def _run():
    return subprocess.run(
        [sys.executable, str(RUN)], cwd=ROOT, capture_output=True, text=True
    )


@pytest.fixture(scope="module")
def first_run():
    if not RUN.exists():
        pytest.fail("src/run.py does not exist yet")
    result = _run()
    if result.returncode != 0:
        pytest.fail(f"src/run.py exited {result.returncode}\n{result.stderr[-2000:]}")
    return result


def test_run_exists_and_takes_no_arguments(first_run):
    """Somebody else has to be able to run this without asking you how."""
    assert first_run.returncode == 0


def test_writes_metrics_json(first_run):
    assert METRICS.exists(), "src/run.py must write outputs/metrics.json"
    json.loads(METRICS.read_text())


def test_metrics_has_the_required_fields(first_run):
    """
    Real keys with believable values, not words that happen to appear in the file.

    An earlier version of this searched the whole document as one string, so a
    metrics.json containing nothing but an empty feature list and the sentence
    "seed base_rate roc_auc n_rows" passed every test in this file without
    fitting anything.
    """
    m = json.loads(METRICS.read_text())

    def find(key):
        """The value of `key` wherever you nested it, or None."""
        stack = [m]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if key in node:
                    return node[key]
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
        return None

    n_rows = find("n_rows")
    assert isinstance(n_rows, int) and n_rows > 0, \
        "outputs/metrics.json needs n_rows, as a whole number of rows you used"

    base_rate = find("base_rate")
    assert isinstance(base_rate, (int, float)) and 0 < base_rate < 1, \
        "outputs/metrics.json needs base_rate, a proportion between 0 and 1"

    seed = find("seed")
    assert isinstance(seed, int), "outputs/metrics.json needs seed, as a number"

    features = find("features")
    assert isinstance(features, list) and features and all(
        isinstance(f, str) for f in features), \
        "outputs/metrics.json needs features: a non-empty list of column names"

    aucs = [v for k, v in _walk(m) if "roc_auc" in k]
    assert aucs, "outputs/metrics.json records no roc_auc"
    for v in aucs:
        assert isinstance(v, (int, float)) and 0 <= v <= 1, \
            f"a roc_auc of {v!r} is not a score between 0 and 1"


def _walk(node, prefix=""):
    """Every (key, scalar value) pair in a nested structure."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                yield from _walk(v, k)
            else:
                yield k, v
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v, prefix)


def test_two_runs_produce_identical_output(first_run):
    """The whole of Week 1 in one assertion."""
    a = hashlib.sha256(METRICS.read_bytes()).hexdigest()
    second = _run()
    assert second.returncode == 0
    b = hashlib.sha256(METRICS.read_bytes()).hexdigest()
    assert a == b, (
        "two runs of src/run.py gave different files. Something in your code is "
        "not seeded, or depends on the order a set or dictionary happened to be in, "
        "or on the state of a file you wrote earlier."
    )


def test_no_absolute_paths_in_source():
    """A path that starts at the root of your machine cannot start on anyone else's."""
    offenders = []
    # A drive letter counts however it is spelled. The earlier pattern required a
    # DOUBLED backslash, so it missed r"C:\Users\..." - a raw string, which is
    # exactly what a Windows user writes - and C:/Users/..., which Python also
    # accepts on Windows.
    pattern = re.compile(r"""["'](?:/Users/|/home/|/mnt/|[A-Za-z]:[\\/])""")
    for path in (ROOT / "src").rglob("*.py"):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path.name}:{i}  {line.strip()}")
    assert not offenders, "absolute paths found:\n" + "\n".join(offenders)


def test_data_file_is_the_one_we_shipped():
    """If the data changed, every number above is about a different dataset."""
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()[:16]
    assert digest == "dd0caefae80c6529", (
        f"data/retail_orders_week1.csv has hash {digest}, not the one shipped. "
        "Restore the original file."
    )


def test_no_leaked_column_in_the_feature_list(first_run):
    """
    This one fails until you have dealt with what you found in the scan.

    A column belongs in the feature list only if you could have obtained it, with
    that value, at the moment you needed the prediction. Nothing in the file says
    which columns those are. You have to decide, and you have to be able to say why.
    """
    m = json.loads(METRICS.read_text())

    # Find "features" wherever you put it, rather than only one level down. An
    # earlier version of this test looked in exactly two places, so nesting the
    # key anywhere else made it pass with the leaked column still in the model.
    def find_features(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "features":
                    yield value
                else:
                    yield from find_features(value)
        elif isinstance(node, list):
            for item in node:
                yield from find_features(item)

    lists = [f for f in find_features(m)]
    assert lists, (
        "outputs/metrics.json has no 'features' key anywhere in it. The feature "
        "list is the record of what you decided to model on, so it has to be in "
        "the file."
    )

    banned = {"export_seq", "returned"}
    found = sorted({c for lst in lists for c in lst if c in banned})
    assert not found, (
        f"{found} is in your feature list. Before you remove it, write down in "
        "docs/leakage_note.md why it was there and what it was doing to the score."
    )
