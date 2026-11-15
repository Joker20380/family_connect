"""Manual isolated layout gate; session input and screenshots remain private."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18769)
    args = parser.parse_args()
    if args.session_file.stat().st_mode & 0o077:
        raise ValueError('Private session file required')
    session = json.loads(args.session_file.read_text())
    base = f'http://127.0.0.1:{args.port}'
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/snap/bin/chromium', headless=True,
                                             args=['--disable-dev-shm-usage'])
        context = browser.new_context()
        context.add_cookies([dict(name='sessionid', value=session['session'], url=base)])
        page = context.new_page()
        for width in (1440, 390):
            page.set_viewport_size(dict(width=width, height=1000))
            page.goto(base + '/inventory/?city=controlled')
            assert page.locator('body').inner_text().count('Controlled city') == 1
            assert page.locator('input[name=city]').input_value() == 'controlled'
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(args.output / f'list-{width}.png'), full_page=True)
            page.goto(base + '/inventory/' + session['pseudonym'] + '/')
            block = page.locator('#device-technical')
            assert 'Controlled city' in block.inner_text()
            block.locator('summary').click()
            assert 'city_sha256' not in block.inner_text()
            assert block.locator('a[href="https://db-ip.com/"]').count() == 1
            assert page.locator('a[href="/subscriptions/"]').count() > 0
            assert page.locator('a[href="/servers/"]').count() > 0
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            block.screenshot(path=str(args.output / f'card-{width}.png'))
        context.close(); browser.close()
    print(json.dumps(dict(result='PASS', widths=[1440, 390], scope='isolated synthetic layout, not production E2E')))


if __name__ == '__main__':
    main()
