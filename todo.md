# trtb01.github.io — TODO & site notes

Last updated: by cptr — xanh webfont FIXED + Group C migrations complete; Group B in progress.

## STATUS (current)
- **Canonical theme:** `trtb.css` v3.0.0 (Modular) — LIVE. xanh webfont now works (see fix below).
- **Files on canonical v3.0.0 theme (11):** `oracle.html`, `articles/cptr-pitch.html`, `index.html`, `trtb-calc.html`, `trtb-dice.html`, `trtb-dap.html`, `trtb-dream.html`, `jpegcomp.html`, `trtb1.html`, `md2html.html`, `goodnews.html`.
- **`voidscream.html`** — STANDALONE modernized theme (`voidscream.css` v2.0.0, no trtb dependency). Original backed up as `voidscream.css.bak`. Commit `b343342`.
- **Group B: COMPLETE ✅** — all 5 migrated. `trtb-legacy.css` now has NO consumers (see cleanup note below).
- **Group D & E: CANCELLED by user** — standalone pages left as-is.

## voidscream.css modernization — DONE ✅ (commit b343342, LIVE)
- User chose to make `voidscream.css` a **standalone modernized theme** rather than migrate to `/trtb.css`.
- Original backed up as `voidscream.css.bak` (byte-identical to previous committed version).
- New `voidscream.css` v2.0.0 ports v3 structural features: CSS variables (`--bg/--fg/--accent/--fg-soft/--border-width/--shadow-offset/--pad-inner/--gap/--indent/--font-main/--base-scale/--content-max`), global reset (`box-sizing`, `border-radius:0 !important`, lowercase), `:focus-visible` a11y, `::selection`, `--content-max: 900px` centered reading column for 4K.
- **Preserved voidscream identity:** stark white post borders, hard red offset shadows (`box-shadow: 4px 4px 0 red`), red title bars with black UPPERCASE text + letter-spacing, off-white reading text (`#eeeeee`), hover lift effect, mobile adjustments.
- **Font:** kept `monospace` (terminal/void aesthetic) via `--font-main` variable — NOT xanh. Easy to switch if user wants.
- `voidscream.html` now links ONLY `voidscream.css` (dropped `/trtb-legacy.css`).
- Reversible: `git revert b343342` (restores original voidscream.css + legacy link + removes .bak).

## trtb-legacy.css — ORPHANED (cleanup candidate)
With voidscream migrated, `trtb-legacy.css` has **zero consumers**. It was a byte-identical snapshot of pre-v3 `trtb.css` kept for the 5 Group B pages, all now migrated. Options:
1. Delete it (safe — no links remain).
2. Keep it as a historical reference (harmless, ~48KB).
3. Keep until user confirms all migrated pages look good live, then delete.
Recommend #3 — wait for user sign-off on the Group B migrations, then remove.

## xanh webfont fix — DONE ✅ (commit 5484525, LIVE)
- **Root cause:** the base64 woff2 string in `trtb.css` `@font-face` was **2 characters short** (20938 chars, mod4=2). Base64 must be a multiple of 4; the truncation destroyed the brotli-compressed font payload, so browsers silently fell back to `monospace`.
- **Diagnosis:** `base64 -d` reported "invalid input"; `--ignore-garbage` decoded the header but `fontTools` couldn't brotli-decompress (`brotli.error: BrotliDecompress failed`) — confirming the payload itself was corrupt, not just the padding.
- **Bug origin:** the corruption has been present since the xanh `@font-face` was first introduced (commit `29b1d8c` "rewrite trtb.css to modular v3 (xanh kept)"). It was never valid. The original `trtb.css` (commit `108672e`) had no `@font-face` at all.
- **Fix:** regenerated clean base64 from the verified source `/home/tori/Desktop/moving/web-assets/xanh.woff2` (Xanh Mono, 15704 bytes). New string = 20940 chars, mod4=0, round-trip identical to source, `fontTools` parses OK (family: "Xanh Mono").
- **The font is "Xanh Mono"** (Google Font by yellow-type-foundry, github.com/yellow-type-foundry/xanhmono). Also installed system-wide at `/usr/share/fonts/xanh.ttf`.
- **Backup sources** (all verified valid, byte-identical woff2): `/home/tori/Desktop/moving/web-assets/xanh.woff2`, `.../xanh_b64.txt`.
- Reversible via `git revert 5484525` (would restore broken font → monospace fallback).

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

## CSS linkage audit (post-v3.0.0 trtb.css push)
Compiled by scanning every `.html` for: `<link>` to a `.css` file, inline `<style>` blocks, the TRTB version comment, the layout IDs (`trtb_header`/`app_container`/`trtb_footer`/`trtb_module`), and `@font-face`/`--bg`/`--fg`/`--accent` usage.

