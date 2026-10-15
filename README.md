# jam-ai-ranks

Do game-jam entries that disclose generative AI rank differently from those that don't? An open study of
itch.io jam results, by MV2 of Munim, Inc., made with AI agents. Code Apache-2.0; data CC BY 4.0.

**Status (15 October 2026): method 0.2.0; full run queued.** The analysis code was committed before any
data was collected. The pilot run of 0.1.0 found a parser bug (below), so no rank comparison has been
published yet. Results from 0.2.0 will be added here without changing the method again; if it has to
change, the reason will be written down here.

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
Bezemer, FDG 2020, 3,752 games) predates generative AI disclosure; we found no study that relates a
game's own AI disclosure to its jam rank.

## Method

`study.py` reads **every** results page of each jam (`/jam/<slug>/results?page=N`), so each entry's place
is measured against the whole jam. It then reads the game pages of an **evenly spaced sample** of each
jam's ranking (100 per jam in the queued run: the first, the last and evenly between), taking one page
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
  ranking would be wrong.

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

## Pilot (0.1.0, 15 October 2026): top 20 of each jam only

The pilot's one usable number is descriptive: how many of each jam's **top 20** game pages disclose AI.

| jam | AI rule | top-20 pages read | `yes` | `no` | `unanswered` |
|---|---|---|---|---|---|
| Gamedev.js Jam 2026 | allowed | 20 | 9 | 11 | 0 |
| Gamedev.js Jam 2025 | not stated | 20 | 7 | 13 | 0 |
| Game Off 2025 | not stated | 20 | 4 | 14 | 2 |
| GDevelop BIG Game Jam #9 | not stated | 19 | 2 | 17 | 0 |
| AI Browser Game Jam | required | 20 | 19 | 0 | 1 |
| SCREAM JAM 2025 | most AI banned | 20 | 1 | 15 | 4 |
| Brackeys Game Jam 2025.2 | all AI banned | 20 | 0 | 18 | 2 |

Read on 15 October 2026; disclosure is as the page shows it today. These are the very best-placed
entries, not the jams as a whole, and 20 is small; the full run answers the question.

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

`entries_public.csv` has no titles, names, usernames, page addresses or submission ids, so no entry or
creator can be singled out. A private copy with itch's submission ids stays on MV2's machine for
re-checking only.

## Run

```
python -m unittest -v test_study.py
python study.py --jams jams.csv --out out --delay 1.0 --deadline-minutes 290 --games-per-jam 100
```

The tests run the parsers on sample pages (including itch's real pager), the percentiles, the even
sample, the permutation test, a full collect, analyse and write cycle against a fake site, turn-taking
between jams, leaving out a jam with unread results pages, and check the public file carries no
addresses or ids.

Made by MV2 of Munim, Inc. with AI agents (Anthropic Claude). Apache-2.0.
