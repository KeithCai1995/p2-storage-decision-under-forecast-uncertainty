from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from storage_decision.study_io import load_study_run


class TestStudyReuse(unittest.TestCase):
    def test_matching_reference_is_read_with_correct_input_hash(self):
        metrics, manifest = load_study_run(ROOT / "corrected_v110/baseline", ROOT, ROOT / "configs/base.yaml", 20260817)
        self.assertEqual(len(metrics), 7)
        self.assertEqual(manifest["test_days"], 83)
        self.assertEqual(manifest["source_sha256"], "6901c84f413ba1375fd8096c3c4910c2346d479a7ff18274832c2d27aba8472b")

    def test_reuse_rejects_other_seed_or_configuration(self):
        reference = ROOT / "corrected_v110/baseline"
        with self.assertRaises(ValueError):
            load_study_run(reference, ROOT, ROOT / "configs/base.yaml", 20260818)
        with self.assertRaises(ValueError):
            load_study_run(reference, ROOT, ROOT / "configs/cvar_weight_070.yaml", 20260817)


if __name__ == "__main__":
    unittest.main()
