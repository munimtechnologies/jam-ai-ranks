# jam-ai-ranks

Do game-jam entries that disclose generative AI rank differently from those that don't? An open study of
itch.io jam results, by MV2 of Munim, Inc., made with AI agents. Code Apache-2.0; data CC BY 4.0.

**Status (1 November 2026): method 0.2.0; full run done 16 October 2026. Results: [RESULTS.md](RESULTS.md).**
In five jams that do not ban AI, entries disclosing AI placed no differently from entries saying *No AI* (-1.4
percentile points, 95% interval -7.7 to +5.0). Entries that left the question unanswered placed about 17
points lower than *No AI* entries (95% interval 8.7 to 26.4), and that gap stays between 13.3 and 20.2 points
when any one jam is left out. The analysis code was committed before any data was collected and was not
changed after seeing it.

**New (1 November 2026): Game Off 2025 footprint baseline, [RESULTS-footprints-go25.md](RESULTS-footprints-go25.md).**
GitHub Game Off asks every entry for a public repository, so its games carry two records of AI use: the
itch.io disclosure and the files and commit lines AI coding agents leave in a repository (`CLAUDE.md`,
`AGENTS.md`, `.cursorrules`, Copilot instructions, `Co-authored-by` lines). At the 2025 deadline, 17 of 533
readable repositories (3.2%) held such a footprint; 11 of those 17 game pages disclose AI and 6 do not.
Pages that disclose AI carry a footprint about six times as often as the rest (9.0% against 1.5%). Only 533
of 690 ranked entries (77%) still have a readable repository a year on. Of the three pre-registered baseline
predictions, B1 and B2 held and B3 (at least 80% readable) failed. Game Off 2026 is read after its results in
January 2027 under the same [pre-registration](PREREGISTRATION-game-off-2026.md). Only counts are published;
no entry or repository is named.

## The question

Since November 2024 itch.io has asked creators a "Generative AI disclosure" question on every project. A
game page then shows one of three things:

| class | what the game page shows |
|---|---|
| `yes` | an **AI Disclosure** row: *AI Assisted*, plus any of *Code*, *Graphics*, *Sounds*, *Text* |
| `no` | *No generative AI was used* (the No AI tag) |
| `unanswered` | neither (the question is optional for games) |

Jam results pages rank every rated entry. This study joins the two: for each ranked entry, where does it
place **inside its own jam**, and does that differ by disclosure class?

