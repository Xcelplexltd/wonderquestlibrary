
from html import escape


def status_page(title, message, link_text="Sign In",
                link_url="/login", status_code=200):
    safe_title = escape(title)
    safe_message = escape(message)
    safe_link_text = escape(link_text)
    safe_link_url = escape(link_url, quote=True)

    from fastapi.responses import HTMLResponse

    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} - Wonder Quest Library</title>
  <link rel="stylesheet" href="/wq-account.css">
</head>
<body class="wq-page">
  <header class="wq-page-header">
    <a class="wq-brand" href="/home">Wonder Quest Library</a>
    <nav class="wq-page-nav" aria-label="Main navigation">
      <a href="/home">Home</a>
      <a href="/stories.html">Stories</a>
      <a href="/games/">Games</a>
      <a href="/login">Sign In</a>
    </nav>
  </header>
  <main class="wq-main">
    <section class="wq-card">
      <h1>{safe_title}</h1>
      <p>{safe_message}</p>
      <p><a class="wq-button" href="{safe_link_url}">
        {safe_link_text}
      </a></p>
    </section>
  </main>
</body>
</html>""",
        status_code=status_code,
    )
