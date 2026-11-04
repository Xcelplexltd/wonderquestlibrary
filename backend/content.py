
from pathlib import Path
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
)
from sqlalchemy.orm import Session

from backend.auth import get_session_user, has_content_access
from backend.database import get_db

router = APIRouter()

PROJECT = Path(__file__).resolve().parent.parent
LIBRARY = PROJECT / "library" / "dist"
GAMES = PROJECT / "games" / "dist"

PUBLIC_ASSETS = {
    "library-watercolour.webp",
    "stories-whole-book.webp",
    "games-bunny-fixed.png",
}

OLD_GAMES = "https://get-set-go-games.saniya-ikram.chatgpt.site"
OLD_HOME = "https://getsetgo.saniya-ikram.chatgpt.site"


def check_access(request: Request, db: Session):
    token = request.cookies.get("wq_session")
    user = get_session_user(db, token)

    if user is None:
        return RedirectResponse("/login", status_code=303)


    if not has_content_access(user):
        return HTMLResponse(
            """
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport"
                    content="width=device-width, initial-scale=1">
              <title>Membership Required - Wonder Quest Library</title>
              <link rel="stylesheet" href="/wq-account.css">
            </head>
            <body class="wq-page">

              <header class="wq-page-header">
                <a class="wq-brand" href="/home">
                  Wonder Quest Library
                </a>
                <nav class="wq-page-nav">
                  <a href="/home">Home</a>
                  <a href="/stories.html">Stories</a>
                  <a href="/games/">Games</a>
                  <a href="/account">My Account</a>
                </nav>
              </header>

              <main class="wq-main">
                <section class="wq-card">
                  <h1>Membership Required</h1>

                  <p>
                    Your Wonder Quest Library membership
                    is not currently active.
                  </p>

                  <p class="wq-muted">
                    An active membership is needed to
                    enjoy our stories and educational games.
                  </p>

                  <p>
                    You can explore our monthly membership
                    for &pound;6.99.
                  </p>

                  <a class="wq-button" href="/subscribe">
                    View Membership
                  </a>

                  <p>
                    <a href="/account">
                      Back to My Account
                    </a>
                  </p>
                </section>
              </main>

            </body>
            </html>
            """,
            status_code=403,
        )


    return None


