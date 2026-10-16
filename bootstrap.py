#!/usr/bin/env python3
"""Fetch the upstream browser client and connect it to a local PES6 data pack."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

UPSTREAM = "https://pes6.optijuegos.net/"
ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
USER_AGENT = "PES6WebLocalBootstrap/1.0 (local user-initiated setup)"

# Upstream client files are downloaded directly from their publisher at setup
# time, rather than mirrored in this repository.
FILES = [
    "index.html",
    "PES6Recomp.js", "PES6Recomp.wasm.gz", "PES6Recomp.data.gz",
    "css/rooms.css", "css/styles.css",
    "js/ads.js", "js/app.js", "js/bindings.js", "js/commentary-preload.js",
    "js/compat.js", "js/config.js", "js/core.js", "js/data.js", "js/errors.js",
    "js/gamepads.js", "js/netserver.js", "js/news.js", "js/online.js",
    "js/pakdownload.js", "js/range-cache.js", "js/runtime.js", "js/savedata.js",
    "js/saves.js", "js/settings.js", "js/storage.js", "js/touch.js", "js/ui.js",
    "js/rooms/player_name.js", "js/rooms/room_browser.js", "js/rooms/room_link.js",
    "js/runtime/background.js", "js/runtime/debug.js", "js/runtime/downloads.js",
    "js/runtime/loader.js", "js/runtime/module.js", "js/runtime/player.js",
    "js/runtime/renderer.js",
    "assets/background.png", "assets/chat.html", "assets/favicon.png",
    "assets/joystick.png", "assets/logo.png", "assets/logo2.png",
    "assets/pak-commentary.json", "assets/pak-commentary-mariano.json",
]

GAME_ONLY_CSS = r'''html,body{width:100%;height:100%;min-height:100%;margin:0!important;overflow:hidden!important;background:#000!important}body{display:block!important}header,.sidebar,.about,footer,.now-playing,.toolbar{display:none!important}.layout{display:block!important;width:100vw!important;height:100vh!important;height:100dvh!important;margin:0!important;padding:0!important}.player-col{display:block!important;width:100vw!important;height:100vh!important;height:100dvh!important;max-width:none!important;margin:0!important}#stage.player{position:fixed!important;z-index:1;inset:0!important;width:100vw!important;height:100vh!important;height:100dvh!important;max-width:none!important;max-height:none!important;margin:0!important;aspect-ratio:auto!important;border-radius:0!important;box-shadow:none!important}#stage #canvas{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;image-rendering:pixelated}#stage #overlay{z-index:8;opacity:0;pointer-events:none;background:#000!important}#overlay .title,#overlay .subtitle,#overlay .load-line,#overlay .start-choice{display:none!important}#fatalError[hidden]{display:none!important}#overlay.boot-error{display:flex!important;opacity:1;pointer-events:auto;background:rgba(0,0,0,.96)!important;color:#fff}#overlay.boot-error #fatalError,#overlay.boot-error .compat-notice{display:block!important;width:min(760px,90vw);color:#fff;font:15px/1.5 system-ui,sans-serif}#overlay.boot-error #fatalError{padding:16px}#netStatus:not(.error),#pakStatus{display:none!important}#netStatus.error{display:block!important;position:fixed!important;z-index:12;left:50%;bottom:max(12px,env(safe-area-inset-bottom));transform:translateX(-50%);width:min(760px,94vw);padding:12px 16px;border:1px solid #a33;border-radius:8px;background:rgba(65,8,8,.96);color:#fff;font:14px/1.45 system-ui,sans-serif}#touchPad{display:none!important}'''


GAME_ONLY_CSS = GAME_ONLY_CSS.replace(
    "#netStatus:not(.error),#pakStatus{display:none!important}",
    "#netStatus,#pakStatus{display:none!important}",
).replace("#netStatus.error{display:block!important;", "#netStatus.error{display:none!important;")


def request(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=90)


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".download")
    try:
        with request(url) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response, out, length=1024 * 1024)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not apply local patch ({label}); the upstream client changed. No modified site was generated.")
    return text.replace(old, new, 1)


def customize_site() -> None:
    index = SITE / "index.html"
    text = index.read_text(encoding="utf-8")
    old_bootstrap = (
        '<link rel="stylesheet" href="css/rooms.css">\n  <link rel="stylesheet" href="css/game-only.css">\n'
        '  <link rel="stylesheet" href="css/loading-ui.css">\n'
        '  <script>window.PES6_AUTO_START=true;try{localStorage.setItem("pes6.showLoadingNotice","0");'
        'localStorage.setItem("pes6.downloadFullPak","0");localStorage.setItem("pes6.commentary","0");}catch(e){}</script>'
    )
    new_bootstrap = (
        '<link rel="stylesheet" href="css/rooms.css">\n  <link rel="stylesheet" href="css/loading-ui.css">\n'
        '  <script>window.PES6_AUTO_START=true;try{localStorage.setItem("pes6.showLoadingNotice","0");'
        'localStorage.setItem("pes6.downloadFullPak","0");localStorage.setItem("pes6.commentary","0");}catch(e){}</script>'
    )
    if old_bootstrap in text:
        text = text.replace(old_bootstrap, new_bootstrap, 1)
    elif new_bootstrap not in text:
        text = replace_once(text, '<link rel="stylesheet" href="css/rooms.css">',
                            new_bootstrap, "fullscreen page bootstrap")
    game_only_link = '<link rel="stylesheet" href="css/game-only.css">'
    if game_only_link in text:
        first_link = text.find(game_only_link) + len(game_only_link)
        text = text[:first_link] + text[first_link:].replace(game_only_link, "")
    text = replace_once(text, '<div class="compat-notice" id="compatNotice" hidden></div>',
                        '<div class="compat-notice" id="compatNotice" hidden></div>\n          <p id="fatalError" role="alert" hidden></p>',
                        "error notice hook")
    text = replace_once(
        text,
        '<script src="js/runtime/loader.js"></script>',
        '<script src="js/loading-progress.js"></script>\n  <script src="js/runtime/loader.js"></script>',
        "startup progress screen",
    )
    text = replace_once(
        text,
        '<script src="js/data.js"></script>',
        '<script src="js/pak-chunks.js"></script>\n  <script src="js/data.js"></script>',
        "GitHub Pages chunk reader",
    )
    index.write_text(text, encoding="utf-8")

    config = SITE / "js/config.js"
    text = config.read_text(encoding="utf-8")
    if "pak: '/assets/pes6.pak'," in text:
        text = replace_once(text, "pak: '/assets/pes6.pak',", "pak: 'assets/pes6.pak',", "relative local data path")
    elif "pak: 'assets/pes6.pak'," in text:
        pass
    else:
        text = replace_once(text, "pak: 'https://gitlab.com/api/v4/projects/87089186/packages/generic/game/1.0/iamarianotraining.html',",
                            "pak: 'assets/pes6.pak',", "relative local game data")
    text = replace_once(text, "adsClient: 'ca-pub-7626037243619661'", "adsClient: ''", "disable publisher ads")
    config.write_text(text, encoding="utf-8")

    data = SITE / "js/data.js"
    text = data.read_text(encoding="utf-8")
    text = replace_once(text, "function fetchRangeOnce(url, begin, end) {",
                        "var pakMetadataBytesLoaded = 0;\nfunction fetchRangeOnce(url, begin, end) {",
                        "track metadata range progress")
    text = replace_once(
        text,
        "    var total = parseInt((response.headers.get('Content-Range') || '').split('/')[1], 10);\n"
        "    return response.arrayBuffer().then(function (bytes) {\n"
        "      return { bytes: new Uint8Array(bytes), total: total };\n"
        "    });",
        "    var total = parseInt((response.headers.get('Content-Range') || '').split('/')[1], 10);\n"
        "    return response.arrayBuffer().then(function (bytes) {\n"
        "      var payload = new Uint8Array(bytes);\n"
        "      pakMetadataBytesLoaded += payload.byteLength;\n"
        "      if (isFinite(total) && total > 0) {\n"
        "        window.PES6_PAK_TOTAL_BYTES = total;\n"
        "        if (window.PES6_LOADING) {\n"
        "          window.PES6_LOADING.setPakTotal(total);\n"
        "          window.PES6_LOADING.recordPakMetadata(payload.byteLength, total);\n"
        "        }\n"
        "      }\n"
        "      return { bytes: payload, total: total };\n"
        "    });",
        "report PAK metadata progress",
    )
    data.write_text(text, encoding="utf-8")

    downloads = SITE / "js/runtime/downloads.js"
    text = downloads.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "  bytesDelivered = deliveredBytes || 0;\n  PES6.PakDownload.setGameBusy(networkCount > 0 || retryingCount > 0);",
        "  bytesDelivered = deliveredBytes || 0;\n"
        "  if (window.PES6_LOADING) window.PES6_LOADING.updateGameData(\n"
        "    Math.max(bytesReceived, bytesDelivered), window.PES6_PAK_TOTAL_BYTES || 0);\n"
        "  PES6.PakDownload.setGameBusy(networkCount > 0 || retryingCount > 0);",
        "forward Range activity even when notices are disabled",
    )
    text = replace_once(
        text,
        "  noticeEl.textContent = text;\n  noticeEl.classList.toggle('warn', retrying > 0);",
        "  noticeEl.textContent = text;\n  noticeEl.classList.toggle('warn', retrying > 0);\n"
        "  if (window.PES6_LOADING) window.PES6_LOADING.updateGameData(\n"
        "    Math.max(bytesReceived, bytesDelivered), window.PES6_PAK_TOTAL_BYTES || 0);",
        "show PAK range progress",
    )
    text = replace_once(
        text,
        "function showError(text) {\n  failed = true;",
        "function showError(text) {\n  if (window.PES6_LOADING) window.PES6_LOADING.showError(text);\n  failed = true;",
        "show loading-screen errors",
    )
    downloads.write_text(text, encoding="utf-8")

    module = SITE / "js/runtime/module.js"
    text = module.read_text(encoding="utf-8")
    if "Runtime.Player.start('off')" not in text:
        text = replace_once(text,
            "      Runtime.Player.showStartChoice();",
            "      if (window.PES6_AUTO_START) { PES6.Settings.applyLocalBootDefaults(); Runtime.Player.start('off'); }\n"
            "      else Runtime.Player.showStartChoice();",
            "auto-start",
        )
    module.write_text(text, encoding="utf-8")

    settings = SITE / "js/settings.js"
    text = settings.read_text(encoding="utf-8")
    text = replace_once(text, "backend = auto\\nscale = 2", "backend = webgl2\\nscale = 2", "prefer WebGL 2")
    anchor = "Array.prototype.forEach.call(document.querySelectorAll('.save-settings'), function (button) {"
    boot = '''function applyLocalBootDefaults() {
  try { if (localStorage.getItem('pes6.localBootConfigured') === '1') return; } catch (e) {}
  var text = readIni();
  text = setIniValue(text, 'render', 'backend', 'webgl2');
  text = setIniValue(text, 'boot', 'skip_intro', '1');
  text = setIniValue(text, 'boot', 'language', 'en');
  try {
    settingsIniEl.value = text;
    window.Module.FS.writeFile(CONFIG_PATH, text);
    window.Module.FS.syncfs(false, function (err) {
      if (!err) { try { localStorage.setItem('pes6.localBootConfigured', '1'); } catch (e) {} }
    });
  } catch (e) { PES6.Core.pushLine('Could not apply local boot settings: ' + e, true); }
}
'''
    boot_declarations = text.count("function applyLocalBootDefaults() {")
    if boot_declarations > 1 and boot in text:
        text = text.replace(boot, "", 1)
    if "function applyLocalBootDefaults() {" not in text:
        text = replace_once(text, anchor, boot + anchor, "boot configuration writer")
    if "applyLocalBootDefaults: applyLocalBootDefaults" not in text:
        text = replace_once(text, "  save: saveSettings,", "  save: saveSettings,\n  applyLocalBootDefaults: applyLocalBootDefaults,", "expose boot configuration")
    settings.write_text(text, encoding="utf-8")

    core = SITE / "js/core.js"
    text = core.read_text(encoding="utf-8")
    legacy_status = """function setStatus(text) {
  if (/^(Error|No se pudo|Navegador no compatible)/i.test(text)) {
    var fatalEl = document.getElementById('fatalError');
    if (fatalEl) { fatalEl.textContent = text; fatalEl.hidden = false; }
    overlayEl.classList.add('boot-error');
    overlayEl.hidden = false;
  }"""
    native_status = """function setStatus(text) {
  if (/^(Error|No se pudo|Navegador no compatible)/i.test(text)) {
    if (window.PES6_LOADING) window.PES6_LOADING.showError(text);
  }"""
    if legacy_status in text:
        text = text.replace(legacy_status, native_status, 1)
    elif native_status not in text:
        text = replace_once(text, "function setStatus(text) {", native_status,
                            "native browser error dialog")
    core.write_text(text, encoding="utf-8")

    compat = SITE / "js/compat.js"
    text = compat.read_text(encoding="utf-8")
    text = text.replace("    PES6.Core.elements.overlay.classList.add('boot-error');\n", "")
    compat.write_text(text, encoding="utf-8")
    (SITE / "css").mkdir(parents=True, exist_ok=True)
    (SITE / "css/game-only.css").write_text(
        GAME_ONLY_CSS + "\n",
        encoding="utf-8",
    )
    (SITE / "css/loading-ui.css").write_text(
        (ROOT / "loading-ui.css").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (SITE / "js/loading-progress.js").write_text(
        (ROOT / "loading-progress.js").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (SITE / "js/pak-chunks.js").write_text(
        (ROOT / "pak-chunks.js").read_text(encoding="utf-8"), encoding="utf-8"
    )


def validate_pak(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"Local game data not found: {path}")
    if path.stat().st_size < 64:
        raise RuntimeError(f"The local game-data file is too small: {path}")
    with path.open("rb") as stream:
        if stream.read(8) != b"PES6PAK2":
            raise RuntimeError(f"The selected local data file is not a PES6PAK2 package: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare PES6Web using a local PES6 data package.")
    parser.add_argument("--pak", type=Path, default=None,
                        help="Path to your locally obtained PES6 PAK file (or set PES6_PAK_PATH).")
    args = parser.parse_args()
    try:
        SITE.mkdir(parents=True, exist_ok=True)
        for i, rel in enumerate(FILES, 1):
            dest = SITE / rel
            if dest.exists() and dest.stat().st_size:
                print(f"[{i}/{len(FILES)}] already present: {rel}")
                continue
            print(f"[{i}/{len(FILES)}] downloading upstream client file: {rel}")
            download_file(UPSTREAM + rel, dest)
        customize_site()

        target = SITE / "assets/pes6.pak"
        if target.is_file():
            validate_pak(target)
            print(f"Using existing local game data: {target}")
        else:
            source = args.pak or (Path(os.environ["PES6_PAK_PATH"]) if os.environ.get("PES6_PAK_PATH") else None)
            if source is None:
                default = ROOT / "assets/pes6.pak"
                if default.is_file():
                    source = default
            if source is None:
                assembler = ROOT / "assemble_pak.py"
                if not assembler.is_file():
                    raise RuntimeError("No local game data was supplied. Run assemble_pak.py if repository chunks are available, or run: python bootstrap.py --pak /path/to/pes6.pak")
                print("Reassembling local game data from repository chunks...")
                try:
                    subprocess.run([sys.executable, str(assembler)], cwd=ROOT, check=True)
                except subprocess.CalledProcessError as exc:
                    raise RuntimeError("Could not reassemble PES 6 data from the repository chunks.") from exc
                validate_pak(target)
                print(f"Reassembled local game data: {target} ({target.stat().st_size:,} bytes)")
            else:
                source = source.expanduser().resolve()
                validate_pak(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                validate_pak(target)
                print(f"Copied local game data into the ignored build folder: {target} ({target.stat().st_size:,} bytes)")
        print("\nSetup complete. Run START-GAME.cmd (Windows) or ./start-game.sh (Linux/macOS).")
        return 0
    except (OSError, urllib.error.URLError, RuntimeError) as exc:
        print(f"\nSetup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
