# Default app baseline

Date: 2026-05-16

> Historical note: this document records one machine's tested defaults. It is **not** the current automatic baseline. Default apps are now user-owned choices configured through the app's **Default Apps** page.

## Goal

Document one tested set of workstation defaults without forcing them on every user.

## Applied defaults

| MIME/category | Default |
|---|---|
| Folders | Dolphin |
| PDF | Okular |
| Images | Gwenview |
| Archives | Ark |
| Plain text / code-ish files | Zed |
| HTTP/HTTPS | Zen Browser |

## Specific associations

```text
inode/directory                    org.kde.dolphin.desktop
application/pdf                    okularApplication_pdf.desktop
image/png/jpeg/gif/webp/tiff/svg   org.kde.gwenview.desktop
application/zip/7z/rar/tar/gzip/xz org.kde.ark.desktop
text/plain/text/markdown/json/etc  dev.zed.Zed.desktop
http/https                         app.zen_browser.zen.desktop
```

## Backup/revert

Backup and before/after logs:

```text
notes/default-app-cleanup-20260516-024811/
```

Revert:

```bash
~/dms-kde-workstation/scripts/restore-default-app-cleanup-latest
```

## Installer implication

The installer should **not** force these defaults automatically. It should only expose a UI to change:

- browser
- terminal
- file manager
- PDF viewer
- image viewer
- archive manager
- text/code editor
