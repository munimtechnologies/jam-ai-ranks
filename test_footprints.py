# Tests for footprints.py. By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
import os
import shutil
import subprocess
import tempfile
import unittest

import footprints as fp

RATE_PAGE = """<html><body><div class="header"><a href="https://github.itch.io">GitHub</a>
<a href="https://github.com/features/copilot">Copilot</a></div>
<div class="fields"><div class="field"><h3>GitHub repository URL</h3>
<p><a href="https://github.com/Some-Owner/My.Game.git" rel="nofollow">https://github.com/Some-Owner/My.Game.git</a></p></div>
<div class="field"><h3>Game description</h3><p>See https://github.com/other/thing too</p></div></div>
</body></html>"""


class RepoLinkTest(unittest.TestCase):
    def test_answer_after_label(self):
        self.assertEqual(fp.repo_from_rate_page(RATE_PAGE), "Some-Owner/My.Game")

    def test_no_label_tree_link(self):
        page = "<p>Source: <a href='https://github.com/a-b/c_d/tree/main'>repo</a></p>"
        self.assertEqual(fp.repo_from_rate_page(page), "a-b/c_d")

    def test_trailing_full_stop(self):
        self.assertEqual(fp.repo_from_rate_page("<p>Code at https://github.com/x/y.</p>"), "x/y")

    def test_github_own_pages_only(self):
        page = "<a href='https://github.com/features/copilot'>x</a> <a href='https://github.itch.io'>y</a>"
        self.assertEqual(fp.repo_from_rate_page(page), "")


class PathTest(unittest.TestCase):
    def test_root_file(self):
        s = fp.path_signals(["CLAUDE.md", "src/main.gd"])
        self.assertEqual(s, {"families": ["claude"], "families_any": ["claude"], "root": True})

    def test_vendored_marker_counted_apart(self):
        s = fp.path_signals(["addons/foo/AGENTS.md", "project.godot"])
        self.assertEqual(s, {"families": [], "families_any": ["agents_md"], "root": False})

    def test_folders(self):
        self.assertEqual(fp.path_signals([".cursor/rules/game.mdc"])["families"], ["cursor"])
        self.assertEqual(fp.path_signals([".claude/settings.json"])["families"], ["claude"])
        self.assertEqual(fp.path_signals([".clinerules/style.md"])["families"], ["cline"])

    def test_copilot_files(self):
        self.assertEqual(fp.path_signals([".github/copilot-instructions.md"])["families"], ["copilot"])
        self.assertEqual(fp.path_signals([".github/instructions/ui.instructions.md"])["families"], ["copilot"])
        self.assertEqual(fp.path_signals([".github/workflows/build.yml"])["families"], [])

    def test_nested_aider_not_root(self):
        s = fp.path_signals(["docs/.aider.chat.history.md"])
        self.assertEqual(s["families"], ["aider"])
        self.assertFalse(s["root"])

    def test_unity_packages_is_vendored(self):
        s = fp.path_signals(["Packages/com.example.tool/CLAUDE.md"])
        self.assertEqual(s["families"], [])
        self.assertEqual(s["families_any"], ["claude"])

    def test_plain_game(self):
        s = fp.path_signals(["README.md", "project.godot", "scenes/main.tscn", "LICENSE"])
        self.assertEqual(s, {"families": [], "families_any": [], "root": False})


class CommitTest(unittest.TestCase):
    def test_claude_code_trailer(self):
        msg = ("Fix jump\n\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
               "Co-Authored-By: Claude <noreply@anthropic.com>\n")
        self.assertEqual(fp.commit_signals([("Ann", "ann@example.org", "ann@example.org", msg)]), ["claude"])

    def test_person_named_claude_is_not_an_agent(self):
        msg = "Level two\n\nCo-authored-by: Claude Martin <claude.martin@example.org>\n"
        self.assertEqual(fp.commit_signals([("Ann", "ann@example.org", "ann@example.org", msg)]), [])
        msg = "Art\n\nCo-authored-by: Jules Devin <jules@example.org>\n"
        self.assertEqual(fp.commit_signals([("Ann", "ann@example.org", "ann@example.org", msg)]), [])

    def test_copilot_author_and_trailer(self):
        bot = ("Copilot", "198982749+Copilot@users.noreply.github.com", "noreply@github.com", "Add menu")
        self.assertEqual(fp.commit_signals([bot]), ["copilot"])
        msg = "Menu\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>"
        self.assertEqual(fp.commit_signals([("Ann", "a@example.org", "a@example.org", msg)]), ["copilot"])

    def test_aider_trailer_names_only_aider(self):
        msg = "Tweak\n\nCo-authored-by: aider (anthropic/claude-3-5-sonnet) <noreply@aider.chat>"
        self.assertEqual(fp.commit_signals([("Ann", "a@example.org", "a@example.org", msg)]), ["aider"])

    def test_cursor_agent(self):
        bot = ("Cursor Agent", "cursoragent@cursor.com", "cursoragent@cursor.com", "Refactor")
        self.assertEqual(fp.commit_signals([bot]), ["cursor"])

    def test_parse_log(self):
        text = ("A\x1fa@example.org\x1fc@example.org\x1fmsg one\n\n"
                "Co-authored-by: Copilot <1+Copilot@users.noreply.github.com>\n\x1e\n"
                "B\x1fb@example.org\x1fb@example.org\x1fmsg two\n\x1e\n")
        commits = fp.parse_log(text)
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[1][0], "B")
        self.assertEqual(fp.commit_signals(commits), ["copilot"])