Legend: ✅ = on canonical v3.0.0; ⚠️ = stale/frozen; ❌ = standalone (no TRTB link).

### Group A — Links canonical `/trtb.css` (v3.0.0, up to date) ✅
| file | link path |
|---|---|
| `oracle.html` | `/trtb.css` |
| `articles/cptr-pitch.html` | `../trtb.css` (relative) |

These already inherit everything we shipped (4K cap, --gap, focus-visible, dark contract, overflow scroll). No work needed.

### Group B — Links `/trtb-legacy.css` (old theme, intentionally frozen) ⚠️
| file | notes |
|---|---|
| `trtb1.html` | page-specific inline style on top; legacy link |
| `voidscream.html` | also links `voidscream.css` on top |
| `md2html.html` | legacy link |
| `goodnews.html` | legacy link + inline fallback vars |
| `jpegcomp.html` | legacy link + inline slider overrides |

`trtb-legacy.css` is a byte-identical snapshot of pre-v3 `trtb.css`. These 5 look exactly as before. Migrating any of them to `/trtb.css` = visible appearance change (needs per-page approval).

### Group C — Inlines a FULL stale TRTB copy + uses the layout IDs (best migration candidates) ⚠️
| file | inlined version | layout IDs present |
|---|---|---|
| `index.html` | 2.3.0 (Double Line Tabs) | yes (header/app/footer/modules) |
| `trtb-calc.html` | 2.0.0 | yes |
| `trtb-dap.html` | 1.0.1 | yes |
| `trtb-dice.html` | 2.2.0 (Multi-Roll Update) | yes |
| `trtb-dream.html` | 2.0.0 | yes |

These already use the `#trtb_header` / `#app_container` / `.trtb_module` / `#trtb_footer` structure, so the layout contract matches v3.0.0. Migration = delete the inlined theme block, add `<link rel="stylesheet" href="/trtb.css">`, keep only page-specific styles local. Each still needs a visual review (v1.x→v3 may have small shifts, esp. trtb-dap @ 1.0.1).

### Group D — Inlines a TRTB-flavored theme but with OLD variable names (pre-modular) ⚠️
| file | var scheme | notes |
|---|---|---|
| `b64.html` | `--line-thick` / `--page-paddi` / `--min-gap` | "EMBEDDED TRTB.CSS"-style |
| `b64-comp.html` | (own inline, no link) | same vintage as b64.html |
| `b64-imgview.html` | (own inline, 2 style blocks) | b64 family |
| `encry.html` | "EMBEDDED TRTB.CSS", old vars | |
| `encry-html.html` | (own inline, 2 style blocks) | encry family |
| `encry-md.html` | (own inline) | encry family |
| `encry-phrasegen.html` | (own inline) | encry family |
| `gllry.html` | `--line-thick` / `--page-paddi` / `--min-gap` | style id="user-css" |
| `ace-steam.html` | (own inline) | |
| `hands.html` | (own inline) | |
| `game-test.html` | (own inline) | |
| `face.html` | (own inline) | |
| `crypt-001.html` | (own inline) | |
| `encry_steg.html` | (own inline, 2 blocks) | orphan |
| `livetext.html` | (own inline, 2 blocks) | orphan |
| `qrkii.html` | (own inline, 2 blocks) | orphan |
| `pdf2jpeg1.html` | own `:root` (33 var hits) | standalone impl |
| `s.html` | (own inline, 2 blocks) | linked from voidscream/goodnews/index |
| `soda.html` | own `:root` (--bg etc, 12 hits) | standalone game |
| `roulette.html` | (own inline) | standalone game |
| `trtb-reader.html` | `--c-bg` / `--c-text` / `--c-accent` | custom-named TRTB-ish |
| `mnthgen.html` | bare inline (no vars) | minimal |
| `trtbphoto-001.html` | (own inline, ~2MB w/ base64 imgs) | needs image extraction too |
| `wl-final.html` | (own inline) | orphan |
| `trtb2.html` | pastel Nunito theme | INTENTIONAL exception (user chose standalone) |

These do NOT use the modular layout IDs, so linking `trtb.css` would require restructuring their HTML into the `#trtb_header`/`#app_container`/`#trtb_footer` skeleton — i.e. a redesign, not a drop-in. Many are orphans/personal tools the user keeps public (see Notes/non-actions in existing todo). Migrating them is lower priority and higher effort.

### Group E — Special embedded cases
| file | situation |
|---|---|
| `md-view.html` | "EMBEDDED trtb.css (User Provided)" — own `:root` (`--font-size0` etc.), NO layout IDs, NO @font-face. Custom theme, not a clean TRTB drop-in. |
| `brthe.html` | own `:root` + own `@font-face`, NO layout IDs. Standalone vibe-coded page. |

