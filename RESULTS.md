# jam-ai-ranks results (method 0.2.0, read 15-16 October 2026; robustness checked 16 October 2026)

By MV2 of Munim, Inc., made with AI agents (Anthropic Claude). Text CC BY 4.0; code Apache-2.0.

These results were first posted on MV2's itch.io devlog in October 2026 and are added to this repository on
31 October 2026, unchanged except for the two literature references corrected under "How this fits what was known".

**Short answer.** In five itch.io jams that do not ban generative AI, entries whose game page discloses
AI placed **no differently** from entries that say *No generative AI was used*: on average 1.4
percentile points lower, with a 95% interval of 7.7 points lower to 5.0 points higher. The clear gap
is elsewhere: entries that **left the disclosure question unanswered** placed about **17 percentile
points lower** than entries that answered *No* (95% interval 8.7 to 26.4 points; p = 0.001). Both results
hold when any one jam is left out (below). This is an association in one sample of seven jams, not a cause.

The method was fixed and published before this run; nothing in it was changed after seeing the data.
The full run read every results page of every jam (5,125 ranked entries) and an evenly spaced sample of
up to 100 game pages per jam (609 pages classified), between 22:06Z on 15 October and 00:06Z on 16 October
2026. It used 2,000 label shuffles for p-values (so the smallest possible p is 0.0005) and 1,000
resamples for intervals.

## What the sampled game pages say

| jam | AI rule | ranked entries | pages classified | discloses AI | says No AI | unanswered | share disclosing AI |
|---|---|---|---|---|---|---|---|
| Gamedev.js Jam 2026 | allowed, even encouraged | 477 | 99 | 54 | 35 | 9 | 54.5% |
| Gamedev.js Jam 2025 | not stated | 406 | 95 | 20 | 65 | 10 | 21.1% |
| Game Off 2025 | not stated | 690 | 97 | 22 | 70 | 5 | 22.7% |
| GDevelop BIG Game Jam #9 | not stated | 387 | 97 | 12 | 70 | 15 | 12.4% |
| AI Browser Game Jam | required | 25 | 25 | 24 | 0 | 1 | 96.0% |
| SCREAM JAM 2025 | most generative AI banned | 908 | 97 | 2 | 82 | 13 | 2.1% |
| Brackeys Game Jam 2025.2 | all AI banned | 2,232 | 99 | 4 | 85 | 10 | 4.0% |

One Gamedev.js 2026 page showed both a disclosure and the No AI line; it is counted apart. Disclosure is as
the pages show it today, not at jam time.

## Where each group places inside its own jam

Place = percentile inside the entry's whole jam (100 = best, 0 = worst), from the raw overall score.
Differences are pooled over the jams that have both groups; the p-value shuffles labels inside each jam.
The second column uses itch's own ratings-adjusted rank instead; it agrees throughout.

**Jams that do not ban AI** (5 jams, 413 classified pages)

| comparison | entries | difference (raw score) | 95% interval | p | difference (itch rank) |
|---|---|---|---|---|---|
| discloses AI vs everyone else | 132 vs 280 | +0.8 | -5.3 to +6.3 | 0.78 | +1.6 (-4.0 to +7.0) |
| discloses AI vs says No AI | 108 vs 240 (4 jams) | -1.4 | -7.7 to +5.0 | 0.67 | -0.4 (-6.6 to +5.8) |
| says No AI vs unanswered | 240 vs 39 (4 jams) | **+17.5** | **+8.7 to +26.4** | **0.001** | +17.2 (+8.4 to +26.3), p = 0.0005 |
| AI graphics, on the Graphics criterion | 67 vs 280 | -4.9 | -12.1 to +2.2 | 0.16 | |
| AI sound, on the Audio criterion | 38 vs 280 | +8.1 | -1.5 to +17.3 | 0.06 | |

Median number of ratings: 15 for entries disclosing AI, 15.5 for No AI, 13 for unanswered, so raters
saw the groups about equally often.

**Jams that ban AI** (2 jams, 196 classified pages): only 6 sampled pages disclose AI (2 in SCREAM JAM,
whose rule bans *most* generative AI, and 4 in Brackeys, which bans all of it). That is too few to compare
places, and no interval for them is reported here. *No AI* vs unanswered: +8.6 points (95% interval -3.2 to
+20.0; p = 0.18), the same direction as in the other jams but not clear on its own.

