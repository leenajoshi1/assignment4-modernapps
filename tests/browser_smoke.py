"""Run with frontend :3000 and backend :5000. Uses the starter's Longhorn fixture.
Install optional tools: pip install playwright; python -m playwright install chromium
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM_PATH') or None)
    context = browser.new_context(viewport={'width':1440,'height':1050})
    page = context.new_page()
    failures = []
    page.on('pageerror', lambda error: failures.append(str(error)))
    page.goto('http://localhost:3000/admin')
    page.get_by_label('Username', exact=True).fill('admin')
    page.get_by_label('Password', exact=True).fill('wrong')
    page.get_by_role('button', name='Login', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('not found')
    page.get_by_label('Password', exact=True).fill('admin')
    page.get_by_role('button', name='Login', exact=True).click()
    expect(page.locator('#uploadPhotoForm')).to_be_visible()
    response = context.request.post('http://localhost:3000/api/generaluser', data={'gmail':'viewer@gmail.com'})
    assert response.status in (201,409)
    page.locator('#photo_file').set_input_files({'name':'austin-campus.png','mimeType':'image/png','buffer':(ROOT/'public/images/longhorn.png').read_bytes()})
    page.locator('#date_taken').fill('2026-11-10')
    page.locator('#tags').fill('Austin, campus, longhorns')
    page.locator('#comments').fill('A Longhorn afternoon in Austin.\nPhoto shared with the class.')
    page.get_by_role('button', name='Submit', exact=True).click()
    # Supports rerunning against a database that already has the demo fixture.
    expect(page.locator('#available_photos_list img[alt="austin-campus.png"]')).to_be_visible()
    for kind, query in [('Name','austin-campus'),('Tags','longhorns'),('Date','2026-11-10')]:
        page.locator('#search_select').select_option(kind)
        page.locator('#search_input').fill(query)
        page.get_by_role('button', name='Search', exact=True).click()
        expect(page.locator('#available_photos_list img[alt="austin-campus.png"]')).to_be_visible()
    page.locator('#search_input').fill('')
    page.get_by_role('button', name='Search', exact=True).click()
    (ROOT/'screenshots').mkdir(exist_ok=True)
    page.screenshot(path=str(ROOT/'screenshots/01-admin-upload.png'), full_page=True)
    page.locator('#available_photos_list img[alt="austin-campus.png"]').click()
    expect(page.locator('.modal')).to_be_visible()
    expect(page.locator('.modal-body')).to_contain_text('A Longhorn afternoon in Austin.')
    page.screenshot(path=str(ROOT/'screenshots/02-photo-comments.png'), full_page=True)
    page.get_by_role('button', name='Close', exact=True).click()
    page.locator('#dropdownMenu1').click()
    page.get_by_role('link', name='Logout', exact=True).click()
    expect(page).to_have_url('http://localhost:3000/admin')
    page.goto('http://localhost:3000/')
    page.get_by_label('Gmail address').fill('unknown@gmail.com')
    page.get_by_role('button', name='Login', exact=True).click()
    expect(page.get_by_role('alert')).to_contain_text('User not found')
    page.get_by_label('Gmail address').fill('viewer@gmail.com')
    page.get_by_role('button', name='Login', exact=True).click()
    expect(page.locator('#available_photos_list img[alt="austin-campus.png"]')).to_be_visible()
    expect(page.locator('#uploadPhotoForm')).to_have_count(0)
    page.screenshot(path=str(ROOT/'screenshots/03-general-viewer.png'), full_page=True)
    page.reload()
    expect(page.locator('#available_photos_list img[alt="austin-campus.png"]')).to_be_visible()
    page.locator('#dropdownMenu1').click()
    page.get_by_role('link', name='Logout', exact=True).click()
    expect(page).to_have_url('http://localhost:3000/')
    page.goto('http://localhost:3000/photo-portal')
    expect(page).to_have_url('http://localhost:3000/')
    assert not failures, failures
    browser.close()
    print('PASS: both logins, invalid logins, upload, three searches, modal comments, role visibility, refresh, both logout routes, route guard; no browser exceptions.')
