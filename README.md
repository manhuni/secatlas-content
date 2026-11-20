# The content library of SecAtlas

This repository (`D:\Projects\Personal\Github\secatlas-content`) is the single source of truth for SecAtlas live content.

## How to add, edit, or delete content (No App Build, No Worker Deploy)

1. **Edit an article or block**:
   - Open `content/<article_id>.json` (English) or `content/<article_id>.<lang>.json` (translated edition: `vi`, `ja`, `ko`, `pt_br`, `id`, `th`, `tr`).
   - Every block in the app is **100% data-driven**:
     - `objectives`: Leave `[]` to hide "What you will learn", or add strings to show it.
     - `media.gallery` / `section.gallery`: Leave `[]` to hide image galleries, or add media items (`image`, `video`, `audio`, `link`) to show them.
     - `sections[i].steps`, `table`, `plots`, `equations`, `simulations`, `terms`, `symbols`, `examples`, `calloutKind`: Present only when non-empty in JSON.
     - Set `"hidden": true` inside `"item"` to hide an article from the app without deleting its file.
2. **Add or delete an article**:
   - Create or remove `content/<article_id>.json`.
   - Run `python sync_catalog.py` locally (optional — GitHub Actions also runs `sync_catalog.py` automatically on every `git push`).
3. **Publish**:
   - Run `git add -A && git commit -m "..." && git push`.
   - GitHub Actions automatically syncs `catalog/` and `items/` (if needed) and updates `current.json` to the new commit SHA.
   - The app picks up the new content automatically without rebuilding the Flutter app or deploying any Cloudflare Worker.