def serve_file(root: Path, relative: str):
    root = root.resolve()
    target = (root / relative).resolve()

    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    if target.suffix.lower() == ".html":
        content = target.read_text(encoding="utf-8")

        # Add Peep & Poppy label to Cyber Smart Officers.
        if root == GAMES and relative == "index.html":

            card_start = content.find(
                '<article class="game-card scam-safe">'
            )

            if card_start != -1:
                art_start = content.find(
                    '<a class="art"',
                    card_start,
                )

                if art_start != -1:
                    art_end = content.find("</a>", art_start)

                    if art_end != -1:
                        art_html = content[art_start:art_end]

                        if '<span class="tag">' not in art_html:
                            label = (
                                '<span class="tag">'
                                'PEEP &amp; POPPY'
                                '</span>'
                            )

                            content = (
                                content[:art_end]
                                + label
                                + content[art_end:]
                            )
        # Clean up the Wonder Quest Library homepage heading.
        if root == LIBRARY and relative == "index.html":

            # Keep LIBRARY without decorative symbols.
            content = content.replace(
                '<span class="brand-sub">❧ &nbsp; LIBRARY &nbsp; ❧</span>',
                '<span class="brand-sub">LIBRARY</span>',
            )

        # Remove the corrupted decorative line.
        content = re.sub(
            r'<span class="brand-book"[^>]*>.*?</span>',
            '',
            content,
            count=1,
            flags=re.DOTALL,
        )
        # Add Peep & Poppy badge to Cyber Smart Officers.
        if root == GAMES and relative == "index.html":
            content = content.replace(
                'loading="lazy"></a><div class="card-copy"><p class="category">PEEP &amp; POPPY',
                'loading="lazy"><span class="tag">PEEP &amp; POPPY</span></a><div class="card-copy"><p class="category">PEEP &amp; POPPY',
            )

        if (
            (root == LIBRARY and relative in ("index.html", "stories.html"))
            or (root == GAMES and relative == "index.html")
        ):
            # Remove the old page-specific footer.
            content = re.sub(
                r"<footer\b[^>]*>.*?</footer>",
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            additions = (
                '<link rel="stylesheet" href="/account-nav.css">'
                '<script src="/account-nav.js" defer></script>'
                '<style>'
                '.wq-footer {'
                'margin-top:32px;'
                'padding:28px 16px;'
                'background:#f3eee3;'
                'border-top:1px solid #ded7c7;'
                'text-align:center;'
                'color:#56675d;'
                'box-sizing:border-box;'
                'width:100%;'
                '}'
                '.wq-footer-inner {'
                'max-width:900px;'
                'margin:0 auto;'
                '}'
                '.wq-footer strong {'
                'color:#315c4e;'
                'font-size:18px;'
                '}'
                '.wq-footer p {'
                'margin:10px 0;'
                'line-height:1.6;'
                '}'
                '.wq-footer a {'
                'color:#285f52;'
                'text-decoration:underline;'
                '}'
                '.wq-footer small {'
                'color:#77776b;'
                '}'
                '</style>'
            )

            content = content.replace(
                "</head>",
                additions + "</head>"
            )

            footer = """
            <footer class="wq-footer">
                <div class="wq-footer-inner">
                    <strong>Wonder Quest Library</strong>

                    <p>
                        A little world of stories,
                        games and discovery.
                    </p>

                    <p>
                        Questions or enquiries? Contact us at
                        <a href="mailto:admin@wonderquestlibrary.com">
                            admin@wonderquestlibrary.com
                        </a>
                    </p>

                    <small>
                        &copy; 2026 Wonder Quest Library.
                        All rights reserved.
                    </small>
                </div>
            </footer>
            """

            if 'class="wq-footer"' not in content:
                content = content.replace(
                    "</body>",
                    footer + "</body>"
                )

        content = content.replace(
            OLD_GAMES, "/games/"
        ).replace(
            OLD_HOME + "/stories.html", "/stories.html"
        ).replace(
            OLD_HOME + "/", "/home"
        ).replace(
            "http://127.0.0.1:8001", "/games/"
        ).replace(
            "http://127.0.0.1:8000/stories.html",
            "/stories.html"
        ).replace(
            "http://127.0.0.1:8000/", "/home"
        )

        if root == LIBRARY:
            content = content.replace(
                'href="./"', 'href="/home"'
            )

        return HTMLResponse(
            content,
            headers={"Cache-Control": "no-store"},
        )

    return FileResponse(
        target,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/home")
def public_home():
    return serve_file(LIBRARY, "index.html")


@router.get("/stories.html")
def stories(request: Request, db: Session = Depends(get_db)):
    denied = check_access(request, db)
    if denied is not None:
        return denied
    return serve_file(LIBRARY, "stories.html")


@router.get("/reader")
@router.get("/reader/")
def reader_home(
    request: Request,
    db: Session = Depends(get_db),
):
    denied = check_access(request, db)
    if denied is not None:
        return denied
    return serve_file(LIBRARY, "reader/index.html")


@router.get("/reader/{filepath:path}")
def reader_files(
    filepath: str,
    request: Request,
    db: Session = Depends(get_db),
):
    denied = check_access(request, db)
    if denied is not None:
        return denied
    return serve_file(LIBRARY, f"reader/{filepath}")


@router.get("/games")
@router.get("/games/")
def games_home(
    request: Request,
    db: Session = Depends(get_db),
):
    denied = check_access(request, db)
    if denied is not None:
        return denied
    return serve_file(GAMES, "index.html")


@router.get("/games/{filepath:path}")
def game_files(
    filepath: str,
    request: Request,
    db: Session = Depends(get_db),
):
    denied = check_access(request, db)
    if denied is not None:
        return denied

    candidate = GAMES / filepath

    if candidate.is_dir():
        filepath = filepath.rstrip("/") + "/index.html"

    return serve_file(GAMES, filepath)


@router.get("/assets/{filepath:path}")
def library_assets(
    filepath: str,
    request: Request,
    db: Session = Depends(get_db),
):
    if filepath not in PUBLIC_ASSETS:
        denied = check_access(request, db)
        if denied is not None:
            return denied

    return serve_file(LIBRARY, f"assets/{filepath}")



@router.get("/{filename}")
def library_styles(filename: str):
    allowed = {
        "style.css",
        "navigation.css",
        "account-nav.css",
        "account-nav.js",
        "wq-account.css",
    }

    if filename not in allowed:
        raise HTTPException(status_code=404)

    return serve_file(LIBRARY, filename)

