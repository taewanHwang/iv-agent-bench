import json
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.validate_experiments import validate

BASE = Path(__file__).resolve().parents[1]


class ExperimentRegistryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(BASE / 'experiments', self.root / 'experiments')
        self.index = self.root / 'experiments/index.json'
        self.version = json.loads(self.index.read_text())['experiments'][0]['experiment_version']
        self.experiment = self.root / 'experiments' / self.version

    def change(self, path, change):
        obj = json.loads(path.read_text())
        change(obj)
        path.write_text(json.dumps(obj))

    def test_registry_validates_without_private_files(self):
        self.assertFalse((self.root / '.private').exists())
        self.assertGreaterEqual(validate(self.root), 1)

    def test_duplicate_experiment_version_rejected(self):
        self.change(self.index, lambda x: x['experiments'].append(dict(x['experiments'][0])))
        with self.assertRaisesRegex(ValueError, 'Duplicate experiment'):
            validate(self.root)

    def test_aggregate_cost_mismatch_rejected(self):
        self.change(self.experiment / 'results/cost-v1.json', lambda x: x.update(batch_total_reference_cost_usd='0'))
        with self.assertRaisesRegex(ValueError, 'Batch cost mismatch'):
            validate(self.root)

    def test_unknown_required_state_cannot_be_promoted(self):
        self.change(self.experiment / 'results/quality-v1.json', lambda x: x['rows'][0].update(overall_verdict='pass'))
        with self.assertRaisesRegex(ValueError, 'Unknown required state'):
            validate(self.root)

    def test_artifact_cannot_escape_experiment_directory(self):
        self.change(self.experiment / 'experiment.json', lambda x: x['artifacts'].append('../../README.md'))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            validate(self.root)

    def test_quality_model_must_match_run(self):
        self.change(self.experiment / 'results/quality-v1.json', lambda x: x['rows'][0].update(model='wrong-model'))
        with self.assertRaisesRegex(ValueError, 'Quality model mismatch'):
            validate(self.root)


if __name__ == '__main__':
    unittest.main()
