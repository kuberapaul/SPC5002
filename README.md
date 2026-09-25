# SPC5002 Week 1 lab



AI in the Real World. The repository you build this week is the one you add to
every week until May, and it is half the marks for this module.

## What is here

    data/retail_orders_week1.csv      2,030 rows, 17 columns. The raw export.
    notebooks/week1_broken.ipynb      a handover from a placement student
    tests/test_week1_contract.py      seven tests you did not write
    src/                              empty. You fill it.
    Makefile, requirements.txt        the entry points and the pinned versions

## Setup

You need Python 3.11 or newer. Check with `python --version` before anything
else. The pinned versions of pandas, numpy and scikit-learn do not exist for
3.10, and `make setup` will fail. pip does tell you why, in a long line above
the error listing every version it skipped for requiring a different Python,
but it is easy to read straight past.

    python -m venv .venv
    source .venv/bin/activate          # Windows: .venv\Scripts\activate
    make setup

If `make` is not available on your machine, read the Makefile and run the
commands in it directly. It is four lines.

## The dataset

A year of orders from an online retailer, one row per order, with a flag for
whether the customer sent it back. It arrived as a single CSV from someone in
the operations team. Nobody has told you how it was produced, which turns out to
matter.

| | |
|---|---|
| rows | 2,030 |
| columns | 17 |
| target | `returned`, 391 positive, base rate 0.193 |
| sha256 | `dd0caefae80c6529` |

Do not edit the file. If you change it, every number you report is about a
different dataset, and `test_data_file_is_the_one_we_shipped` will say so.

## What you are doing

**Task A.** Open the notebook. Restart the kernel and run all cells. It will not
get through. Work out why, fix each fault, and write down what each one was.

There are five **reproducibility** faults. (They are not an inventory of every
statistical problem in the file — Task C is about one of those, and later weeks
are about others.) **Two of them crash. Three do not.** The two that crash tell you
where they are; the three that do not are the ones worth your morning, because
each of them produces an answer that looks fine and is wrong, or an answer that
is different every time you run it. You will know you have found all five when
two consecutive runs of the notebook give identical numbers and you can say what
each of the five was doing.

Two runs agreeing is necessary and it is not sufficient. One of the five never
shows up that way: restarting the kernel clears it, so it only appears if you
re-run *that one cell* twice without restarting, and watch the number change.

**Task B.** Move the working logic out of the notebook and into `src/run.py`. It
has to run from a clean clone with no arguments, take its paths relative to the
repository, write `outputs/metrics.json`, and give the same file twice.

    make run
    make verify

`make verify` prints two hashes. Yours will almost certainly not be the ones in
the chapter or on the slides, because `metrics.json` records the Python version
that produced it, down to the patch release. What matters is that your two lines
agree with each other.

**Task C.** Fit one model per column and sort by ROC-AUC. One column is a long way
clear of the rest. Find out what it is, decide whether it belongs in a model, and
write `docs/leakage_note.md` saying why.

When you take that column out, the notebook's remaining list, five numeric
columns, lands at about 0.53. The 0.62 quoted in the chapter uses a different
six: `item_price`, `discount_pct`, `customer_prior_orders`, and the three
categoricals `category`, `channel`, `payment_method`, one-hot encoded. The scan
tells you which of those matters. `category` is the strongest column in the file
you are allowed to use, and on its own it does the work, since the three numerics with
`category` alone score about 0.63, and `channel` and `payment_method` add nothing
measurable. The notebook's last cell is a table of return rate by category, so
the placement student did look at it, and still left it out of the model.

`make test` tells you where you are. If `export_seq` is still in your feature
list, six pass and `test_no_leaked_column_in_the_feature_list` fails, which is
the state it is designed to leave you in. Once you have written the note and
taken the column out, all seven pass. Either is a reasonable place to be at the
end of Friday.

## The evaluation protocol

Task B and Task C both start again from **all 2,030 raw rows**. The two filters
in the notebook belong to Task A and are not part of the reference model; Week 4
is where cleaning is decided properly.

To reproduce the numbers quoted in the lecture, the settings have to match:

| | |
|---|---|
| features | the columns you settle on in Task C. Numerics through a `StandardScaler`, text through a `OneHotEncoder(handle_unknown="ignore")` |
| estimator | `LogisticRegression(max_iter=2000)` |
| cross-validation | `StratifiedKFold(5, shuffle=True, random_state=0)`, scored on `roc_auc` |
| holdout | `train_test_split(test_size=0.25, random_state=7, stratify=y)` |
| preprocessing | inside the pipeline, so it is refitted on each training fold |

The two seeds are different on purpose and both matter: use 7 for the folds as
well and the honest model reads 0.6206, not 0.6243.

## Committing

At least five commits, each one a thing you did rather than a save point. A
message that says `update` or `fix` tells the marker nothing, and the commit
history is assessed.

## Handing in

Nothing is submitted separately this week. Your repository is the submission,
and it is checked by cloning it onto a machine that is not yours and running
`make setup && make run`. That check happens for real in Week 12, but the
demonstrators do a dry run of it on the Friday of Week 2, so it is worth being
ready.
