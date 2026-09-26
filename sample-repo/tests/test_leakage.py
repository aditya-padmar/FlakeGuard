"""Tests with state leakage patterns."""
import json
import os
from pathlib import Path


def _get_inventory_path() -> Path:
    state_dir = os.environ.get("FLAKEGUARD_STATE_DIR")
    if state_dir:
        base_dir = Path(state_dir)
    else:
        base_dir = Path(__file__).resolve().parent.parent / ".flakeguard_state"
    return base_dir / "inventory.json"


class TestStateLeakage:
    """Tests exhibiting disk artifact state leakage flakiness."""

    def test_seeds_inventory_row(self):
        """Seeds an inventory row into shared file and leaves state dirty."""
        inv_file = _get_inventory_path()
        inv_file.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        if inv_file.exists():
            try:
                with open(inv_file, "r", encoding="utf-8") as f:
                    rows = json.load(f)
            except Exception:
                rows = []
        rows.append({"sku": "SKU-1", "qty": 1})
        with open(inv_file, "w", encoding="utf-8") as f:
            json.dump(rows, f)
        assert len(rows) == 1

    def test_expects_clean_inventory(self):
        """Expects clean inventory; fails if run after test_seeds_inventory_row."""
        inv_file = _get_inventory_path()
        rows = []
        if inv_file.exists():
            try:
                with open(inv_file, "r", encoding="utf-8") as f:
                    rows = json.load(f)
            except Exception:
                rows = []
        assert len(rows) == 0, (
            f"Suspected cause: state leakage from uncleaned disk artifact. "
            f"Expected 0 leftover rows but found: {rows}"
        )

    def test_inventory_roundtrip_control(self, tmp_path):
        """Stable control test using isolated tmp_path."""
        private_file = tmp_path / "private_inventory.json"
        data = [{"sku": "CTRL-1", "qty": 42}]
        with open(private_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        with open(private_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data