## Does one jam drive it? (independent re-check)

A second script (`verify_sampled.py`, which shares no code with `study.py`) re-read the 625 sampled rows, re-derived
the three pooled differences above exactly (+0.8, -1.4, +17.5), found no mismatch, and then split them by jam and
left each jam out in turn (job jam-ai-ranks-verify-v1, 16 October 2026 13:57Z, all tests passed). Percentile points:

| comparison | Game Off 2025 | Gamedev.js 2025 | Gamedev.js 2026 | GDevelop BIG #9 | AI Browser | pooled, leaving one jam out |
|---|---|---|---|---|---|---|
| discloses AI vs says No AI | -3.6 (22 vs 70) | +0.2 (20 vs 65) | -2.8 (54 vs 35) | +2.9 (12 vs 70) | (no No AI) | **-2.0 to -0.7** |
| discloses AI vs everyone else | -3.5 (22 vs 75) | +4.2 (20 vs 75) | +0.4 (54 vs 44) | +5.7 (12 vs 85) | -8.7 (24 vs 1) | **+0.0 to +1.9** |
| says No AI vs unanswered | +1.5 (70 vs 5) | +29.8 (65 vs 10) | +15.8 (35 vs 9) | +16.3 (70 vs 15) | (none) | **+13.3 to +20.2** |

- **No AI penalty in any single jam.** The per-jam differences between disclosing AI and saying No AI go both ways
  and are all within 4 points; leaving any jam out keeps the pooled figure between -2.0 and -0.7.
- **The unanswered gap is not one jam's doing.** Three of the four jams show it at 16-30 points; Game Off, with
  only 5 unanswered pages in its sample, shows +1.5, which says little either way. Leaving any one jam out keeps
  the pooled gap between 13.3 and 20.2 points. Per-jam groups are small (5 to 15 unanswered pages), so the per-jam
  numbers are descriptive only; no per-jam interval is claimed.
- The AI Browser Game Jam row compares 24 disclosing entries with a single other entry and means nothing alone.

## How this fits what was known

- **Steam studies find a penalty.** Bazzaz and Cooper (arXiv preprint, August 2026,
  [arXiv 2608.11539](https://arxiv.org/abs/2608.11539)) found that Steam games disclosing generative AI get lower
  recommendation rates than procedurally generated games. Game Oracle's 2026 analysis of games released on Steam
  in 2025 reported fewer reviews and lower average review scores for games with an AI disclosure. Both look at
  commercial releases and buyers. (An earlier version of this text called the first a CHI PLAY 2026 paper and the
  second a 2025 study; both were corrected on 31 October 2026.)
- **In these jams, raters did not place AI-disclosing entries lower.** Jam raters are often other entrants,
  and the disclosure is shown on each game's page. We found no earlier study that relates an
  itch.io game's own AI disclosure to its jam placing; earlier work on what makes jam games place well (Vu and
  Bezemer, FDG 2020) predates the disclosure field.
- **The unanswered gap is new and is probably about care, not AI.** Leaving an optional question blank may go
  with a less finished page or a rushed entry. This study cannot tell which.

## Limits

- Seven jams, chosen (large jams with results after November 2024 whose AI rules were already recorded), not sampled.
- Game pages are a sample, evenly spaced through each ranking: every page of AI Browser Game Jam, about one in
  four to one in nine in the middle-sized jams, one in 22 in Brackeys. Counts are from the sample.
- Disclosure is read today and self-reported; *unanswered* is not "no AI", and creators may have changed it after the jam.
- Association, not cause: teams that disclose may differ in experience, team size, engine or genre.
- An interval that includes zero means no difference was found at this sample size, not that none exists;
  a gap of up to about 8 points lower or 5 points higher would not have been detected.
- The AI-sound result (p = 0.06) is one of five comparisons and is not treated as a finding.

## Data

`data/summary-2026-10-16.json` holds every number above (jam-level counts, means and comparisons only; no entry is
listed). `data/verify-2026-10-16.json` (from `verify_sampled.py`) holds the per-jam and leave-one-jam-out figures.
The row-level file is not published. If it is, it will be only in the redacted form that `check_results.py` makes:
in the two jams that ban AI, ranks, ratings, scores and engines are removed and places are rounded to one decimal,
so the data cannot be used to single out an entry that discloses AI where AI is banned. `check_results.py` also
re-derives every count, mean and pooled difference from the row file without any code from `study.py`.
