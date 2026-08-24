# msg/ — one-off message pages

This folder holds small, self-contained "message" pages. Each one shows a single
short message, styled with the canonical site theme (`trtb.css`).

## How to make a new message page

1. Create a new `.html` file in this folder, e.g. `hello.html`.
2. Copy the template below and change the message text + `<title>`.
3. Preview locally, then publish to the live site (see "Publishing").

### Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>your-title</title>
  <link rel="stylesheet" href="../trtb.css">
  <style>
    #msg {
      position: absolute;
      top: 40%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
  </style>
</head>
<body>
  <p id="msg">your message here,</p>
</body>
</html>
```

### Rules / notes

- **Stylesheet path is `../trtb.css`** (relative) — `trtb.css` lives one folder
  up, in the repo root. Do NOT use `/trtb.css` (absolute) or the message pages
  will break if the site is ever served from a subpath.
- **Positioning:** `#msg` is absolutely positioned at `top: 40%` (40% down from
  the top of the viewport) and horizontally centered via `left: 50%` +
  `transform: translate(-50%, -50%)`.
- **Text is lowercase-enforced.** `trtb.css` applies
  `text-transform: lowercase` globally, so any casing you type renders lowercase.
- **Keep it a single `<p id="msg">`.** Extra content is fine but the pattern is
  intentionally minimal — one centered message.
- **Live URL:** once pushed, each page is reachable at
  `https://trtb01.github.io/msg/<filename>.html`.

## Publishing

From the repo root:

```bash
./publish "add msg page <filename>"
```

or the long form:

```bash
git -C "/home/tori/a1 - websites/trtb-github-com" pull --rebase --autostash origin main
git -C "/home/tori/a1 - websites/trtb-github-com" add -A
git -C "/home/tori/a1 - websites/trtb-github-com" commit -m "add msg page"
git -C "/home/tori/a1 - websites/trtb-github-com" push origin main
```

The page goes live in ~30-60s.

## Existing pages

| file | message |
|---|---|
| `chuds.html` | hi chudtopia, |
