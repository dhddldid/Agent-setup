"""병렬 점검: 임시 DB·라우터 출력만 사용하는 단위 시험."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("parallel_gaps", Path(__file__).resolve().parents[1] / "scripts/check_parallel_gaps.py")
assert SPEC is not None and SPEC.loader is not None
gaps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gaps)


class ParallelGapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.corpus = self.root / "corpus.json"
        self.corpus.write_text(json.dumps({"schema_version": "ko_routing_corpus/v1", "cases": [
            {"text": "로그인과 검색 개발", "kind": "multi", "expect_any": ["dag-ulw"]},
            {"text": "오타 고쳐줘", "kind": "small", "expect_any": ["quick"]}]}))

    def fake_run(self, skills):
        values = iter(skills)
        def run(command, **kwargs):
            output = json.dumps({"route": {"selected_skill": "ignored"},
                                 "recommendations": [{"skill": next(values)}]})
            return subprocess.CompletedProcess(command, 0, output, "")
        return run

    def fake_hint(self, skills, source="user_trigger_pack"):
        values = iter(skills)
        def hint(text):
            return {"selected_workflow": next(values), "hints": [{"id": source}]}
        return hint

    def test_routing_misses_thresholds(self):
        for limit, exceeded in ((0, True), (1, False)):
            with patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["dag-ulw", "quick"])):
                result = gaps.routing(self.corpus, max_multi_misses=limit, max_small_misses=limit,
                                      hint_function=self.fake_hint(["deep-interview", "dag-ulw"]))
            self.assertEqual((result["multi_misses"], result["small_misses"]), (1, 1))
            self.assertEqual(result["threshold_exceeded"], exceeded)
            self.assertEqual([r["classification"] for r in result["results"]], ["miss", "small-false-positive"])
            self.assertEqual(result["results"][0]["recommend_top1"], "dag-ulw")

    def test_small_needs_no_expect_any_and_multi_does(self):
        data = json.loads(self.corpus.read_text())
        del data["cases"][1]["expect_any"]
        self.corpus.write_text(json.dumps(data))
        with patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["wrong", "dag-ulw"])):
            result = gaps.routing(self.corpus, hint_function=self.fake_hint(["dag-ulw", "quick"]))
        self.assertEqual(result["findings"], 0)
        self.assertEqual((result["multi_hit_rate"], result["small_fp_rate"]), (1, 0))
        del data["cases"][0]["expect_any"]
        self.corpus.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            gaps.routing(self.corpus, hint_function=self.fake_hint([]))

    def test_public_workflow_small_false_positive(self):
        with patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["quick", "quick"])):
            result = gaps.routing(self.corpus, hint_function=self.fake_hint(["", "ulw-work"]))
        self.assertEqual(result["multi_misses"], 1)
        self.assertEqual(result["small_misses"], 1)
        self.assertEqual(result["results"][0]["classification"], "miss")
        self.assertEqual(result["results"][1]["classification"], "small-false-positive")

    def test_shipped_rule_claimed_and_no_hint(self):
        with patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["dag-ulw", "quick"])):
            result = gaps.routing(self.corpus, hint_function=self.fake_hint(["web-research", ""], "web_research"))
        self.assertEqual(result["shipped_rule_claimed"], 1)
        self.assertEqual(result["results"][0]["classification"], "shipped-rule-claimed")
        self.assertEqual([r["source"] for r in result["results"]], ["shipped-rule", "none"])

    def test_isolated_pack_and_cleanup(self):
        observed = []
        def hints(texts, env, omh, hint_function):
            home = Path(env["OMH_HOME"])
            observed.extend([home, Path(env["HERMES_HOME"])])
            self.assertTrue(home.is_relative_to(Path.home() / ".hermes/cache/scratch"))
            self.assertEqual((home / "routing/trigger-packs/ko.json").read_bytes(), self.corpus.read_bytes())
            self.assertNotEqual(env["HERMES_HOME"], str(Path.home() / ".hermes"))
            return [self.fake_hint(["dag-ulw"])(t) for t in texts], "fake-python"
        with patch.object(gaps, "measure_route_hints", side_effect=hints), patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["wrong", "quick"])) as run:
            gaps.routing(self.corpus, pack=self.corpus)
            self.assertTrue(all(c.kwargs["env"]["OMH_HOME"] == str(observed[0]) for c in run.call_args_list))
        self.assertTrue(all(not p.exists() for p in observed))

    def test_cli_json_report_and_miss_exit(self):
        report = self.root / "reports/out.md"
        hints = ([{"selected_workflow": "wrong"}, {"selected_workflow": "quick"}], "fake-python")
        with patch.object(gaps, "measure_route_hints", return_value=hints), patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["dag-ulw", "quick"])), contextlib.redirect_stdout(io.StringIO()) as output:
            code = gaps.main(["routing", "--corpus", str(self.corpus), "--json", "--report-file", str(report)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["findings"], 1)
        self.assertIn("복합 요청 누락 1건", report.read_text())

    def test_clean_stdout_silenced(self):
        hints = ([{"selected_workflow": "dag-ulw"}, {"selected_workflow": "quick"}], "fake-python")
        with patch.object(gaps, "measure_route_hints", return_value=hints), patch.object(gaps.subprocess, "run", side_effect=self.fake_run(["wrong", "quick"])), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(gaps.main(["routing", "--corpus", str(self.corpus), "--quiet-clean"]), 0)
        self.assertEqual(output.getvalue(), "")

    def test_router_failure_is_error(self):
        with patch.object(gaps, "measure_route_hints", side_effect=RuntimeError("failure")), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(gaps.main(["routing", "--corpus", str(self.corpus)]), 2)

    def test_readonly_sqlite_json_turns_and_actions(self):
        db = self.root / "state.db"
        with sqlite3.connect(db) as conn:
            conn.executescript("CREATE TABLE sessions(id TEXT, title TEXT); CREATE TABLE messages(id INTEGER,session_id TEXT,role TEXT,tool_calls TEXT,timestamp REAL);")
            conn.execute("INSERT INTO sessions VALUES ('one','테스트')")
            def add(index, role="assistant", name=None, args=None, raw=None):
                calls = raw if raw is not None else json.dumps([{"function": {"name": name, "arguments": json.dumps(args)}}]) if name else None
                conn.execute("INSERT INTO messages VALUES (?,?,?,?,?)", (index, "one", role, calls, 100 + index))
            add(1, "user")
            add(2, name="delegate_task", args={"tasks": [{"goal": "a"}]})
            add(3, name="delegate_task", args={"goal": "b"})
            add(4, "user")
            add(5, name="delegate_task", args={"tasks": [{"goal": "c"}, {"goal": "d"}]})
            add(6, name="delegate_task", args={"action": "status", "goal": "ignored"})
            add(7, name="skill_view", args={"name": "dag-ulw"})
            add(8, raw="broken json")
        before = db.read_bytes()
        result = gaps.hermes_history(db, 0)
        self.assertEqual(result["summary"], {"spawns": 3, "tasks": 4, "single_task_spawns": 2, "single_later_turn": 1, "single_later_session": 2, "sessions": 1, "dag_ulw_sessions": 1, "findings": 1})
        self.assertEqual(result["sessions"][0]["user_message_ids"], [1, 4])
        self.assertEqual(db.read_bytes(), before)
        self.assertEqual(gaps.hermes_history(db, 106)["summary"]["spawns"], 0)
        with self.assertRaises(sqlite3.OperationalError):
            gaps.hermes_history(self.root / "missing.db", 0)
        self.assertFalse((self.root / "missing.db").exists())

    def test_claude_batches_and_codex_clear_spawns(self):
        claude = self.root / "claude"
        claude.mkdir()
        rows = [{"timestamp": 200, "uuid": "u", "message": {"role": "user", "content": "요청"}},
                {"timestamp": 201, "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Task"}, {"type": "tool_use", "name": "Agent"}]}}]
        (claude / "session.jsonl").write_text("\n".join(map(json.dumps, rows)))
        result = gaps.external_history(claude, 0, "claude")
        self.assertEqual(result["summary"]["tasks"], 2)
        self.assertEqual(result["summary"]["spawns"], 1)
        self.assertEqual(result["summary"]["single_task_spawns"], 0)
        codex = self.root / "codex"
        codex.mkdir()
        (codex / "session.jsonl").write_text(json.dumps({"timestamp": 200, "type": "response_item", "payload": {"type": "function_call", "name": "spawn_agent"}}))
        self.assertEqual(gaps.external_history(codex, 0, "codex")["summary"]["tasks"], 1)
        self.assertEqual(gaps.external_history(self.root / "empty", 0, "codex")["status"], "not covered")


if __name__ == "__main__":
    unittest.main()
