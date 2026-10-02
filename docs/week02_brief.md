<!-- This is the Week 2 brief. It lives in docs/ rather than at the top of the
     repository because README.md is yours: Week 1's homework asks you to write
     it, and a later zip must not overwrite your own work. -->

# SPC5002 Week 2 lab

Last week you were handed one file. This week you are handed the three it was
made from.

## Getting it into your repository

This week does not start a new repository. Copy everything inside this
`lab_week02` folder into the repository you built in Week 1 and let it replace
the Makefile and requirements.txt. Your README, your `src/run.py` and your Week 1
docs are not in this zip, so nothing of yours is overwritten.

In a terminal, in the folder that holds both `lab_week01` and `lab_week02`:

    cp -R lab_week02/. lab_week01/
    cd lab_week01
    source .venv/bin/activate          # Windows: .venv\Scripts\activate
    make setup
    make test
    jupyter lab

On Windows, drag everything from `lab_week02` into your repository in Explorer
and say yes to replacing, then run the rest in PowerShell.

`openpyxl` is new this week and `make setup` installs it. Before you write
anything, `make test` shows 9 passed and 6 errors. The 9 are your seven from
Week 1 and two of this week's that need no code. The last line opens JupyterLab
in your browser, and the rest of the week happens there.

## Working in JupyterLab

JupyterLab is where you work in this module. Three parts of it matter this week.

A terminal, from File, New, Terminal. Run `source .venv/bin/activate` in every
new terminal before anything else, even though you started JupyterLab from an
activated one. On a machine with Anaconda the terminal can otherwise pick up the
wrong Python, and `(.venv)` at the start of the prompt tells you it has not. Run
`make`, `python` and `git` here.

An editor, for `src/ingest.py`. Double-click `src` in the file browser to go into
it, then File, New, Python File. That makes `untitled.py` inside `src`. Rename it
with File, Rename Python File, and type only `ingest`, because the box keeps the
`.py` for you and typing `ingest.py` gives `ingest.py.py`. Save with Ctrl+S, or
Cmd+S on a Mac, and run it from the terminal.

A notebook, for looking at the sources before you write the readers. Make it in
the `notebooks` folder. A notebook runs from its own folder, so the paths start
`../data/sources/`.

If `make` is missing, which it usually is on Windows, run what the Makefile
would. `make ingest` is `python src/ingest.py` and `make test` is
`python -m pytest -q`.

## What is here

    data/sources/web_orders_2025.csv       1,900 rows. Storefront export.
    data/sources/phone_orders_2025.json      96 calls. Call-centre log.
    data/sources/crm_customers.xlsx       1,088 rows. Customer database extract.
    data/retail_orders_week1.csv          2,030 rows. What you were given in Week 1.
    tests/test_week2_contract.py          eight tests you did not write
    src/                                  you add ingest.py

## The task

Write `src/ingest.py`. It reads the three sources, reconciles them, joins them,
and writes **two** files. It takes no arguments and runs from a clean clone. It
finds its files from its own location, the way `src/run.py` does.

    from pathlib import Path
    import json
    import numpy as np
    import pandas as pd

    ROOT = Path(__file__).resolve().parents[1]
    SOURCES = ROOT / "data" / "sources"
    WEEK1 = ROOT / "data" / "retail_orders_week1.csv"
    OUT = ROOT / "outputs"

    outputs/ingest_report.json    the counts, and what happened at each step
    outputs/orders_joined.csv     the joined table itself, 1,996 rows

The second one is not optional and it is not for this week. **Weeks 3, 4 and 5
all start from `outputs/orders_joined.csv`, not from the file you were handed in
Week 1.** Week 4's contract test fails immediately without it, and so does
`selfcheck.py` in Week 7. Write it this week, while you still remember what is
in it.

**Task A.** One function per source. Each returns a frame with the same column
names and the same types as the others, and each ends by checking its row count.
Use the column names of the Week 1 file, because Task C compares against it. Do
not join anything yet.

**Task B.** Concatenate. Check. Then, before you write the join, put your
predicted row count in a comment. Then run the join with
`validate="many_to_one"` and see what happens.

**Task C.** Reproduce the join the way it was originally run, and compare the
result column by column against `data/retail_orders_week1.csv`. Fifteen of the
sixteen shared columns will match exactly. Find the one that does not.

## What the sources will do to you

Nothing here is unusual and none of it is a trick. All of it is in files people
are sent every week.

- The web CSV starts with a byte order mark. `pandas.read_csv` strips it for you,
  so this one will not bite in pandas. Open the same file with Python's `csv`
  module and the first column is called `'\ufeffOrder ID'`. The moment you hand
  this file to anything that is not pandas, it is your problem.
- Its dates are day first. `pd.to_datetime` without a format guesses from the
  first row and warns. `format="mixed"` reads 694 of the 1,900 as the wrong day
  and says nothing. Give the format.
- 112 of its categories end in a space. The phone log writes `Footwear ` with a
  trailing space in all 14 of its footwear orders.
- The phone log has its own words for categories and payment methods, and says
  `true` where the storefront says `Y`. Keep the storefront's words, because the
  Week 1 file uses them.
- The phone JSON stores money in **pence**, as integers.
- Twelve of the phone quantities are strings. Summing the column raises a
  `TypeError`, which is the kind outcome.
- The phone log records a UTC timestamp with a time of day. The storefront and
  the Week 1 file record a date. Keep the time and Task C finds fourteen matching
  columns instead of fifteen.
- The spreadsheet has two title rows above the header. `read_excel` does not
  complain. It gives you 1,090 rows and columns called `Unnamed`.
- Its region field is free text. Twenty-two distinct strings, seven places.

## Committing

At least six commits. `make test` tells you where you are, and `make verify`
runs your ingestion twice and fails if the two runs differ.

One test copies your repository, replaces the CRM with one where three more
customers have two rows, and runs your code again. It expects your code to stop.
If it does not stop, the test fails, and it is the only test here worth failing.
