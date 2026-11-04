# Wonder Quest Library — source handover

Snapshot: 28 October 2026.

## Contents

- `library/`: home page, stories shelf, story reader, artwork, existing narration assets and narration working files.
- `games/`: games shelf, Bruno's Birthday Adventure, Cyber Detectives and Scam or Safe game files, artwork and sounds.
- Each project includes its tracked `.openai/hosting.json` hosting metadata. These IDs identify the existing hosted projects; do not reuse them for a new unrelated deployment.
- Git history, access tokens, local caches and temporary files are excluded.

The product is one connected Wonder Quest Library experience. Its current source is stored in two hosting projects connected by navigation links. Both are included here.

## Start locally

These are static HTML, CSS and JavaScript websites. No npm install or build is needed for the current version. Use a local HTTP server rather than double-clicking HTML files.

With Python 3 installed, open two terminals from the extracted `WonderQuestLibrary` folder:

Terminal 1:

    python -m http.server 8000 --directory library/dist

Terminal 2:

    python -m http.server 8001 --directory games/dist

Open http://localhost:8000 for the library and http://localhost:8001 for games.

On Windows, `py` can be used instead of `python`.

Navigation between library and games currently uses the published URLs. To keep navigation local, replace these URL prefixes in the HTML/JS source you are testing:

- `https://getsetgo.saniya-ikram.chatgpt.site` -> `http://localhost:8000`
- `https://get-set-go-games.saniya-ikram.chatgpt.site` -> `http://localhost:8001`

Use your final production origins instead when deploying. Keep both local servers running while testing.

## Main editable files

- `library/dist/index.html`: home page.
- `library/dist/stories.html`: stories shelf.
- `library/dist/style.css` and `navigation.css`: library styling and navigation.
- `library/dist/reader/index.html`: reader markup and controls.
- `library/dist/reader/reader.js`: book definitions, image/audio mappings, paging and bookmarks.
- `library/dist/reader/reader.css`: reader styling.
- `library/dist/reader/assets/`: book images and existing page audio.
- `library/narration/`: narration scripts and working records; these are not a guarantee that every recording is installed.
- `games/dist/index.html` and `style.css`: games shelf and styling.
- `games/dist/bruno/`: Bruno's Birthday Adventure.
- `games/dist/cyber-detectives/`: Cyber Detectives.
- `games/dist/scam-or-safe/`: Scam or Safe / Cyber Smart Officers.

The `dist` folders are the current editable, deployed static source, not minified framework build output. The library's separate `reader/` directory and `artwork/` directories contain retained source/working assets; edit the deployed reader under `library/dist/reader/`.

## State included

- Bruno's Let's play button uses forest green.
- Mystery Download portrait page 4 spelling corrected to 'looked'.
- The MP4 full-story audio-player update has been rolled back. There are no new continuous audio players beneath the three stories.
- Existing page-by-page narration is preserved, including Mystery Download, Little AI Helper and Magic Picture.
- Pattern Puzzle and Important Update are not enabled for narration in the restored reader.

## Not implemented

Customer registration/login, parent/kids permissions, five-session enforcement, admin/test accounts and subscription payments have NOT been implemented. The current website is static and has no customer-account database or payment backend. Browser-local bookmarks are not user accounts.

Confirmed requirements for future implementation:

- Overall admin: wonderquest.admin@gmail.com.
- Temporary support contact: wonderquest.admin@gmail.com.
- Test account: getsetgoseries@gmail.com, normal family privileges, subscription-exempt.
- Parents: full website, billing and family settings.
- Kids: stories and games only; protected return to parent access.
- Five simultaneous sessions per family account, enforced server-side.
- Monthly subscription: GBP 6.99; payment provider and email delivery need connecting.
- Admin ChatGPT sign-in must verify an approved admin identity, not grant admin to every ChatGPT user.

No passwords or email-sending credentials are included. The addresses above are requirements, not provisioned accounts. No analytics implementation is included.

## Hosting and provenance

Library: https://getsetgo.saniya-ikram.chatgpt.site
Games: https://get-set-go-games.saniya-ikram.chatgpt.site

Library source commit: 7a009480817e6fb70274ee395ed7fe38a5fedb90
Games source commit: 65efa3e9a76b87b8af15eebdcb0154dbb789465f

For another static host, deploy each `dist` directory and update navigation URLs. The existing host's access restrictions do not transfer automatically to another host. Account and subscription functionality requires a backend before launch.
