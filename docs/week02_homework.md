# Week 2 homework

**Due Thursday 11:00 of Week 3, before the lecture.** The exact date is on
QMplus. Not marked on its own. It goes in the repository, and parts 2 and 3
become sections of your final report.

There is nothing to upload. Push to the same repository on github.qmul.ac.uk,
over SSH as on the Week 1 Friday. The URL you gave on QMplus in Week 1 still
stands.

Budget about eight hours. This is the first full week.

## 1. Finish the ingestion

`make ingest` runs from a clean clone and writes both
`outputs/ingest_report.json` and `outputs/orders_joined.csv`. Week 4 starts from
the second one, so a missing joined table stops you two weeks from now rather
than today.

`make test` shows 15 passed, your seven from Week 1 and this week's eight.
`make verify` prints four hashes and `the two runs match`.

Every step that can change the row count says how many rows it expects before it
looks. That is the whole of this week and it is four lines of code.

## 2. `docs/sources.md`

One section per source. Four questions each, half a page is plenty.

1. Where does it come from, and who owns it?
2. What does one row mean?
3. What did you have to decide in order to read it? List every decision, not only
   the ones that would have crashed. The encoding, the date format, the currency
   unit, the type coercions, the whitespace, the category mapping.
4. What are you unsure about?

Question 4 is the one that gets read. A source note with nothing in question 4 is
either a source you understood completely, which happens about once, or a source
you did not look at hard enough.

This becomes the dataset section of your final report.

## 3. `docs/join_decision.md`

About 200 words.

- What the join did, in row counts.
- Why 27 duplicated CRM rows produced 34 duplicated orders. Explain it as if to
  somebody who has not seen the data.
- Which resolution you chose for the 27 customers, and why. Keeping the first row
  is a choice. Keeping neither row, so that those customers' region, tenure and
  opt-in stay blank until the CRM owner says which is right, is also a choice.
  Both keep all 1,996 orders and both are defensible, and not choosing is not.
- What you would have asked the CRM owner if you could.

## 4. The column that does not reconcile

Add a section to `docs/sources.md` on `marketing_opt_in`. The CRM leaves it blank
for 32 customers. Twenty-three of them placed 46 orders in 2025, and on every
one of those orders the file you were handed in Week 1 shows an answer the CRM
does not have, true on 34 and false on 12.

Say what you would do. There is no right answer. There are several wrong ones,
and the most common is to keep the values quietly because they are already there
and removing them feels like losing data.

Whatever you decide, it has to survive the question *where did this number come
from*, asked by somebody who will act on it.

## 5. Six commits

Each one a thing you did. Look at `git log --oneline` when you are finished and
ask whether Friday is reconstructable from it.

## Optional, if you finish early

Write the ingestion so that adding a fourth source is a matter of writing one
function rather than editing three. A common shape is a small registry mapping a
source name to a reader, with every reader returning the same columns and types.

Then write two sentences on what you gave up to get that, because you did give
something up. Generic code is harder to read than three explicit functions, and
the next person has to understand the abstraction before they can understand the
storefront.
