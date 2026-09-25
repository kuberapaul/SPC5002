# Week 1 homework

**Due Thursday 11:00 of Week 2, before the lecture.** The exact date is on
QMplus. Not marked on its own: it goes in the repository, and the repository is
50 per cent of the module.

Budget about five hours. Week 1 is the light one. From Week 2 the independent
work is closer to eight, so if this takes you fifteen, come and say so on Friday
rather than in November.

## How this is handed in

There is no separate upload. **The repository is the submission**, and a
repository the marker cannot open has not been submitted.

1. The repo lives on **github.qmul.ac.uk** — sign in with your QMUL account.
   Not github.com: your work stays inside the university.
2. Make it **private**. Not public, and not internal. Later in the term you
   will be asked to add the markers to it; there is nothing to do about that
   now.
3. Paste the repo URL into the **Week 1 submission link on QMplus**, once. It
   is the same repository every week until May, so you only do this once.

Pushing uses an **SSH key**, not a password — github.qmul.ac.uk refuses your
QMUL password for git. Friday sets this up: `ssh-keygen -t ed25519`, press
Enter three times, then paste `~/.ssh/id_ed25519.pub` into
github.qmul.ac.uk/settings/ssh/new. The remote is
`git@github.qmul.ac.uk:<you>/spc5002.git` — `git@` and a colon, not `https://`.
The `.pub` file is safe to share. The other one never leaves your machine.

If github.qmul.ac.uk is down or your account is not working, say so on Friday.
As a fallback, `git bundle create week01.bundle --all` writes your entire
history — commits and all — into one file you can upload to QMplus. It is a
safety net, not the normal route.

## 1. Finish the seminar work

Everything from Friday, committed and pushed.

If `export_seq` is still in your feature list, `make test` shows six passing and
`test_no_leaked_column_in_the_feature_list` failing. Part 3 is what clears it.
Whichever way you finished Friday, this homework is handed in with all seven
green and the note written.

## 2. Make it survive a cold clone

Clone your own repository into a directory somewhere else on your machine, make a
fresh virtual environment, and run it.

    git clone <your repo> /tmp/coldclone
    cd /tmp/coldclone
    python -m venv .venv && source .venv/bin/activate
    make setup && make run

Every time this fails, the reason is worth writing down. Most people are stopped
by one of four things: a file that was never committed, a package installed
globally months ago, a path that points at their own home directory, or an
output directory that is expected to exist.

Add a **Running this** section to your `README.md` giving the exact commands.
Assume the reader has Python and nothing else, and that they will not email you.

## 3. The leakage note

`docs/leakage_note.md`, about 300 words. Four questions, in your own words.

1. Which column was it, and what score did it get on its own?
2. What is the mechanism? Not that it correlates with the target, but what
   somebody did, to what system, that put that information into that column.
3. Which of the checks in the notebook would have caught it? Work through them
   one at a time: the train and test split, the scaler, and the metric. Then
   answer the one that is not in the notebook. Would a five-fold
   cross-validation have caught it, and why not?
4. What question would have caught it, and who would you have had to ask?

Marks in this module go to number 2 and number 4. Number 1 is a lookup.

## 4. Five commits

Not five pushes at midnight. Five points at which something changed and you could
say what. Look at your own log afterwards and ask whether you could reconstruct
Friday from it.

    git log --oneline

## Optional, if you want the harder version

Drop `export_seq` in code, immediately after loading, so that nothing
downstream can reach it even by accident. **Do not edit the CSV** — the README
says not to and `test_data_file_is_the_one_we_shipped` checks its hash. Re-run.
The honest model does not move.

(The honest model is the six-column one from Task C, with the three
categoricals in it. If you only deleted `export_seq` from the notebook's list you
are at about 0.53, and the first thing to do is go back to the scan and ask what
you are not using.)

Now explain why removing the column is not a fix, and what would have to change
for you to be confident the same thing has not happened to a different column
that you have not noticed.

That question does not have a clean answer and it is the reason this module
exists.
