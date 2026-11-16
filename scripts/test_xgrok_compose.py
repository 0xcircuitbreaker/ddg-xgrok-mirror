#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Daedalus Development Group
"""Offline compose CLI integration and remit/length regression tests."""
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import xgrok_compose as compose
from xgrok_draft import account, account_voice, write


class ComposeTests(unittest.TestCase):
    def test_weights(self):
        self.assertEqual(compose.weighted_length('a' * 257 + 'https://example.com/' + 'b' * 300), 280)
        self.assertEqual(compose.weighted_length('界' * 140), 280)
        self.assertEqual(compose.weighted_length('e\u0301'), 1)
        bad = {'model': 'mock', 'options': [dict(text='界' * 141, rationale='r', pillar='p')] * 3}
        with self.assertRaises(ValueError):
            compose.validate_options(bad)

    def test_cli_mock_and_fences(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp)
            write(path / 'account_config.json', {'handle': 'test', 'expected_handle': 'test',
                  'browser_profile': 'unused', 'content_pillars': ['engineering'],
                  'content_mix_contract': {'engineering': 'all'}})
            (path / 'VOICE_GUIDE.md').write_text('terse engineering')
            remit = dict(persona='test engineer', topics=['engineering'], banned_tactics=['bait'],
                         voice_path='VOICE_GUIDE.md', max_replies_per_day=5, require_approval=True)
            write(path / 'xgrok.json', remit)
            write(path / 'analytics/20261115.json', {'themes': ['retry failures']})
            response = {'model': 'mock', 'options': [dict(text='bounded retry question ' + str(i),
                        rationale='engineering retry theme', pillar='engineering') for i in range(3)]}
            def model(cmd, **kwargs):
                self.assertIn('test engineer', cmd[3])
                self.assertIn('bait', cmd[3])
                self.assertIn('retry failures', cmd[3])
                return SimpleNamespace(returncode=0, stdout=json.dumps(response))
            with patch.object(sys, 'argv', ['xgrok', 'compose', '--handle', 'test', '--account-dir', tmp]), patch.object(compose.subprocess, 'run', side_effect=model):
                runpy.run_path(str(Path(__file__).with_name('xgrok')), run_name='__main__')
            data = json.loads((path / 'reply_targets/xgrok_posts_draft_latest.json').read_text())
            self.assertEqual(len(data['posts']), 3)
            self.assertTrue(all(p['failed'] and not p['approved'] and p['status'] == 'draft' for p in data['posts']))
            self.assertFalse((path / 'queues').exists())
            self.assertIn('test engineer', account_voice(*account('test', path)))
            remit['require_approval'] = False
            write(path / 'xgrok.json', remit)
            with self.assertRaises(ValueError):
                account('test', path)


if __name__ == '__main__':
    unittest.main()
