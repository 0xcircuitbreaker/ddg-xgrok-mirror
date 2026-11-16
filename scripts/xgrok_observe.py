#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Daedalus Development Group
"""Read-only X observation worker. Uses the existing Playwright environment."""
import argparse
import asyncio
import contextlib
import importlib.util
import json
from pathlib import Path
import re
import sys

URL = re.compile(r'https://(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/(\d+)')


def checked_url(url):
    if not isinstance(url, str) or not URL.fullmatch(url):
        raise ValueError('Expected a canonical X post URL')
    return url


def count_value(text):
    text = text.strip().replace(',', '')
    if not text:
        return 0
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([KkM]?)', text)
    if not match:
        return None
    return int(float(match[1]) * {'': 1, 'K': 1000, 'k': 1000, 'M': 1000000}[match[2]])


async def observe(request):
    spec = importlib.util.spec_from_file_location('x_backend', Path.home() / 'x-deleter/scripts/x_rebrand_ddg.py')
    backend = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend)
    profile = Path(request['browser_profile']).expanduser()
    if not profile.is_dir():
        raise ValueError('Browser profile does not exist')
    async with backend.async_playwright() as playwright:
        context = await backend.launch_context(playwright, False, profile_dir=profile)
        try:
            page = await context.new_page()
            active = await backend.current_username(page)
            if not active or active.casefold() != request['expected_handle'].lstrip('@').casefold():
                raise ValueError('Active account mismatch; observation aborted')
            async def navigate(url):
                if not await backend.safe_goto(page, url):
                    raise RuntimeError('Navigation failed')
            async def articles():
                result = []
                for article in await page.locator('article[data-testid="tweet"]').all():
                    # Timestamp permalink identifies the outer post, not a quoted post.
                    links = article.locator('a:has(time)')
                    if not await links.count():
                        continue
                    href = await links.first.get_attribute('href')
                    match = re.fullmatch(r'/([A-Za-z0-9_]+)/status/(\d+)', href or '')
                    if not match:
                        continue
                    text = article.locator('[data-testid="tweetText"]').first
                    item = {'url': 'https://x.com' + href, 'author': match[1], 'status_id': match[2],
                            'text': await text.inner_text() if await text.count() else ''}
                    for key, tests in {'replies': ['reply'], 'reposts': ['retweet', 'unretweet'], 'likes': ['like', 'unlike']}.items():
                        control = article.locator(','.join('[data-testid="' + t + '"]' for t in tests)).first
                        item[key] = count_value(await control.inner_text()) if await control.count() else None
                    result.append(item)
                return result
            if request['command'] == 'mentions':
                await navigate('https://x.com/notifications/mentions')
                found = {}
                for _ in range(6):
                    for item in await articles():
                        if re.search(r'@' + re.escape(request['expected_handle'].lstrip('@')) + r'\b', item['text'], re.I):
                            found[item['status_id']] = item
                    await page.mouse.wheel(0, 850)
                    await page.wait_for_timeout(1500)
                return {'candidates': list(found.values()), 'scrolls': 6}
            if request['command'] == 'feedback':
                results = []
                for target in request['items']:
                    checked_url(target['reply_url'])
                    try:
                        await navigate(target['reply_url'])
                        status_id = URL.fullmatch(target['reply_url'])[2]
                        match = next((r for r in await articles() if r['status_id'] == status_id), None)
                        if match is None:
                            raise RuntimeError('Exact reply not visible')
                        results.append(dict(match, id=target.get('id'), reply_url=target['reply_url']))
                    except Exception as exc:
                        results.append({'id': target.get('id'), 'reply_url': target['reply_url'], 'error': str(exc)})
                return {'replies': results}
            # GraphQL legacy parent IDs are used instead of guessing ancestry from
            # nearby articles (which may be siblings, recommendations or quotes).
            tweets = {}
            async def capture(response):
                if '/graphql/' not in response.url:
                    return
                try:
                    data = await response.json()
                    def walk(node):
                        if isinstance(node, dict):
                            legacy = node.get('legacy', {})
                            if node.get('rest_id') and isinstance(legacy, dict) and 'full_text' in legacy:
                                tweets[str(node['rest_id'])] = legacy
                            for value in node.values():
                                walk(value)
                        elif isinstance(node, list):
                            for value in node:
                                walk(value)
                    walk(data)
                except Exception:
                    pass
            page.on('response', capture)
            url = checked_url(request['url'])
            current = URL.fullmatch(url)[2]
            parents, visited = [], set()
            complete = False
            reason = 'depth_limit'
            target = None
            for _ in range(20):
                if current in visited:
                    reason = 'cycle_detected'
                    break
                visited.add(current)
                await navigate(url)
                visible = {r['status_id']: r for r in await articles()}
                if target is None:
                    target = visible.get(current)
                    if not target or not target['text']:
                        raise RuntimeError('Exact target post not visible')
                legacy = tweets.get(current)
                if legacy is None:
                    reason = 'parent_metadata_unavailable'
                    break
                parent = legacy.get('in_reply_to_status_id_str')
                if not parent:
                    complete, reason = True, 'root_reached'
                    break
                parent_item = visible.get(parent)
                author = legacy.get('in_reply_to_screen_name')
                if parent_item is None and author:
                    parent_item = {'status_id': parent, 'author': author, 'url': 'https://x.com/' + author + '/status/' + parent}
                if parent_item is None:
                    reason = 'parent_unavailable'
                    break
                url = checked_url(parent_item['url'])
                await navigate(url)
                exact = next((r for r in await articles() if r['status_id'] == parent), None)
                if not exact:
                    reason = 'parent_unavailable'
                    break
                parents.append(exact)
                current = parent
            return {'target': target, 'conversation_context': list(reversed(parents)), 'context_complete': complete, 'context_stop_reason': reason}
        finally:
            await context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text())
    with contextlib.redirect_stdout(sys.stderr):
        result = asyncio.run(observe(request))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
