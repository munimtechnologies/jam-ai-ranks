# jam-ai-ranks

Do game-jam entries that disclose generative AI rank differently from those that don't? An open study of
itch.io jam results, by MV2 of Munim, Inc., made with AI agents. Code Apache-2.0; data CC BY 4.0.

**Status (14 October 2026): method only.** The analysis code was committed before any data was
collected. The first run is queued, and its results will be added here without changing the method. If
the method has to change, the reason will be written down here.

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

- **Jams that do not ban AI** (Gamedev.js 2026 allows it, Gamedev.js 2025, Game Off 2025, Kenney Jam 2025,
  GDevelop BIG Game Jam #9 and Pirate Software Game Jam 17 say nothing, and AI Browser Game Jam requires it):
  do raters place `yes` entries lower or higher than the rest?
- **Narrower:** in jams with a Graphics (or Audio) criterion, do entries that disclose AI *graphics* (or
  *sound*) place lower **on that criterion**?
- **Jams that ban AI** (SCREAM JAM 2025, Brackeys 2025.2): how many entries say *No AI*, how do they place
  against `unanswered` entries, and how many pages disclose AI anyway? (Counts only; no entry is named.)

The jams and their rules are from [game-jam-ai-rules](https://github.com/munimtechnologies/game-jam-ai-rules),
MV2's quote-backed dataset of jam AI rules. Prior work on what makes itch.io jam games rank well (Vu and
Bezemer, FDG 2020, 3,752 games) predates generative AI disclosure; we found no study that relates a
game's own AI disclosure to its jam rank.

## Method

`study.py` reads each jam's public results pages (`/jam/<slug>/results?page=N`) and each ranked entry's
game page, one request at a time and at least a second apart, with a User-Agent that names Munim, Inc. It
records the entry's rank, number of ratings, score, raw overall score, every criterion's raw score, and the
page's disclosure class, AI parts, engine and whether it plays in the browser.

- **Place in jam** (`pct`, 1 = best, 0 = worst, ties share their mean place) is computed two ways: from the
  raw overall score (`pct_raw`, the main measure) and from itch's own rank (`pct_rank`), which scales down
  entries with few ratings.
- **Comparison:** the mean place of one class minus another, pooled over the jams that have both. The
  p-value comes from shuffling class labels **inside each jam** (so jam size and jam quality cancel out),
  and the 95% interval from resampling each class inside each jam.
- Comparisons: `yes` vs (`no` + `unanswered`), `yes` vs `no`, `no` vs `unanswered`, and per criterion
  (AI graphics on Graphics, AI sound on Audio), separately for jams that ban AI and jams that don't.

## Limits, stated up front

- **Disclosure is read today, not at jam time.** Creators can change it after the jam, and many games were
  submitted before they answered.
- **Self-report.** `unanswered` is not "no AI", and `no` is the creator's word.
- **Association, not cause.** Teams that disclose may differ in experience, team size, engine or genre.
  Engine and browser play are recorded so that can be looked at, but the study cannot separate them.
- **Only ranked entries.** Entries with too few ratings to rank are not in the results pages.
- The jams were chosen (big jams with results after November 2024 whose AI rules we had already
  recorded), not sampled.

## Privacy

`entries_public.csv` has no titles, names, usernames, page addresses or submission ids, so no entry or
creator can be singled out. A private copy with itch's submission ids stays on MV2's machine for
re-checking only.

## Run

```
python -m unittest -v test_study.py
python study.py --jams jams.csv --out out --delay 1.0 --deadline-minutes 280
```

The tests run the parsers on sample pages, the percentiles, the permutation test and a full collect,
analyse and write cycle against a fake site, and check the public file carries no addresses or ids.

Made by MV2 of Munim, Inc. with AI agents (Anthropic Claude). Apache-2.0.
