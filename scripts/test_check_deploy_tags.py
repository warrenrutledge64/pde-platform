#!/usr/bin/env python3
"""Offline tests for the deploy-tag guard (scripts/check_deploy_tags.py, OD-012).

Run as a script (no pytest needed in the offline sandbox):
    python3 scripts/test_check_deploy_tags.py
or via unittest:
    python3 -m unittest scripts.test_check_deploy_tags
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_deploy_tags as g


_CLEAN_DEPLOY = (
    "aws cloudformation deploy \\\n"
    "  --template-file infra/state-machine.yaml \\\n"
    "  --stack-name pdlv-promotion-pipeline-stack \\\n"
    "  --tags Project=PDE Story=2.3 Component=state-machine \\\n"
    "  --no-fail-on-empty-changeset\n"
)


class DeployTagGuardTests(unittest.TestCase):
    def test_clean_deploy_passes(self):
        checks = g.invariants_for_text(_CLEAN_DEPLOY, "x")
        self.assertEqual(len(checks), 1)
        self.assertTrue(all(ok for _, ok in checks))

    def test_missing_tags_fails(self):
        broken = _CLEAN_DEPLOY.replace(
            "  --tags Project=PDE Story=2.3 Component=state-machine \\\n", ""
        )
        checks = g.invariants_for_text(broken, "x")
        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0][1])

    def test_wrong_tag_value_fails(self):
        broken = _CLEAN_DEPLOY.replace("Project=PDE", "Project=ZTIE")
        checks = g.invariants_for_text(broken, "x")
        self.assertFalse(checks[0][1])

    def test_create_stack_key_value_form_passes(self):
        text = (
            "aws cloudformation create-stack \\\n"
            "  --stack-name pdlv-codebuild \\\n"
            "  --tags Key=Project,Value=PDE Key=Story,Value=2.3\n"
        )
        checks = g.invariants_for_text(text, "x")
        self.assertEqual(len(checks), 1)
        self.assertTrue(checks[0][1])

    def test_pde_stack_is_not_policed(self):
        # ZTIE's pde-* stacks are never a PDE deploy target — ignore them.
        text = (
            "aws cloudformation deploy \\\n"
            "  --stack-name pde-ztie-websocket-api \\\n"
            "  --template-file whatever.yaml\n"
        )
        self.assertEqual(g.invariants_for_text(text, "x"), [])

    def test_single_line_deploy_is_detected(self):
        text = (
            "aws cloudformation deploy --stack-name pdlv-x "
            "--template-file t.yaml --tags Project=PDE\n"
        )
        checks = g.invariants_for_text(text, "x")
        self.assertEqual(len(checks), 1)
        self.assertTrue(checks[0][1])

    def test_self_test_passes(self):
        self.assertEqual(g.self_test(), 0)

    def test_live_runbooks_carry_the_tag(self):
        # The committed LIVE-RUNBOOKs must themselves be clean.
        self.assertEqual(g.main([]), 0)


if __name__ == "__main__":
    unittest.main()