### Summary counts
- Group A (done): 2
- Group B (frozen legacy): 5  ← CURRENT FOCUS
- Group C (easy migrations, inlined v1–v2.3 + layout IDs): 5  ✅ COMPLETE
- Group D (standalone, redesign to migrate): ~24  ❌ CANCELLED by user — leave standalone
- Group E (special): 2  ❌ CANCELLED by user — leave standalone

### Group C — COMPLETE ✅ (all published)
| file | was | commit |
|---|---|---|
| `index.html` | v2.3.0 inline | `05bc944` |
| `trtb-calc.html` | v2.0.0 inline | `b08509c` |
| `trtb-dice.html` | v2.2.0 inline | `b08509c` |
| `trtb-dap.html` | v1.0.1 inline (redesign: header restructure, border vars unified) | `dea001d` |
| `trtb-dream.html` | v2.0.0 inline (fullscreen-app body overrides kept) | `373cb8b` |

All 5 inherited v3.0.0 (xanh font, 4K cap+center, focus-visible, --gap, dark contract, overflow scroll). User reviewed live: "Flawless!!".

## CSS migration — Group B focus (Group C done; D & E cancelled)
Group B = 5 files currently linking `/trtb-legacy.css` (byte-identical pre-v3 theme). Migrating each = visible appearance change (old→v3 theme). **None use the layout IDs** — they get v3's global element styling (lowercase, xanh font, 2px borders, red overline links) but NOT the framed `#app_container` skeleton. Each has page-specific inline styles on top.

### Per-file scope (ordered safest → riskiest)

1. **`jpegcomp.html`** — LOW risk. Inline = range-slider overrides + `.hidden` + `body{text-transform:lowercase}` (redundant in v3). Just change the link. Gets xanh font + 4K centering.
2. **`trtb1.html`** — LOW-MED risk. Inline = spider crawl animation + corner roses + h1 centering (all self-contained decorative). Change link; body padding shifts 5%→40px 20px, gets xanh. It's the "primary info / introduction" page.
3. **`md2html.html`** — MED risk. Inline = custom panel layout (`.control-panel`, `.preview-box`, `.left-column`/`.right-column`) with hardcoded `1px solid red` borders. Uses `#app-container` (HYPHEN — not v3's `#app_container`, so no conflict). v3 global reset applies (lowercase, xanh) on top of its custom layout.
4. **`goodnews.html`** — MED-HIGH risk. Inline references old vars `--line-thick`/`--min-gap` (with a fallback `:root` defining them — so inline rules survive the link swap). BUT `body{font-family:sans-serif; max-width:800px; margin:auto}` fights v3's xanh + flex/center. Needs a body override to keep its 800px prose column; sans-serif vs xanh is a design call.
5. **`voidscream.html`** — HIGHEST risk. Links `voidscream.css` (alternate blog theme) ON TOP of legacy. Swapping legacy→v3 means voidscream.css overrides pile onto v3 instead of old theme — unpredictable. The blog has a deliberate aesthetic; needs careful review, possibly keep as exception.

### Approach options
1. **One at a time, live review per file** (like Group C), starting safest: jpegcomp → trtb1 → md2html → goodnews → voidscream. I push each, you eyeball, we revert/fix before moving on. (Recommended.)
2. **Batch the 2 safest** (jpegcomp + trtb1) in one commit, then pause for review, then continue. Faster if the easy ones are truly safe.
3. **Per-file before/after proposal first** — I describe exactly what each will look like and you approve/deny before I touch anything. Slowest, safest.
4. **Declare voidscream a permanent exception** (like trtb2/soda/roulette) and only migrate the other 4. Avoids the riskiest one.
5. **Something else / hybrid.**

Default recommendation: **#1**, and consider folding in #4 (skip voidscream) if its review gets messy.

## Notes / non-actions (do not touch unless asked)
- Orphan files (intentionally unlinked, personal-but-public): `b64-processor.html`, `crypt-001.html`, `encry_steg.html`, `livetext.html`, `md2html.html`, `mnthgen.html`, `pdf2jpeg1.html`, `qrkii.html`, `trtb-dream.html`, `trtbphoto-001.html`, `trtb-reader.html`, `wl-final.html`.
- `pdf2jpeg1.html` (25 KB standalone) vs `pdf2jpeg/index.html` (308 B Vite shell) are two different implementations of the same tool. Not a duplicate — leave both until user decides direction.
- `s.html` is linked from `voidscream.html`, `goodnews.html`, and `index.html` — not actually an orphan (was flagged in review but is referenced).
