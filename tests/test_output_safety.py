from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tomllib
import inspect
import importlib.util
import pandas as pd
from matplotlib.axes import Axes
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.artifacts import prepare_output
from storage_decision.experiment import run


class TestOutputSafety(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="p2_safety_", dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_new_output_and_explicit_overwrite_preserve_unrelated_files(self):
        output = prepare_output(self.root / "local_runs/baseline", self.root)
        keep = output / "unrelated.txt"
        keep.write_text("retain this file", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            prepare_output(output, self.root)
        self.assertEqual(prepare_output(output, self.root, overwrite=True), output)
        self.assertEqual(keep.read_text(encoding="utf-8"), "retain this file")
        with self.assertRaises(ValueError):
            prepare_output(output, self.root, overwrite=True, kind="supplementary")

    def test_unknown_nonempty_output_never_gets_overwrite_permission(self):
        output = self.root / "unknown"
        output.mkdir()
        keep = output / "private.txt"
        keep.write_text("unchanged", encoding="utf-8")
        with self.assertRaises(ValueError):
            prepare_output(output, self.root, overwrite=True)
        self.assertEqual(keep.read_text(encoding="utf-8"), "unchanged")

    def test_root_sources_git_and_reference_outputs_are_protected(self):
        protected = [self.root, self.root.parent, self.root / ".git/objects", self.root / ".GIT/logs",
                     *[self.root / name for name in ("src", "data", "configs", "scripts", "tests", "report", "historical_v102", "outputs", "evidence", ".github")],
                     self.root / "corrected_v110", self.root / "corrected_v110/baseline/tables",
                     self.root / "corrected_v110/multiseed/seed_20260818"]
        for destination in protected:
            for overwrite in (False, True):
                with self.subTest(destination=destination, overwrite=overwrite), self.assertRaises(ValueError):
                    prepare_output(destination, self.root, overwrite)
        safe = self.root / "corrected_v110/supplementary_20261021"
        self.assertEqual(prepare_output(safe, self.root, kind="supplementary"), safe)
        with self.assertRaises(ValueError):
            prepare_output(safe, self.root, overwrite=True, kind="supplementary")

    def test_legacy_local_experiment_can_be_explicitly_overwritten(self):
        output = self.root / "local_runs/legacy"
        output.mkdir(parents=True)
        (output / "run_manifest.json").write_text(json.dumps({"project": "P2_forecast_to_storage"}), encoding="utf-8")
        self.assertEqual(prepare_output(output, self.root, overwrite=True), output)

    def test_run_refuses_nonempty_before_reading_or_solving(self):
        output = prepare_output(self.root / "local_runs/existing", self.root)
        with patch("storage_decision.experiment.optimise_schedule") as solver:
            with self.assertRaises(FileExistsError):
                run(self.root / "missing.yaml", self.root, output)
            solver.assert_not_called()

    def test_plotting_api_minimum_matches_dependency_declarations(self):
        dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
        self.assertIn("matplotlib>=3.9", dependencies)
        self.assertIn("matplotlib>=3.9", (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines())
        self.assertIn("matplotlib==3.10.8", (ROOT / "requirements-lock.txt").read_text(encoding="utf-8").splitlines())
        self.assertIn("tick_labels", inspect.signature(Axes.boxplot).parameters)

    def test_cli_forwards_only_explicit_overwrite_permission(self):
        spec = importlib.util.spec_from_file_location("p2_run_cli_test", ROOT / "scripts/run_experiment.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for flag in ([], ["--overwrite"]):
            result = {"summary": pd.DataFrame(), "output_root": str(self.root / "new")}
            with patch.object(sys, "argv", ["run_experiment.py", "--output-root", str(self.root / "new"), *flag]), patch.object(module, "run", return_value=result) as called, patch("builtins.print"):
                module.main()
                self.assertEqual(called.call_args.kwargs["overwrite"], bool(flag))


if __name__ == "__main__":
    unittest.main()
