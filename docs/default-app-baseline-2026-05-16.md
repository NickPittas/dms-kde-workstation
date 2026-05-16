# Default app baseline

Date: 2026-05-16

## Goal

Make DMS KDE Workstation use KDE/Qt apps for local workstation files while preserving user choices for browser and code editor.

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

The installer should set these defaults only after apps are installed and tested. It should also expose a UI to change:

- browser
- terminal
- file manager
- PDF viewer
- image viewer
- archive manager
- text/code editor
