"""Small local tool checks; no benchmark, real recording or raw archive writes."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


figures = module('generate_final_figures')
package = module('prepare_submission')


class FigureChecks(unittest.TestCase):
    def setUp(self):
        with (ROOT / figures.CPU_LONG).open(newline='', encoding='utf-8') as source:
            self.rows = list(csv.DictReader(source))

    def load_fixture(self, rows):
        scratch = ROOT / 'work'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            path = Path(directory) / figures.CPU_LONG
            path.parent.mkdir(parents=True)
            with path.open('w', newline='', encoding='utf-8') as output:
                writer = csv.DictWriter(output, fieldnames=self.rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with patch.object(figures, 'ROOT', Path(directory)):
                return figures.load(figures.CPU_LONG)

    def test_original_sources(self):
        for source in figures.SOURCES:
            self.assertTrue(figures.load(source))

    def test_missing_sample(self):
        with self.assertRaisesRegex(ValueError, 'incomplete matrix'):
            self.load_fixture(self.rows[:-1])

    def test_duplicate_repetition(self):
        # CSV configurations are interleaved; find another repetition of the
        # same complete group rather than assuming adjacent rows share a group.
        keys = ('width', 'height', 'generations', 'backend', 'version',
                'threads', 'chunk', 'binding')
        other = next(row for row in self.rows[1:]
                     if all(row.get(key) == self.rows[0].get(key) for key in keys)
                     and row['rep'] != self.rows[0]['rep'])
        self.rows[0]['rep'] = other['rep']
        with self.assertRaisesRegex(ValueError, 'duplicate/missing'):
            self.load_fixture(self.rows)

    def test_nonfinite_time(self):
        self.rows[0]['elapsed_seconds'] = 'nan'
        with self.assertRaisesRegex(ValueError, 'invalid time'):
            self.load_fixture(self.rows)

    def test_mixed_source(self):
        self.rows[0]['commit'] = 'wrong-source'
        with self.assertRaisesRegex(ValueError, 'mixed provenance'):
            self.load_fixture(self.rows)

    def test_state_mismatch(self):
        self.rows[0]['checksum'] = '0'
        with self.assertRaisesRegex(ValueError, 'state mismatch'):
            self.load_fixture(self.rows)

    def test_ambiguous_selection(self):
        with self.assertRaisesRegex(ValueError, 'unique five-sample'):
            figures.select({figures.CPU_LONG: self.rows}, figures.CPU_LONG,
                           4096, 64, 'omp-vector', 16)


class VideoGateChecks(unittest.TestCase):
    # All video/ffprobe objects are mocks, not fabricated media files.
    def check_metadata(self, codec='h264', duration='530', size=70_000_000,
                       container='mov,mp4,m4a,3gp,3g2,mj2', name=None):
        path = MagicMock()
        path.name = name or package.VIDEO_NAME
        path.is_file.return_value = True
        path.stat.return_value = SimpleNamespace(st_size=size)
        metadata = {'streams': [{'codec_type': 'video', 'codec_name': codec}],
                    'format': {'duration': duration, 'format_name': container}}
        process = SimpleNamespace(stdout=json.dumps(metadata))
        with patch.object(package.shutil, 'which', return_value='ffprobe'), \
                patch.object(package.subprocess, 'run', return_value=process):
            return package.video_metadata(path, 'ffprobe')

    def test_mock_valid_metadata(self):
        self.assertEqual(self.check_metadata()['duration_seconds'], 530)

    def test_filename(self):
        with self.assertRaisesRegex(ValueError, 'named'):
            self.check_metadata(name='wrong.mp4')

    def test_codec(self):
        with self.assertRaisesRegex(ValueError, 'H.264'):
            self.check_metadata(codec='hevc')

    def test_duration(self):
        for duration in ['600', '601', 'nan', '0']:
            with self.assertRaisesRegex(ValueError, '600 seconds'):
                self.check_metadata(duration=duration)

    def test_size(self):
        for size in [0, 100_000_000]:
            with self.assertRaisesRegex(ValueError, '100 MB'):
                self.check_metadata(size=size)

    def test_container(self):
        with self.assertRaisesRegex(ValueError, 'MP4'):
            self.check_metadata(container='matroska,webm')


if __name__ == '__main__':
    unittest.main()
