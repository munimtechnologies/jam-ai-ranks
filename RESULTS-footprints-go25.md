# Results: AI-agent footprints and AI disclosure in GitHub Game Off 2025 (baseline)

By MV2 of Munim, Inc., made with AI agents (Anthropic Claude). Text and data CC BY 4.0; code Apache-2.0.
Graded on 1 November 2026 against [PREREGISTRATION-game-off-2026.md](PREREGISTRATION-game-off-2026.md),
which was published on 31 October 2026. The data job waited until that file was public on GitHub (seen at
2026-11-01 06:38 UTC, SHA-256 `094fe25d...b555`) before it read any page or repository. Aggregate counts:
[data/footprints-go25-summary.json](data/footprints-go25-summary.json).

## In short

- **17 of 533** Game Off 2025 repositories that could be read (**3.2%**, 95% interval 2.0% to 5.1%) held a
  file or commit line that an AI coding agent leaves behind (`AGENTS.md`, `CLAUDE.md`, Copilot
  instructions, `.cursor`, Kiro files, or a `Co-authored-by` line naming an agent) at the jam deadline.
- **11 of those 17** game pages disclose AI on itch.io; **6 of 17** (35%) do not. Repositories whose page
  discloses AI carry a footprint about six times as often as the rest (9.0% against 1.5%).
- **533 of 690** ranked entries (77%) still have a repository that can be read. 72 linked repositories
  could not be cloned a year after the jam; four of four checked by hand now return "not found".
- Pre-registered predictions: **B1 held, B2 held, B3 failed.**

## Grades

| | prediction | result | grade |
|---|---|---|---|
| B1 | footprint share among analysable repositories between 1.0% and 10.0% | 17 of 533 = 3.2% (2.0% to 5.1%) | **held** |
| B2 | at least 30% of footprint entries with a read page do not disclose AI (graded if at least 10) | 6 of 17 = 35.3% (17.3% to 58.7%) | **held** |
| B3 | at least 80% of ranked entries have an analysable repository | 533 of 690 = 77.2% (74.0% to 80.2%) | **failed** |

Intervals are 95% Wilson intervals. B2 held on its point estimate, but with only 17 entries its interval
reaches well below 30%, so it is weak evidence either way. B3 missed by about 19 entries.

## What was read

- All 35 results pages of `game-off-2025`: **690** ranked entries. **668** game pages were read (the other
  22 could not be read).
- **621** submission pages gave a GitHub repository link; **69** did not (one checked by hand answers the
  repository question with the game's own itch.io page).
- Of the 621 repositories: **533** analysable (a commit on the default branch before the deadline,
  2025-12-01 21:37 UTC), **72** could not be cloned, **9** have no commit before the deadline, **7** are empty.
  One of the 72 "repository" links was a GitHub user page, not a repository: the reader's fallback took it.
  It is counted as not analysable, as the method says, and it does not change any grade.
- Each repository was read as a blob-less bare clone (history and file names only, no file contents), cut
  at the last commit before the deadline.

## Footprints

- **17 of 533** (3.2%). Markers at the repository root only: 14 of 533 (2.6%).
- **15** of the 17 show an agent file in the repository; footprints from commit lines alone: fewer than 5.
  Markers found only inside vendored folders (`addons/`, `Packages/` and the like) do not count; that
  adds fewer than 5.
- Families (an entry can have more than one): `AGENTS.md` **8**, Claude (`CLAUDE.md`, `.claude/`, or a
  Claude Code commit line) **7**, GitHub Copilot, Cursor and Kiro fewer than 5 each.
- At today's default branch: **19 of 542** readable repositories (3.5%), so a few footprints were added
  after the jam ended.

For scale (different populations and dates, so not a like-for-like comparison): 26.3% of 22,854 popular,
active GitHub repositories had an agent instruction file in October 2026 (Zarzycki, arXiv 2610.31715), and
a DEV Community sample by janzong found AGENTS.md or CLAUDE.md in 9.4% of active repositories in September
2026. Jam repositories from November 2025 sit well below both. Game Off 2026 (read in January 2027) will
show how much this changed in a year.

## Footprints and the itch.io disclosure

Among the 533 analysable entries:

| page shows | footprint | no footprint |
|---|---|---|
| AI Assisted (`yes`) | 11 | 111 |
| No generative AI was used (`no`) | fewer than 5 | 335 |
| question unanswered | fewer than 5 | 63 |
| other, or page not read | 0 | 7 |

- **11 of 122** entries whose page discloses AI have a footprint (9.0%, 5.1% to 15.4%), against **6 of 411**
  of the rest (1.5%, 0.7% to 3.1%).
- **6 of 17** footprint entries do not disclose AI: their page says *No generative AI was used* or leaves the
  question unanswered (fewer than 5 each).

This is not evidence that anyone misled anyone. Game Off states no AI rule, itch.io's question is optional
and self-reported, many people read "generative AI" as art and sound only, an agent file can come from a
template, and a footprint shows that an agent was set up or credited, not how much of the game it made. A
repository without a footprint may still have been made with AI: most tools leave no file.

## Placing (exploration, not predicted)

Place inside the jam (1 = best, 0 = worst), from the raw overall score, with study.py's shuffle test:

- Disclosing AI vs *No AI*: **-3.3** percentile points (95% -8.6 to +2.3; p = 0.23).
- *No AI* vs unanswered: **+8.8** points (95% +1.6 to +16.0; p = 0.012). The same direction as this
  repository's [five-jam result](RESULTS.md), but Game Off 2025 was one of those five jams (there through a
  100-page sample), so this is not an independent replication.
- Footprint vs no footprint: **+3.8** points (95% -7.1 to +14.8; p = 0.61, 17 entries): no detectable
  difference.

Using itch's own rank instead of the raw score gives the same picture (-1.9, +7.3 and +2.5 points).

## Limits

- Disclosures are read today (November 2026), a year after the jam; creators can change them.
- 23% of ranked entries have no analysable repository, mostly because the repository was later deleted or
  made private. If teams that used agents removed their repositories more or less often than others, the
  3.2% is biased in an unknown direction.
- One jam, one year. Commit dates can be set by hand; the deadline cut trusts them.
- The footprint list is the one fixed in footprints.py 0.1.0; tools that leave other files are missed.

## Changes since the pre-registration

None. footprints.py 0.1.0 and the predictions were used as published. The reader's fallback that took a
user page as a repository (above) is noted, not fixed, so the 2026 read uses the same method; any fix will
be dated here first and the 2025 baseline re-read with it as a sensitivity check.

## Reproduce

```
python footprints.py --jam game-off-2025 --cutoff 2025-12-01T21:37:00Z --out out-go25 --delay 1.0
```

The row file names repositories, so it stays on MV2's machine and is not published. Only the counts above
and in `data/footprints-go25-summary.json` are public. MV2 does not enter Game Off 2026 and never rates
entries in it.

MV2 of Munim, Inc., mv2@munimtech.com. Made with AI agents (Anthropic Claude) working in his name.
