"""Refine only the Scam or Safe intro card and description.
Run from the Wonder Quest Library project root:
    python refine_scam_or_safe_intro.py

This script does not touch backend/content.py, other games, or gameplay logic.
"""
from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd() / 'games' / 'dist' / 'scam-or-safe'
JS = ROOT / 'adventure.js'
CSS = ROOT / 'adventure.css'
MARKER = '/* WQ: Bruno-style Scam or Safe introduction (2026-11) */'

DESCRIPTION = (
    '<p>Join Peep and Poppy on a cyber-smart adventure! '
    'Look closely at messages and websites, spot the clues, '
    'and discover how to stay safe online.</p>'
)

STYLES = r'''
/* WQ: Bruno-style Scam or Safe introduction (2026-11) */
/* Intro only: preserve gameplay, other screens, and shared navigation. */
.mission.paper {
    width: 100%;
    max-width: 1180px;
    min-height: calc(100svh - 120px);
    margin: 0 auto;
    padding: clamp(22px, 4vw, 52px);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: clamp(22px, 4vw, 55px);
    text-align: left;
    background: #f6edda;
    border-radius: 26px;
}
.mission > img.study {
    flex: 0 0 43%;
    width: 43%;
    max-width: 460px;
    height: auto;
    max-height: 450px;
    object-fit: contain;
    border-radius: 20px;
}
.mission > .mission-copy {
    flex: 1;
    min-width: 0;
    padding: 0;
    text-align: left;
}
.mission-copy > .eyebrow {
    font-size: 11px;
    letter-spacing: .18em;
    color: #405f45;
    margin: 0 0 10px;
}
.mission-copy h1 {
    font-size: clamp(34px, 4.5vw, 54px);
    line-height: 1.08;
    margin: 8px 0 20px;
}
.mission-copy .opening-dialogue {
    max-width: 500px;
    margin: 0 0 20px;
    text-align: left;
}
.mission-copy .opening-dialogue p {
    max-width: 460px;
    font-size: 19px;
    line-height: 1.5;
    margin: 0 0 20px;
}
.mission-copy #start.primary {
    background: #405f45;
    border: 0;
    border-radius: 27px;
    box-shadow: none;
    padding: 13px 25px;
    min-height: 48px;
    font-size: 17px;
}
.mission-copy #start.primary:hover { background: #304a34; }
.mission-copy > .small {
    font-size: 13px;
    margin: 12px 0 0;
    color: #75684f;
}
@media (max-width: 760px) {
    .mission.paper {
        min-height: auto;
        padding: 24px 20px 30px;
        flex-direction: column;
        gap: 14px;
        text-align: center;
    }
    .mission > img.study {
        flex: none;
        width: 100%;
        max-width: 420px;
        max-height: 275px;
    }
    .mission > .mission-copy {
        width: 100%;
        text-align: center;
    }
    .mission-copy h1 { font-size: clamp(30px, 7vw, 40px); }
    .mission-copy .opening-dialogue { margin: 0 auto 18px; text-align: center; }
    .mission-copy .opening-dialogue p {
        font-size: 17px;
        margin: 0 auto 18px;
    }
    .mission-copy > .small { margin: 12px auto 0; }
}
'''

# Ensure the target is exactly the intro dialogue just before its start button.
PATTERN = re.compile(
    r'(<div class="opening-dialogue">)(.*?)(</div>\s*<button class="primary" id="start">)',
    re.DOTALL,
)


def main():
    if not JS.is_file() or not CSS.is_file():
        sys.exit('Cannot find games/dist/scam-or-safe/adventure.js and adventure.css. Run from project root.')
    js_before = JS.read_bytes()
    css_before = CSS.read_bytes()
    try:
        js_text = js_before.decode('utf-8')
        css_text = css_before.decode('utf-8')
    except UnicodeDecodeError:
        sys.exit('File encoding is not UTF-8. No changes made.')

    matches = list(PATTERN.finditer(js_text))
    if len(matches) != 1:
        sys.exit(f'Expected one Scam or Safe introduction dialogue before the start button; found {len(matches)}. No changes made.')
    match = matches[0]
    if 'function mission()' not in js_text[:match.start()] or 'game.reset();startMusic()' not in js_text[match.end():]:
        sys.exit('Unexpected game structure. No changes made; do not replace the game code.')

    updated_js = (
        js_text[:match.start()]
        + match.group(1) + DESCRIPTION + match.group(3)
        + js_text[match.end():]
    )
    updated_css = css_text if MARKER in css_text else css_text.rstrip() + '\n\n' + STYLES.strip() + '\n'

    changed = []
    for path, before, after in ((JS, js_before, updated_js.encode('utf-8')), (CSS, css_before, updated_css.encode('utf-8'))):
        if before == after:
            continue
        backup = path.with_name(path.name + '.before_intro_refinement.bak')
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_bytes(after)
        changed.append(path.name)

    if changed:
        print('Updated:', ', '.join(changed))
        print('Backups created or preserved: *.before_intro_refinement.bak')
    else:
        print('Intro changes already applied. No changes made.')
    print('Only the intro description and CSS layout were adjusted.')
    print('Review /games/scam-or-safe/ on desktop and mobile; other game screens are unchanged.')


if __name__ == '__main__':
    main()
