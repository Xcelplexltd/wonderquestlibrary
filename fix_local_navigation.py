
from pathlib import Path
from shutil import copy2
from ftfy import fix_encoding

# Existing locally hosted websites
STORIES = "http://127.0.0.1:8000/"
GAMES = "http://127.0.0.1:8001/"

files = {
    "library/dist/index.html": {
        "https://get-set-go-games.saniya-ikram.chatgpt.site": GAMES
    },
    "library/dist/stories.html": {
        "https://get-set-go-games.saniya-ikram.chatgpt.site": GAMES
    },
    "games/dist/index.html": {
        "https://getsetgo.saniya-ikram.chatgpt.site/stories.html": STORIES + "stories.html",
        "https://getsetgo.saniya-ikram.chatgpt.site/": STORIES
    }
}

for filename, replacements in files.items():
    path = Path(filename)
    if not path.exists():
        print(f"NOT FOUND: {filename}")
        continue

    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        copy2(path, backup)

    content = path.read_text(encoding="utf-8")
    content = fix_encoding(content)

    for old, new in replacements.items():
        content = content.replace(old, new)

    path.write_text(content, encoding="utf-8")
    print(f"Updated: {filename}")

print("Local navigation repair completed.")
