from pathlib import Path
import sys
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from bug_predictor_data import (  # noqa: E402
    iter_split_batches,
    iter_xy,
    load_split,
    to_xy,
)


class BugPredictorLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "processed" / "time").mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write_split(self, split, data):
        path = self.root / "processed" / "time" / f"{split}_prepared.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table(data), path)
        return path

    def test_load_and_xy_ignore_metadata_as_features(self):
        self.write_split("train", {
            "row_id": ["train:1", "train:2"],
            "source": ["print('ok')", "raise ValueError()"],
            "file_defective": [0, 1],
            "repo": ["org/demo", "org/demo"],
            "filepath": ["a.py", "b.py"],
        })
        table = load_split("train", root=self.root)
        X, y = to_xy(table)
        self.assertEqual(X, ["print('ok')", "raise ValueError()"])
        self.assertEqual(y, [0, 1])
        self.assertIn("repo", table.column_names)
        self.assertNotIn("repo", X)

    def test_streaming_batches_and_xy(self):
        self.write_split("val", {
            "source": ["a", "b", "c", "d", "e"],
            "file_defective": [0, 1, 0, 1, 0],
        })
        batches = list(iter_split_batches("val", batch_size=2, root=self.root))
        self.assertEqual([batch.num_rows for batch in batches], [2, 2, 1])
        total = sum(len(X) for X, _ in iter_xy("val", batch_size=2, root=self.root))
        self.assertEqual(total, 5)

    def test_test_split_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "train ou val"):
            load_split("test", root=self.root)

    def test_missing_file_is_reported(self):
        with self.assertRaises(FileNotFoundError):
            load_split("train", root=self.root)

    def test_missing_required_column_is_rejected(self):
        self.write_split("train", {"source": ["x"]})
        with self.assertRaisesRegex(ValueError, "file_defective"):
            load_split("train", root=self.root)

    def test_null_source_is_rejected(self):
        self.write_split("train", {
            "source": ["ok", None],
            "file_defective": [0, 1],
        })
        with self.assertRaisesRegex(ValueError, "source.*null"):
            load_split("train", root=self.root)

    def test_null_target_is_rejected(self):
        self.write_split("train", {
            "source": ["ok", "bad"],
            "file_defective": pa.array([0, None], type=pa.int8()),
        })
        with self.assertRaisesRegex(ValueError, "label.*null"):
            load_split("train", root=self.root)

    def test_non_binary_target_is_rejected(self):
        self.write_split("train", {
            "source": ["x"],
            "file_defective": [2],
        })
        with self.assertRaisesRegex(ValueError, "binaire"):
            load_split("train", root=self.root)

    def test_invalid_batch_size_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "batch_size"):
            list(iter_split_batches("train", batch_size=0, root=self.root))


if __name__ == "__main__":
    unittest.main()
