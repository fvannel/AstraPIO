"""Exact editorial updates must not permit any other source/artifact change."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_check", ROOT / "tools/check_final_release.py")
release_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_check)


class FinalReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        original = json.loads((ROOT / "release/manifest.json").read_text())
        self.manifest = copy.deepcopy(original)
        keep = {
            "reference_files": set(release_check.EDITORIAL_UPDATES) | {"src/pio_single_core.v"},
            "artifacts": {"release/commit_id.json", "release/pdk.json", "release/tt_um_fabien_pio.gds"},
            "vendor_files": {"vendor/ihp-open-pdk/LICENSE"},
        }
        files = {"design_status.json"}
        for section, names in keep.items():
            self.manifest[section] = {n: original[section][n] for n in names}
            files.update(names)
        files.update("release/reference-text/" + n for n in release_check.EDITORIAL_UPDATES)
        for name in files:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.write_manifest()

    def write_manifest(self):
        (self.root / "release/manifest.json").write_text(json.dumps(self.manifest))

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            release_check.check(self.root)

    def replace(self, name, before, after):
        path = self.root / name
        data = path.read_bytes()
        self.assertEqual(data.count(before), 1)
        path.write_bytes(data.replace(before, after, 1))

    def test_exact_documentation_edits_pass(self):
        self.check()

    def test_rtl_change_in_edited_file_is_rejected(self):
        self.replace("src/project.v", b"ena & rst_n", b"ena | rst_n")
        with self.assertRaisesRegex(ValueError, "exact editorial update"):
            self.check()

    def test_driver_declaration_change_is_rejected(self):
        self.replace("firmware/pio_timed.h", b"uint16_t idle_cycles", b"uint32_t idle_cycles")
        with self.assertRaisesRegex(ValueError, "exact editorial update"):
            self.check()

    def test_clock_value_change_is_rejected(self):
        self.replace("info.yaml", b"50000000", b"60000000")
        with self.assertRaisesRegex(ValueError, "exact editorial update"):
            self.check()

    def test_unlisted_comment_change_is_rejected(self):
        with (self.root / "src/pio_spi.v").open("ab") as stream:
            stream.write(b"\n// An additional, unapproved comment\n")
        with self.assertRaisesRegex(ValueError, "exact editorial update"):
            self.check()

    def test_original_copy_tampering_is_rejected(self):
        with (self.root / "release/reference-text/info.yaml").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "frozen release"):
            self.check()

    def test_original_copy_is_required(self):
        (self.root / "release/reference-text/src/project.v").unlink()
        with self.assertRaises(OSError):
            self.check()

    def test_missing_frozen_editorial_entry_is_rejected(self):
        del self.manifest["reference_files"]["info.yaml"]
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, "missing from frozen"):
            self.check()

    def test_other_frozen_source_still_requires_exact_hash(self):
        with (self.root / "src/pio_single_core.v").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "frozen release"):
            self.check()

    def test_gds_still_requires_exact_hash(self):
        with (self.root / "release/tt_um_fabien_pio.gds").open("ab") as stream:
            stream.write(b"\0")
        with self.assertRaisesRegex(ValueError, "frozen release"):
            self.check()

    def test_vendor_still_requires_exact_hash(self):
        with (self.root / "vendor/ihp-open-pdk/LICENSE").open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(ValueError, "frozen release"):
            self.check()

    def test_reference_copy_cannot_escape_repository(self):
        path = self.root / "release/reference-text/info.yaml"
        path.unlink()
        path.symlink_to(ROOT / "release/reference-text/info.yaml")
        with self.assertRaisesRegex(ValueError, "Invalid path"):
            self.check()


if __name__ == "__main__":
    unittest.main()
