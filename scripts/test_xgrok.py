#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Daedalus Development Group
"""Offline contract tests; no browser, model or live-account writes."""
import copy
import importlib.util
import json
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch
import xgrok_draft as d

cli = runpy.run_path(str(Path(__file__).with_name('xgrok')))


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        d.write(self.path / 'account_config.json', {'handle': '0xcircuitbreakr', 'expected_handle': '0xcircuitbreakr', 'browser_profile': '/unused'})
        self.item: dict[str, Any] = dict(id='test', target_url='https://x.com/engineer/status/123', source_post_text='mcp retry boundary', source_status_id='123', source_author='engineer', reply_topic='contextual', target_rationale='test', model='mock', approved_mentions=[], options=[dict(text=t, rationale='test') for t in ['check the retry boundary.', 'record the receipt first.', 'bound the retry count.']])

    def queue(self):
        cli['merge'](self.path, {'handle': '0xcircuitbreakr', 'expected_handle': '0xcircuitbreakr', 'replies': [self.item]}, '0xcircuitbreakr')
        return d.read(cli['queue_path'](self.path))

    def test_merge_and_legacy_fence(self):
        original = {'handle': '0xcircuitbreakr', 'replies': [dict(id='legacy', target_url='https://x.com/other/status/456', reply_text='existing', posted=False)], 'discovery_stats': {'preserved': 1}}
        d.write(cli['queue_path'](self.path), original)
        q = self.queue()
        self.assertEqual(q['replies'][0], original['replies'][0])
        self.assertEqual(q['discovery_stats'], original['discovery_stats'])
        self.assertTrue(q['replies'][1]['failed'])
        spec = importlib.util.spec_from_file_location('legacy', d.ROOT / 'scripts/reply_0xcircuitbreakr.py')
        assert spec is not None and spec.loader is not None
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        self.assertIsNone(legacy.next_unposted({'replies': q['replies'][1:]}))
        with patch('builtins.input', return_value='1'):
            cli['approve'](self.path)
        q = d.read(cli['queue_path'](self.path))
        self.assertEqual(q['replies'][1]['reply_text'], self.item['options'][0]['text'])
        self.assertIsNone(legacy.next_unposted({'replies': q['replies'][1:]}))
        self.queue()
        self.assertEqual(len(d.read(cli['queue_path'](self.path))['replies']), 2)

    def test_legacy_missing_keys(self):
        d.write(cli['queue_path'](self.path), {'handle': '0xcircuitbreakr', 'replies': [{'posted': True}]})
        self.queue()
        self.queue()
        self.assertEqual(len(d.read(cli['queue_path'](self.path))['replies']), 2)

    def test_lock_blocks_other_process(self):
        import fcntl
        import subprocess
        target = cli['queue_path'](self.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target.parent / '.xgrok_lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            command = ['python3', str(Path(__file__).with_name('xgrok')), 'queue', '--handle', '0xcircuitbreakr', '--account-dir', str(self.path), '--input', str(self.path / 'drafts.json')]
            d.write(self.path / 'drafts.json', {'handle': '0xcircuitbreakr', 'expected_handle': '0xcircuitbreakr', 'replies': [self.item]})
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    proc.wait(timeout=0.3)
                self.assertFalse(target.exists())
                fcntl.flock(lock, fcntl.LOCK_UN)
                stdout, stderr = proc.communicate(timeout=10)
                self.assertEqual(proc.returncode, 0, stderr)
                self.assertEqual(len(d.read(target)['replies']), 1)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()

    def test_draft_queue_direct_import(self):
        (self.path / 'VOICE_GUIDE.md').write_text('voice')
        d.write(self.path / 'targets.json', [dict(url=self.item['target_url'], text='source', status_id='123', author='engineer')])
        args = SimpleNamespace(handle='0xcircuitbreakr', account_dir=str(self.path), input=str(self.path / 'targets.json'), output=None, limit=1, allow_mention=[], model=None, queue=True)
        with patch.object(d, 'generate', return_value=copy.deepcopy(self.item)):
            d.run(args)
        self.assertEqual(len(d.read(cli['queue_path'](self.path))['replies']), 1)

    def test_url_policy(self):
        with self.assertRaises(ValueError):
            d.validate_text('https://evil.example', 'https://good.example', [])
        d.validate_text('https://good.example', 'https://good.example', [])

    def test_validation(self):
        d.validate_item(self.item)
        for text in ['x' * 281, '@unapproved hello', 'bad\tcontrol', 'https://example.com']:
            with self.assertRaises(ValueError):
                d.validate_text(text, 'source', [])
        d.validate_text('@approved ok', 'source', ['approved'])
        bad = copy.deepcopy(self.item)
        bad['source_status_id'] = '999'
        with self.assertRaises(ValueError):
            d.validate_item(bad)

    def test_retry_once(self):
        good = json.dumps({'model': 'mock', 'options': self.item['options']})
        with patch.object(d.subprocess, 'run', side_effect=[SimpleNamespace(returncode=0, stdout='not json'), SimpleNamespace(returncode=0, stdout=good)]) as model:
            result = d.generate(dict(url=self.item['target_url'], text='mcp retry boundary', status_id='123', author='engineer'), 'voice', [])
            self.assertEqual(len(result['options']), 3)
            self.assertEqual(model.call_count, 2)
            assert model.call_args_list[0].args
            self.assertIn('ONLY strict JSON', model.call_args_list[0].args[0][3])
        with patch.object(d.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout='{}')) as model:
            with self.assertRaises(ValueError):
                d.generate(dict(url=self.item['target_url'], text='source'), 'voice', [])
            self.assertEqual(model.call_count, 2)

    def test_hash_guard_and_timeout_cleanup(self):
        import subprocess
        self.queue()
        with patch('builtins.input', return_value='1'):
            cli['approve'](self.path)
        target = cli['queue_path'](self.path)
        q = d.read(target)
        valid = copy.deepcopy(q)
        q['replies'][0]['reply_base_hash'] = 'tampered'
        d.write(target, q)
        args = SimpleNamespace(handle='0xcircuitbreakr', expected_handle='0xcircuitbreakr', id='test', yes=True)
        config = {'expected_handle': '0xcircuitbreakr', 'browser_profile': '/unused'}
        with patch.object(d.subprocess, 'run', side_effect=AssertionError('must not launch')):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                cli['post'](self.path, config, args)
        d.write(target, valid)
        with patch.object(d.subprocess, 'run', side_effect=subprocess.TimeoutExpired('withheld', 600)) as backend:
            with self.assertRaises(subprocess.TimeoutExpired):
                cli['post'](self.path, config, args)
            self.assertEqual(backend.call_count, 1)
        self.assertEqual(d.read(target)['replies'][0]['status'], 'posting_verification_required')
        self.assertEqual(list(target.parent.glob('xgrok-*')), [])

    def test_post_guards_and_no_reapproval(self):
        self.queue()
        args = SimpleNamespace(handle='0xcircuitbreakr', expected_handle='wrong', id='test', yes=True)
        config = {'expected_handle': '0xcircuitbreakr', 'browser_profile': '/unused'}
        with patch.object(d.subprocess, 'run', side_effect=AssertionError('must not launch')):
            with self.assertRaises(ValueError):
                cli['post'](self.path, config, args)
            args.expected_handle = '0xcircuitbreakr'
            with self.assertRaises(ValueError):
                cli['post'](self.path, config, args)
            q = d.read(cli['queue_path'](self.path))
            q['replies'][0].update(status='verification_required', approved=True)
            d.write(cli['queue_path'](self.path), q)
            with patch('builtins.input', side_effect=AssertionError('must not reapprove')):
                cli['approve'](self.path)
            self.assertEqual(d.read(cli['queue_path'](self.path))['replies'][0]['status'], 'verification_required')


