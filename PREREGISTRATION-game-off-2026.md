# Pre-registration: AI-agent footprints and AI disclosure in GitHub Game Off 2025 and 2026

By MV2 of Munim, Inc., made with AI agents (Anthropic Claude). Text CC BY 4.0; code Apache-2.0.
Written and published on 31 October 2026, before GitHub Game Off 2026 opens (1 November 2026, 21:37 UTC)
and before any of the 2025 data below has been read. MV2 does not enter Game Off 2026 and never rates
entries in it.

## Question

Game Off asks every entry for a public GitHub repository, and itch.io asks every game page whether
generative AI was used. That makes Game Off a rare place where two records of AI use sit side by side
for the same games:

1. **What the page says**: the itch.io disclosure (*AI Assisted* with Code / Graphics / Sounds / Text,
   *No generative AI was used*, or unanswered), read exactly as in this repository's study.py 0.2.0.
2. **What the repository shows**: files and commit lines that AI coding agents leave behind, such as
   `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules`, `.cursor/`, `.claude/`,
   `.github/copilot-instructions.md`, `.aider*`, `.windsurf/`, `.clinerules`, or a
   `Co-authored-by: Claude <noreply@anthropic.com>` / Copilot / Cursor Agent commit line.

How common are such footprints in jam repositories, how did that change from November 2025 to
November 2026, and how often does a game whose repository shows one also disclose AI on its page?

## What is already known

Counts of agent instruction files exist for general GitHub repositories: 26.3% of 22,854 popular, active
repositories (Zarzycki, arXiv 2610.31715, October 2026), and 9.4% of a random sample of active repositories
for AGENTS.md or CLAUDE.md (a DEV Community sample by the author janzong, September 2026). This repository's
own October 2026 results compared AI disclosure with jam placing. Searches on 31 October 2026 found no count
of agent footprints in game-jam repositories and no comparison of footprints with an AI disclosure.

## Data and method (fixed now)

- **Jams.** GitHub Game Off 2025 (`game-off-2025`, deadline 2025-12-01 21:37 UTC) and Game Off 2026
  (`game-off-2026`, deadline 2026-12-01 21:37 UTC as shown on its page on 31 October 2026). Neither page
  states an AI rule.
- **Entries.** Every ranked entry on every results page, with every game page read (no sampling), using
  study.py's own `collect`, `classify` and percentile code.
- **Repository.** The first GitHub repository link after the "GitHub repository URL" answer on the
  entry's submission page (else the first repository link on that page).
- **Reading a repository.** A blob-less bare clone (`git clone --bare --filter=blob:none`): history and
  file names only, no file contents. The tree and history are taken at the **last commit on the default
  branch made before the jam's deadline**. A repository that cannot be cloned, is empty, or has no commit
  before the deadline is not analysable and is reported apart.
- **Footprint.** At least one counted marker from `footprints.py` 0.1.0 in this repository: the path
  markers and commit markers listed in its code. Markers under vendored folders (`addons/`, `Packages/`,
  `Plugins/`, `node_modules/`, `vendor/`, `third_party/`, `external/`, `library/`) are counted apart and
  do not make a footprint. A Co-authored-by line counts only when it names the agent's product or
  address, never a first name alone (a person called Claude, Devin or Jules is not a footprint).
- **Shares** get 95% Wilson intervals; differences between two shares get Newcombe's 95% hybrid score
  interval. Place comparisons use study.py's `compare` (percentile inside the jam, raw overall score,
  2,000 label shuffles).

## Timeline

- **Baseline (Game Off 2025):** read by job `footprints-go25-v1`, which waits until this file is public
  on GitHub, records its SHA-256, and only then reads any page or repository.
- **Game Off 2026:** read once its results are public (voting ends 1 January 2027), within 14 days.
  The 2025 baseline is read again on the same day as a sensitivity check; the primary comparison uses the
  baseline read now.

## Predictions

Baseline, Game Off 2025 (graded when the baseline job finishes):

- **B1.** The footprint share among analysable repositories is between 1.0% and 10.0%.
- **B2.** Of 2025 entries with a footprint and a read game page, at least 30% do not disclose AI (the
  page says No AI or leaves it unanswered). Graded only if there are at least 10 such entries.
- **B3.** At least 80% of ranked entries have an analysable repository.

Game Off 2026 (graded after its results; **core: G1, G2, G3**):

- **G1.** The 2026 footprint share is at least twice the 2025 baseline share, and the Newcombe interval
  for the difference lies above zero.
- **G2.** The share of read 2026 game pages disclosing AI is higher than the 2025 baseline share, and the
  Newcombe interval for the difference lies above zero.
- **G3.** Of 2026 entries with a footprint and a read game page, at least 25% do not disclose AI.
  Graded only if there are at least 20 such entries.
- **G4.** In Game Off 2026, entries disclosing AI and entries saying No AI place within 8 percentile
  points of each other (point estimate).
- **G5.** In Game Off 2026, entries saying No AI place above entries that leave the question unanswered
  (point estimate above zero).
- **G6.** Claude markers are the most common footprint family in 2026 (more entries than any other family;
  `AGENTS.md` alone is its own family, not Claude).
- **G7.** The Game Off 2026 page still states no AI rule when its results are read.

Not predicted, reported as exploration: placing of entries with and without a footprint; root versus
nested markers; path-only versus commit-only footprints; footprints at today's default branch versus at
the deadline; the share of footprint entries whose page says *No generative AI was used*.

## What this cannot show, and what will not be published

- A footprint shows that an agent was set up or credited in the repository, not how much of the game it
  made. A page without a disclosure is not a false statement: Game Off has no AI rule, itch.io's question
  is optional and self-reported, and people may read "generative AI" as assets only. The results will
  not call any entrant dishonest.
- A repository without a footprint may still have been made with AI (many tools leave no file).
  Footprints can come from a template a team started from, and commit dates can be set by hand.
- **Only counts are published.** No entry, game, repository or person is named, and the row file (which
  names repositories) stays on MV2's machine. A result that would single out one entry in a small cell is
  reported as "fewer than 5".

## Changes

Any change after this date (for example a bug fix in `footprints.py`) is listed in the results file with
its date and reason, and the predictions above are graded as written.
