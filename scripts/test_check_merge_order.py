#!/usr/bin/env python3
"""Offline tests for the merge-order guard (scripts/check_merge_order.py).

Run as a script (no pytest needed in the offline sandbox):
    python3 scripts/test_check_merge_order.py
or via unittest:
    python3 -m unittest scripts.test_check_merge_order
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_merge_order as g

ARMED = "**Gate status:** **ARMED** — the register is non-empty."
DISARMED = "**Gate status:** **DISARMED** — the register is empty."


class MergeOrderGuard(unittest.TestCase):
    def test_docs_only_while_armed_is_ok(self):
        code, _ = g.evaluate(["governance/RUNBOOK.md"], ARMED)
        self.assertEqual(code, 0)

    def test_deliverable_while_armed_fails(self):
        code, msg = g.evaluate(["infra/state-machine.yaml"], ARMED)
        self.assertEqual(code, 1)
        self.assertIn("ARMED", msg)
        self.assertIn("close-out", msg)

    def test_deliverable_while_disarmed_is_ok(self):
        code, _ = g.evaluate(["infra/state-machine.yaml"], DISARMED)
        self.assertEqual(code, 0)

    def test_deferred_template_is_not_a_deliverable(self):
        code, _ = g.evaluate(["infra/deferred/cloudtrail-org-baseline.yaml"], ARMED)
        self.assertEqual(code, 0)

    def test_offline_checker_is_not_a_deliverable(self):
        code, _ = g.evaluate(["infra/validate_state_machine.py"], ARMED)
        self.assertEqual(code, 0)

    def test_missing_gate_line_is_an_error(self):
        code, _ = g.evaluate(["infra/state-machine.yaml"], "no gate line")
        self.assertEqual(code, 2)

    def test_mixed_change_with_deliverable_while_armed_fails(self):
        code, _ = g.evaluate(
            ["governance/RUNBOOK.md", "infra/state-machine.yaml"], ARMED
        )
        self.assertEqual(code, 1)

    def test_gate_line_parse_is_case_insensitive(self):
        self.assertEqual(g.gate_status("**Gate status:** **armed**"), "ARMED")
        self.assertEqual(g.gate_status("**Gate status:** **DisArmed**"), "DISARMED")
        self.assertIsNone(g.gate_status("no marker"))

    def test_self_test_passes(self):
        self.assertEqual(g._self_test(), 0)


if __name__ == "__main__":
    unittest.main()