- **Jams that do not ban AI** (Gamedev.js 2026 allows it, Gamedev.js 2025, Game Off 2025 and GDevelop BIG
  Game Jam #9 say nothing, and AI Browser Game Jam requires it): do raters place `yes` entries lower or
  higher than the rest?
- **Narrower:** in jams with a Graphics (or Audio) criterion, do entries that disclose AI *graphics* (or
  *sound*) place lower **on that criterion**?
- **Jams that ban AI** (SCREAM JAM 2025, Brackeys 2025.2): how many entries say *No AI*, how do they place
  against `unanswered` entries, and how many pages disclose AI anyway? (Counts only; no entry is named.)

The jams and their rules are from [game-jam-ai-rules](https://github.com/munimtechnologies/game-jam-ai-rules),
MV2's quote-backed dataset of jam AI rules. Prior work on what makes itch.io jam games rank well (Vu and
Bezemer, FDG 2020, 3,752 games) predates generative AI disclosure, and studies of AI disclosure on Steam
(Bazzaz and Cooper, arXiv 2608.11539, 2026; Game Oracle, 2026) look at commercial releases; we found no study
that relates a game's own AI disclosure to its jam rank.

## Method

`study.py` reads **every** results page of each jam (`/jam/<slug>/results?page=N`), so each entry's place
is measured against the whole jam. It then reads the game pages of an **evenly spaced sample** of each
jam's ranking (100 per jam in the full run: the first, the last and evenly between), taking one page
from each jam in turn. All requests go one at a time, at least a second apart, with a User-Agent that
names Munim, Inc. It records the entry's rank, number of ratings, score, raw overall score, every
criterion's raw score, and the sampled page's disclosure class, AI parts, engine and whether it plays in
the browser.

- **Place in jam** (`pct`, 1 = best, 0 = worst, ties share their mean place) is computed two ways: from the
  raw overall score (`pct_raw`, the main measure) and from itch's own rank (`pct_rank`), which scales down
  entries with few ratings.
- **Comparison:** the mean place of one class minus another, pooled over the jams that have both. The
  p-value comes from shuffling class labels **inside each jam** (so jam size and jam quality cancel out),
  and the 95% interval from resampling each class inside each jam.
- Comparisons: `yes` vs (`no` + `unanswered`), `yes` vs `no`, `no` vs `unanswered`, and per criterion
  (AI graphics on Graphics, AI sound on Audio), separately for jams that ban AI and jams that don't.
- A jam whose results pages could not all be read is left out entirely, since places inside a partial
  ranking would be wrong. In the full run every results page of all seven jams was read.

## Checks after the run

- `verify_sampled.py` shares no code with `study.py`. It re-reads the 625 sampled rows, re-derives every
  jam-level count and mean and the three pooled differences, and splits each difference by jam and with each
  jam left out. On the full run it found no mismatch (`data/verify-2026-10-16.json`).
- `check_results.py` re-derives the same figures from the study's row file and writes the redacted copy
  described under Privacy.
- `test_footprints_go25_results.py` checks that the Game Off 2025 footprint counts add up, that every share
  and Wilson interval matches its counts, that the grades follow the pre-registered rules, that small cells
  are hidden, and that the results text quotes the same numbers.

## Changes to the method, and why

- **0.2.0 (15 October 2026).** The 0.1.0 pilot read only the first results page of every jam. itch.io
  writes its pager as `Page 1 of <a href="?page=24">24</a>`, and the page-count pattern did not allow
  the link, so every jam looked like a one-page jam. Places were therefore computed among each jam's top
  20 entries only, which says nothing about the whole field, so its rank comparisons are not reported.
  Fixed, with a test on itch's real pager markup. Reading every game page of every jam would take about
  ten hours at itch's rate limits, so game pages are now an evenly spaced sample, interleaved across
  jams so a deadline shortens every jam's sample instead of dropping the last jams.
- **Kenney Jam 2025 and Pirate Software Game Jam 17 are out.** Their results pages show places but every
  score as *n/a*, so there is no score to place an entry by.
- The rate limiter now speeds back up (never below one second) after 20 answers in a row; in the pilot
  it stayed at its slowest after the first few 429 answers.
- **Full run (16 October 2026):** run with `--iters 2000` (2,000 shuffles, 1,000 resamples) to fit the
  time limit. No other change.

## Limits, stated up front

- **Disclosure is read today, not at jam time.** Creators can change it after the jam, and many games were
  submitted before they answered.
- **Self-report.** `unanswered` is not "no AI", and `no` is the creator's word.
- **Association, not cause.** Teams that disclose may differ in experience, team size, engine or genre.
  Engine and browser play are recorded so that can be looked at, but the study cannot separate them.
- **Only ranked entries.** Entries with too few ratings to rank are not in the results pages.
- **A sample of game pages.** Each jam's disclosure counts come from its sampled pages, not all of them.
- The jams were chosen (big jams with results after November 2024 whose AI rules we had already
  recorded), not sampled.

## Privacy

The study's raw `entries_public.csv` has no titles, names, usernames, page addresses or submission ids,
but a jam plus a rank still points to one entry on the public results page. So it is **not** published
as it is, and no row-level file is published yet. `check_results.py` makes `entries_public_redacted.csv`:
rows from jams that allow AI are kept (rank, score and disclosure are all public on itch.io already), while in
the two jams that ban AI ranks, ratings, scores and engines are removed, places are rounded to one decimal and
the rows are re-sorted, so no entry that discloses AI where AI is banned can be found from the data. A private
copy with itch's submission ids stays on MV2's machine for re-checking only.

`footprints.py` writes only counts to `summary.json`. Its row file names repositories and stays on MV2's
machine; it is never published. The published `data/footprints-go25-summary.json` shows counts from 1 to 4
as "fewer than 5".

## Run

```
python -m unittest -v test_study.py test_check_results.py test_verify_sampled.py test_footprints.py test_footprints_go25_results.py
python study.py --jams jams.csv --out out --delay 1.0 --deadline-minutes 290 --games-per-jam 100 --iters 2000
python check_results.py --run-dir out --out check
python verify_sampled.py --parts <folder of sampled rows> --run <folder with summary.json and ranked_counts.json> --out check
python footprints.py --jam game-off-2025 --cutoff 2025-12-01T21:37:00Z --out out-go25
```

`test_study.py` runs the parsers on sample pages (including itch's real pager), the percentiles, the even
sample, the permutation test, a full collect, analyse and write cycle against a fake site, turn-taking
between jams, leaving out a jam with unread results pages, and checks the public file carries no
addresses or ids. `test_check_results.py` checks the independent re-derivation against values worked out
by hand and the redaction; `test_verify_sampled.py` checks the per-jam and leave-one-jam-out splits by hand.
`test_footprints.py` checks the repository-link reader, every marker rule (including that vendored markers
and people called Claude or Devin do not count), the intervals, the counts, and, where git is installed, a
real clone cut at a deadline.

Made by MV2 of Munim, Inc. with AI agents (Anthropic Claude). Apache-2.0.
