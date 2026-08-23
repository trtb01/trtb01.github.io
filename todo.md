# trtb01.github.io — TODO & site notes

Last updated: by cptr, after site review + user feedback (see chat).

## Section-by-section CSS link refactor (in progress)
Goal: every linked HTML page should `<link rel="stylesheet" href="/trtb.css">`, removing inline duplicates and keeping only page-specific overrides. Flat layout kept; standard path is `/trtb.css` (absolute, root-relative).

### trtb.css — REWRITTEN to v3.0.0 (Modular) [LOCAL, NOT PUBLISHED]
- Merged: kept xanh `@font-face` (base64 webfont, `--font-main: 'xanh', monospace`) + adopted the newer modular theme (oracle's v2.0.0 as base: `#trtb_header`/`#app_container`/`.trtb_module`/`.trtb_row`/`#trtb_footer`, `border-radius:0`, enforced lowercase) + ported old general content rules adapted to new vars (img/video/iframe borders, blockquote, hr, pre/code, ul/ol, details/summary, form inputs, ::selection).
- **Side effect:** the 6 files already linking trtb.css (trtb1, voidscream, md-view, md2html, goodnews, jpegcomp) now get the new modular theme automatically. Expected minor visual shifts (h1-6 styling, body padding 5%→40px 20px). Need review before publish.

### main (2 files) — DONE
- `trtb1.html`: already links `trtb.css`; inline style is page-specific only. No edit made. (Will inherit new theme — review.)
- `trtb2.html`: **intentional exception** — alternate pastel theme, does NOT link `trtb.css`. User chose option B (keep standalone). Do not link it.

### Old-theme preservation (5 files) — DONE [LOCAL]
- Created `trtb-legacy.css` = byte-identical copy of the pre-rewrite `trtb.css` (verified via `diff git-show-HEAD:trtb.css trtb-legacy.css` → IDENTICAL). Guarantees exact prior appearance.
- Repointed 5 files from `trtb.css` → `/trtb-legacy.css`: trtb1, voidscream, md2html, goodnews, jpegcomp. (voidscream still also links voidscream.css on top — preserved.)
- `md-view.html`: NOT affected by trtb.css rewrite — it embeds its own full inline copy of the old theme and links NO trtb.css. Left untouched. (Future: could be migrated to link trtb.css, but that risks appearance change — defer.)
- Decision: trtb.css = canonical new modular theme; trtb-legacy.css = old theme for the 5 pages not yet migrated. These 5 are candidates for future modular migration (would change appearance, needs user approval per page).

### exps (3 files) — DONE
- `oracle.html`: MIGRATED — inline v2.0.0 theme replaced with `<link rel="stylesheet" href="/trtb.css">`; kept page-specific `.checkbox_container`, `.display_big`, `.display_sub`, `.label`. [LOCAL]
- `roulette.html`: EXCEPTION — standalone game, no trtb.css link. Left alone per user.
- `soda.html`: EXCEPTION — standalone game, no trtb.css link. Left alone per user.

### Publish checklist (NOT YET PUBLISHED)
- Changed files to commit: trtb.css (rewritten), trtb-legacy.css (new), oracle.html, trtb1.html, voidscream.html, md2html.html, goodnews.html, jpegcomp.html.
- **DO NOT commit**: `.gitignore` (untracked, contains `.cptr` — skill says keep `.cptr` out of committed .gitignore; repo intentionally has no committed .gitignore) and `todo.md` (user hasn't decided whether to publish). Stage explicitly rather than `git add -A`, OR add both to `.git/info/exclude`.
- Recommended: `git add trtb.css trtb-legacy.css oracle.html trtb1.html voidscream.html md2html.html goodnews.html jpegcomp.html` then commit+push.

### Next up (after publish approval)
- Migrate remaining new-modular-theme files to link `/trtb.css` instead of inlining: trtb-dap, trtb-dice, trtb-calc, trtb-dream, index.html.
- b64-suite still BLOCKED on b64.html vs b64-comp.html decision.
- encry-suite, tools, trtb-suite, pages sections pending.

### TODO list by section
- [x] main — done (trtb2 excepted)
- [ ] exps — roulette, oracle, soda
- [ ] b64-suite — BLOCKED on b64.html vs b64-comp.html decision (user will pick winner later)
- [ ] encry-suite — encry, encry-html, encry-md, encry-phrasegen
- [ ] tools — hands, game-test, face, jpegcomp, pdf2jpeg
- [ ] trtb-suite — trtb-calc, trtb-dap, trtb-dice, md-view, brthe
- [ ] pages — ace-steam, gllry, voidscream, goodnews

- Repo is the live GitHub Pages site at https://trtb01.github.io/ (deploys from `main`, root `/`).
- `index.html` hub already organizes links into 7 tabs: main, trtb-suite, pages, b64-suite, encry-suite, tools, exps.
- Files are currently flat in repo root; folder layout does NOT yet match the tab taxonomy.
- See `.cptr/skills/trtb-github-pages/SKILL.md` for publish workflow (pull → edit → publish → confirm).

## Decisions made
- **Orphan files stay orphans.** They are personal/internal tools the user keeps public for easy sharing. Do NOT add them to index tabs unless explicitly asked. They are intentionally unlinked.
- **Delete byte-identical duplicates.** → `pdf2jpeg(2)/` is an exact copy of `pdf2jpeg/` and should be removed.
- **b64.html vs b64-comp.html**: both titled "Base64 File Converter & Encrypter". User will decide which wins later. Do NOT merge/delete yet — wait for their call.
- **Goal: `trtb.css` should be linked in every HTML file** (not inlined). Not required now, but keep in mind for future edits. When touching a page, prefer linking `<link rel="stylesheet" href="trtb.css">` (or the assets path once folders exist) over inline `<style>`.
- **`trtbphoto-001.html` (~2 MB)** is a test with inlined base64 images. Should be fixed (extract images to files) but NOT now. Tracked here.

## TODO items

### Immediate / quick
- [ ] **Delete `pdf2jpeg(2)/`** — byte-identical duplicate of `pdf2jpeg/`. Safe to remove.
      Verified via `diff -rq pdf2jpeg pdf2jpeg\(2\)` → no differences.
- [ ] **Write `todo.md`** (this file).

### Pending user input
- [ ] **Resolve `b64.html` vs `b64-comp.html`** — same title, likely old/new pair. Wait for user to pick the keeper, then delete the other and update any links.

### Future / when convenient
- [ ] **Standardize theme CSS:** make every HTML file link `trtb.css` instead of carrying an inline `<style>` copy. Note `index.html` currently inlines the full TRTB theme despite `trtb.css` existing. `voidscream.css` is used by only `voidscream.html`.
- [ ] **Fix `trtbphoto-001.html`**: extract inlined base64 images to real image files so the HTML isn't ~2 MB.
- [ ] **Folder restructure (proposed, awaiting approval):** mirror the existing tab taxonomy into folders — `/main/`, `/trtb-suite/`, `/pages/`, `/b64-suite/`, `/encry-suite/`, `/tools/`, `/exps/`, plus `/assets/` for CSS and `/scripts/` for serve.sh/publish/roulette.py. Caveat: changes all public URLs (breaks old deep links). Orphans stay at root or get their own `/personal/` area per user preference. NOT approved yet — do not execute until user says go.

## Notes / non-actions (do not touch unless asked)
- Orphan files (intentionally unlinked, personal-but-public): `b64-processor.html`, `crypt-001.html`, `encry_steg.html`, `livetext.html`, `md2html.html`, `mnthgen.html`, `pdf2jpeg1.html`, `qrkii.html`, `trtb-dream.html`, `trtbphoto-001.html`, `trtb-reader.html`, `wl-final.html`.
- `pdf2jpeg1.html` (25 KB standalone) vs `pdf2jpeg/index.html` (308 B Vite shell) are two different implementations of the same tool. Not a duplicate — leave both until user decides direction.
- `s.html` is linked from `voidscream.html`, `goodnews.html`, and `index.html` — not actually an orphan (was flagged in review but is referenced).