class TenantTests(Contracts):
    def approved(self):
        self.queue()
        with patch('builtins.input', return_value='1'):
            cli['approve'](self.path)
        return d.read(cli['queue_path'](self.path))

    def test_hmac_tamper_and_rotation(self):
        import hashlib
        q = self.approved()
        item = q['replies'][0]
        self.assertEqual(item['approval_hmac'], cli['approval_signature'](self.path, item))
        key = self.path / '.xgrok_approval_key'
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        args = SimpleNamespace(handle='0xcircuitbreakr', expected_handle='0xcircuitbreakr', id='test', yes=True)
        for field, value in [('approved_at', 'forged'), ('id', 'other'), ('reply_text', 'forged text')]:
            bad = copy.deepcopy(q)
            bad['replies'][0][field] = value
            if field == 'id':
                args.id = value
            if field == 'reply_text':
                bad['replies'][0]['options'][0]['text'] = value
                bad['replies'][0]['reply_base_hash'] = hashlib.sha256(value.encode()).hexdigest()[:12]
            d.write(cli['queue_path'](self.path), bad)
            with self.assertRaisesRegex(ValueError, 'HMAC'):
                cli['post'](self.path, {}, args)
            args.id = 'test'
        d.write(cli['queue_path'](self.path), q)
        key.write_text('ab' * 32)
        with self.assertRaisesRegex(ValueError, 'HMAC'):
            cli['post'](self.path, {}, args)

    def test_signed_post_roundtrip(self):
        self.approved()
        args = SimpleNamespace(handle='0xcircuitbreakr', expected_handle='0xcircuitbreakr', id='test', yes=True)
        def backend(cmd, **kwargs):
            target = Path(cmd[-1])
            payload = d.read(target)
            payload['replies'][0].update(posted=True, posted_at=d.now(), reply_url='https://x.com/0xcircuitbreakr/status/999')
            d.write(target, payload)
            return SimpleNamespace(returncode=0)
        with patch.object(d.subprocess, 'run', side_effect=backend):
            cli['post'](self.path, {}, args)
        item = d.read(cli['queue_path'](self.path))['replies'][0]
        self.assertEqual(item['status'], 'posted')
        self.assertTrue(item['failed'])

    def test_daily_limit(self):
        from datetime import datetime, timezone, timedelta
        q = self.approved()
        remit = dict(persona='test', topics=[], banned_tactics=[], voice_path='VOICE_GUIDE.md', max_replies_per_day=1, require_approval=True)
        d.write(self.path / 'xgrok.json', remit)
        q['replies'].append(dict(id='old', posted=True, posted_at=d.now()))
        d.write(cli['queue_path'](self.path), q)
        args = SimpleNamespace(handle='0xcircuitbreakr', expected_handle='0xcircuitbreakr', id='test', yes=True)
        with patch.object(d.subprocess, 'run', side_effect=AssertionError('must not publish')):
            with self.assertRaisesRegex(ValueError, 'Daily reply limit'):
                cli['post'](self.path, {}, args)
        q['replies'][-1]['posted_at'] = (datetime.now(timezone.utc)-timedelta(hours=25)).isoformat()
        d.write(cli['queue_path'](self.path), q)
        with patch.object(d.subprocess, 'run', side_effect=RuntimeError('backend reached')):
            with self.assertRaisesRegex(RuntimeError, 'backend reached'):
                cli['post'](self.path, {}, args)

    def test_all_isolation(self):
        import sys
        root = self.path / 'root'
        for handle in ('alice', 'bob'):
            path = root / 'accounts' / handle
            d.write(path / 'account_config.json', dict(handle=handle, expected_handle=handle, browser_profile='/unused'))
            d.write(path / 'xgrok.json', dict(persona=handle, topics=[], banned_tactics=[], voice_path='VOICE_GUIDE.md', max_replies_per_day=2, require_approval=True))
            (path / 'VOICE_GUIDE.md').write_text(handle)
            d.write(path / 'reply_targets/ranked_latest.json', [dict(url=self.item['target_url'], text='source', status_id='123', author='engineer')])
        glob = cli['main'].__globals__
        with patch.dict(glob, ROOT=root), patch.object(sys, 'argv', ['xgrok', 'draft', '--all', '--queue']), patch.object(d, 'generate', return_value=copy.deepcopy(self.item)):
            cli['main']()
        for handle in ('alice', 'bob'):
            q = d.read(root / 'accounts' / handle / 'reply_targets/reply_queue_current.json')
            self.assertEqual(q['handle'], handle)
            self.assertIn(handle, q['replies'][0]['id'])
        seen = []
        with patch.dict(glob, ROOT=root, scan=lambda path, config, handle: seen.append((path.name, handle))), patch.object(sys, 'argv', ['xgrok', 'scan', '--all']):
            cli['main']()
        self.assertEqual(seen, [('alice', 'alice'), ('bob', 'bob')])

    def test_lock_isolation(self):
        import fcntl
        import subprocess
        self.queue()
        other = self.path / 'other'
        d.write(other / 'account_config.json', dict(handle='bob', expected_handle='bob', browser_profile='/unused'))
        d.write(other / 'drafts.json', dict(handle='bob', expected_handle='bob', replies=[self.item]))
        with open(self.path / 'reply_targets/.xgrok_lock', 'a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = subprocess.run(['python3', str(Path(__file__).with_name('xgrok')), 'queue', '--handle', 'bob', '--account-dir', str(other), '--input', str(other / 'drafts.json')], capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(d.read(cli['queue_path'](other))['handle'], 'bob')


if __name__ == '__main__':
    unittest.main()