class StatsTest(unittest.TestCase):
    def test_wilson(self):
        lo, hi = fp.wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.7634, places=3)
        self.assertIsNone(fp.wilson(0, 0))

    def test_newcombe(self):
        d = fp.newcombe(5, 10, 5, 10)
        self.assertEqual(d["diff"], 0.0)
        self.assertLess(d["ci95"][0], 0)
        self.assertAlmostEqual(d["ci95"][0], -d["ci95"][1], places=4)
        d = fp.newcombe(60, 100, 20, 100)
        self.assertEqual(d["diff"], 0.4)
        self.assertGreater(d["ci95"][0], 0)
        self.assertIsNone(fp.newcombe(1, 0, 1, 2))

    def test_git_date(self):
        self.assertEqual(fp.git_date("2025-12-01T21:37:00Z"), "2025-12-01 21:37:00 +0000")


def row(ai_class, status, fp_=None, fams=(), path=None, commit=None, head=None, pct=0.5, repo="o/r"):
    return {"jam": "j", "page_status": "200" if ai_class else "404", "ai_class": ai_class, "repo": repo,
            "repo_status": status, "fp": fp_, "fp_any": fp_, "fp_root": bool(fp_), "fp_path": path,
            "fp_commit": commit, "fp_head": head, "fp_families": list(fams), "pct_raw": pct, "pct_rank": pct}


class AnalyseTest(unittest.TestCase):
    def test_counts(self):
        rows = [row("yes", "ok", True, ["claude"], True, True, True, 0.9),
                row("no", "ok", True, ["cursor"], True, False, True, 0.7),
                row("no", "ok", False, [], False, False, False, 0.5),
                row("unanswered", "ok", False, [], False, False, False, 0.1),
                row("yes", "late", None, [], None, None, True, 0.3),
                row("", "no_repo_link", repo="")]
        s = fp.analyse(rows, "j", "2025-12-01T21:37:00Z", iters=50)
        self.assertEqual(s["ranked"], 6)
        self.assertEqual(s["game_pages_read"], 5)
        self.assertEqual((s["discloses_ai"]["k"], s["discloses_ai"]["n"]), (2, 5))
        self.assertEqual(s["repo_found"], 5)
        self.assertEqual(s["repo_status"], {"ok": 4, "late": 1})
        self.assertEqual((s["footprint"]["k"], s["footprint"]["n"]), (2, 4))
        self.assertEqual((s["footprint_not_disclosing"]["k"], s["footprint_not_disclosing"]["n"]), (1, 2))
        self.assertEqual((s["footprint_at_head_today"]["k"], s["footprint_at_head_today"]["n"]), (3, 5))
        self.assertEqual(s["families"], {"claude": 1, "cursor": 1})
        self.assertEqual((s["footprint_path_only"], s["footprint_commit_only"], s["footprint_path_and_commit"]),
                         (1, 0, 1))
        self.assertEqual(s["crosstab"]["no"], {"footprint": 1, "none": 1})
        self.assertEqual(s["places"]["pct_raw"]["footprint_vs_none"]["diff"], 0.5)
        text = str(s)
        self.assertNotIn("o/r", text)


@unittest.skipUnless(os.name == "posix" and shutil.which("git"), "needs git on a POSIX system")
class ReadRepoTest(unittest.TestCase):
    def test_cutoff_and_head(self):
        root = tempfile.mkdtemp()
        src = os.path.join(root, "src")
        try:
            subprocess.run(["git", "init", "-q", src], check=True)

            def commit(files, msg, date):
                for name, body in files.items():
                    path = os.path.join(src, name)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as f:
                        f.write(body)
                env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
                who = ["-c", "user.name=T", "-c", "user.email=t@example.org"]
                subprocess.run(["git"] + who + ["add", "-A"], cwd=src, check=True, env=env)
                subprocess.run(["git"] + who + ["commit", "-q", "-m", msg], cwd=src, check=True, env=env)

            commit({"README.md": "game"}, "start", "2025-11-10T12:00:00+0000")
            commit({"CLAUDE.md": "notes", "addons/tool/AGENTS.md": "x"},
                   "add notes\n\nCo-Authored-By: Claude <noreply@anthropic.com>", "2025-11-20T12:00:00+0000")
            commit({".cursorrules": "x"}, "after the jam", "2025-12-05T12:00:00+0000")
            got = fp.read_repo("t/t", "2025-12-01T21:37:00Z", root, url="file://" + src)
            self.assertEqual(got["status"], "ok")
            self.assertEqual(got["cut"]["path_families"], ["claude"])
            self.assertEqual(got["cut"]["path_families_any"], ["agents_md", "claude"])
            self.assertEqual(got["cut"]["commit_families"], ["claude"])
            self.assertEqual(got["cut"]["commits"], 2)
            self.assertEqual(got["head"]["path_families"], ["claude", "cursor"])
            late = fp.read_repo("t/t", "2025-11-01T00:00:00Z", root, url="file://" + src)
            self.assertEqual(late["status"], "late")
            gone = fp.read_repo("t/t", "2025-12-01T21:37:00Z", root, url="file://" + root + "/missing")
            self.assertEqual(gone["status"], "clone_failed")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
