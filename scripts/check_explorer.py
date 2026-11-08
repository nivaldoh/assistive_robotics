"""Optional browser audit: uv run --with playwright python scripts/check_explorer.py.

Requires `uv run --with playwright playwright install chromium` once.
The numerical reproduction and explorer themselves do not need Playwright.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
out = root / 'results/browser-check'
out.mkdir(exist_ok=True)
data = json.loads((root / 'results/figure2/run.json').read_text())
indices = {d['name']: i for i, d in enumerate(data['directions'])}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 1050}, device_scale_factor=1)
    errors, network = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda r: network.append(r.url) if r.url.startswith(('http:', 'https:')) else None)
    page.goto((root / 'results/figure2/explorer.html').as_uri())
    assert page.locator('#lesson-0').is_visible()
    assert not page.locator('#lesson-1').is_visible()
    assert not page.locator('#full-explorer').evaluate('(el) => el.open')
    assert page.locator('#previous').is_disabled()
    page.screenshot(path=str(out / 'desktop.png'), full_page=True)

    for mode, paths in [('head', 1), ('pad', 1), ('both', 2)]:
        page.locator(f'[data-arrows="{mode}"]').click()
        assert page.locator('#intro-physical path[marker-end]').count() == paths
        assert page.locator(f'[data-arrows="{mode}"]').get_attribute('aria-pressed') == 'true'
    # The two displayed arrows have equal projected lengths and opposite directions.
    vectors = page.locator('#intro-physical path[marker-end]').evaluate_all('''els => els.map(el => {
        const numbers = el.getAttribute('d').match(/-?[\\d.]+/g).map(Number);
        return [numbers[2] - numbers[0], numbers[3] - numbers[1]];
    })''')
    assert all(abs(vectors[0][i] + vectors[1][i]) < 1e-8 for i in range(2))

    page.locator('#next').click()
    assert page.locator('#lesson-1').is_visible()
    assert page.locator('#lesson-title').evaluate('(el) => el === document.activeElement')
    for view, caption in [('sagittal', 'nose points right'), ('transverse', 'nose points up'), ('coronal', 'Only the downward part')]:
        page.locator(f'button[data-view="{view}"]').click()
        assert caption in page.locator('#view-caption').inner_text()
        assert view.capitalize() in page.locator('#view-title').inner_text()
        assert page.locator('#plane-diagram polygon').count() == 1
        page.locator('#tour').screenshot(path=str(out / f'view-{view}.png'))

    page.locator('#next').click()
    assert page.locator('#lesson-2').is_visible()
    # All beginner comparisons must show the saved scientific results, including the plateau.
    for example in ['backLow', 'backLowL', 'forehead']:
        page.select_option('#lesson-example', example)
        i = indices[example]
        for condition in range(3):
            page.locator(f'[data-capacity="{condition}"]').click()
            expected = f"{data['conditions'][condition]['tasks'][i]['contact_force_N']:.2f}"
            assert expected in page.locator('#capacity-result').inner_text()
            assert expected in page.locator('#capacity-bars .active').inner_text()
            assert page.locator('#direction').input_value() == str(i)
        if example == 'backLowL':
            assert 'adds no force' in page.locator('#capacity-insight').inner_text()
        if example == 'forehead':
            assert 'leaves this test’s maximum unchanged' in page.locator('#capacity-insight').inner_text()
    page.select_option('#lesson-example', 'backLow')
    page.locator('[data-capacity="1"]').click()
    page.locator('#tour').screenshot(path=str(out / 'capacity.png'))
    page.locator('#next').click()
    assert page.locator('#lesson-3').is_visible()
    assert '236.8 N' in page.locator('#chart-reading').inner_text()
    page.locator('#tour').screenshot(path=str(out / 'chart-guide.png'))
    page.locator('#open-explorer').click()
    assert page.locator('#full-explorer').evaluate('(el) => el.open')
    assert page.locator('#direction').input_value() == str(indices['backLow'])
    page.locator('#physical').screenshot(path=str(out / 'physical.png'))
    page.locator('#plots').screenshot(path=str(out / 'plots.png'))
    page.locator('#activation-details summary').click()
    for i in range(25):
        page.select_option('#direction', str(i))
        assert f"Test {data['directions'][i]['paper_index']}:" in page.locator('#task').inner_text()
        for c in range(3):
            expected = f"{data['conditions'][c]['tasks'][i]['contact_force_N']:.2f}"
            assert expected in page.locator('#values tr').nth(c).inner_text()
            page.select_option('#condition', str(c))
            text = page.locator('#activation-force').inner_text()
            assert f'right DCE {c}×' in text and f'achieved force {expected} N' in text
            assert page.locator('#bars .barrow').count() == 24
    page.select_option('#direction', str(indices['templeAboveR']))
    assert 'not in the original chart subsets' in page.locator('#plot-availability').inner_text()
    # A lateral force has no visible projection in the side view.
    page.select_option('#direction', str(indices['earR']))
    assert 'Push points into / out of this picture' in page.locator('#physical svg').first.text_content()
    page.select_option('#direction', str(indices['backLowL']))
    page.select_option('#condition', '2')
    assert '121.69 N' in page.locator('#activation-force').inner_text()
    page.locator('#activation-details').screenshot(path=str(out / 'activation.png'))
    page.locator('#plots .plot-point[data-index="0"]').last.click()
    assert page.locator('#direction').input_value() == '0'
    for key, index in [('Enter', indices['backLow']), (' ', indices['backHigh'])]:
        page.locator(f'#plots .plot-point[data-index="{index}"]').first.focus()
        page.keyboard.press(key)
        assert page.locator('#direction').input_value() == str(index)
        assert page.evaluate('document.activeElement.classList.contains("plot-point")')

    # The generated report must contain exactly the same data as the saved run.
    assert page.evaluate('DATA') == data
    page.locator('#full-explorer').evaluate('(el) => el.open = false')
    overflow_checks = []
    for width in [390, 320]:
        page.set_viewport_size({'width': width, 'height': 844})
        for n in range(4):
            page.locator(f'[data-step="{n}"]').click()
            overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not overflow, f'Tour step {n + 1} overflows at {width}px'
            assert page.locator('.lesson:visible').count() == 1
            if width == 390:
                page.screenshot(path=str(out / f'mobile-step-{n + 1}.png'), full_page=True)
            overflow_checks.append(f'{width}px / step {n + 1}')
        page.locator('#open-explorer').click()
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        overflow_checks.append(f'{width}px / full explorer')
        page.locator('#full-explorer').evaluate('(el) => el.open = false')
    page.locator('#next').click()
    assert page.locator('#lesson-0').is_visible()
    # Keyboard alone can advance from the first navigation button to the second step.
    page.locator('[data-step="0"]').focus()
    page.keyboard.press('Tab')
    page.keyboard.press('Enter')
    assert page.locator('#lesson-1').is_visible()
    assert not errors, errors
    assert not network, f'Offline report made network requests: {network}'
    report = {'checked_utc': datetime.now(timezone.utc).isoformat(),
              'browser': browser.version, 'origin': 'local file, no HTTP server',
              'guided_steps': 4, 'force_arrow_controls': 'passed: equal and opposite',
              'view_switches': 3, 'beginner_example_condition_combinations': 9,
              'direction_condition_combinations_checked': 75,
              'all_displayed_forces_match_saved_run': True,
              'embedded_data_matches_saved_run': True,
              'activation_rows_per_view': 24, 'point_click': 'passed',
              'point_keyboard_selection_and_focus': 'passed: Enter and Space',
              'tour_keyboard_navigation': 'passed', 'overflow_checks': overflow_checks,
              'javascript_errors': errors, 'http_requests': network,
              'screenshots_directory': 'results/browser-check'}
    (root / 'results/browser_verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    browser.close()
