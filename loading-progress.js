/* Simple startup progress overlay for the local fullscreen build. */
(function () {
  'use strict';

  var MB = 1024 * 1024;
  var host = window.location.hostname.toLowerCase();
  var loopback = host === 'localhost' || host === '127.0.0.1' || host === '::1';
  var pakTotal = 0;
  var pakMetadataBytes = 0;
  var failed = false;
  var gameStarted = false;

  var hud = document.createElement('section');
  hud.id = 'loadingHud';
  hud.setAttribute('role', 'status');
  hud.setAttribute('aria-live', 'polite');
  var card = document.createElement('div');
  card.className = 'loading-card';
  var title = document.createElement('h1');
  title.id = 'loadingStage';
  title.textContent = loopback ? 'Loading' : 'Downloading';
  var progress = document.createElement('progress');
  progress.id = 'loadingBar';
  progress.removeAttribute('value');
  var amount = document.createElement('p');
  amount.id = 'loadingAmount';
  amount.textContent = '0.0 MB / —';
  card.appendChild(title);
  card.appendChild(progress);
  card.appendChild(amount);
  hud.appendChild(card);
  document.body.appendChild(hud);

  function mb(value) {
    return Math.max(0, Number(value) || 0) / MB;
  }

  function formatMB(value) {
    return mb(value).toFixed(1) + ' MB';
  }

  function actionFor(url) {
    try {
      var target = new URL(url || '/', window.location.href);
      return loopback && target.origin === window.location.origin ? 'Loading' : 'Downloading';
    } catch (e) {
      return loopback ? 'Loading' : 'Downloading';
    }
  }

  function render(stage, loaded, total) {
    if (failed || gameStarted) return;
    hud.hidden = false;
    hud.classList.remove('is-complete');
    title.textContent = /^downloading\b/i.test(String(stage || '')) ? 'Downloading' : 'Loading';
    var current = Math.max(0, Number(loaded) || 0);
    var max = Math.max(0, Number(total) || 0);
    if (max > 0) {
      progress.max = max;
      progress.value = Math.min(current, max);
      amount.textContent = formatMB(current) + ' / ' + formatMB(max);
    } else {
      progress.max = 1;
      progress.removeAttribute('value');
      amount.textContent = formatMB(current) + ' / —';
    }
  }

  function setPakTotal(total) {
    pakTotal = Math.max(0, Number(total) || 0);
    window.PES6_PAK_TOTAL_BYTES = pakTotal;
  }

  function updateGameData(loaded, total) {
    if (gameStarted || failed) return;
    if (Number(total) > 0) setPakTotal(total);
    var target = (window.PES6 && window.PES6.Core && window.PES6.Core.sources.pak) || '/assets/pes6.pak';
    render(actionFor(target), loaded, pakTotal);
  }

  function recordPakMetadata(bytes, total) {
    pakMetadataBytes += Math.max(0, Number(bytes) || 0);
    if (Number(total) > 0) setPakTotal(total);
    updateGameData(pakMetadataBytes, pakTotal);
  }

  function showError(message) {
    if (failed) return;
    failed = true;
    var text = String(message || 'Unknown error');
    var guidance;
    if (/HTTP\s*404/i.test(text)) {
      guidance = 'PES 6 could not load its local game data (HTTP 404).\n'
        + 'Expected file: site/assets/pes6.pak.\n'
        + 'For the local ZIP, restore it with: python3 bootstrap.py --pak /path/to/pes6.pak.\n'
        + 'From the GitHub repository, run: python3 assemble_pak.py (Windows: py -3 assemble_pak.py).\n'
        + 'For setup help, see https://github.com/Igu2012/pes6web';
    } else if (/webgpu|webgl|gpu|renderer|graphics|context|device|adapter|navegador no compatible/i.test(text)) {
      guidance = 'PES 6 could not initialize browser graphics (WebGPU/WebGL).\n'
        + 'Enable hardware acceleration, update your graphics drivers, and try a current Chrome, Edge, or Firefox browser.\n'
        + 'Test WebGL 2 at https://get.webgl.org/webgl2/\n'
        + 'More help: https://github.com/Igu2012/pes6web';
    } else {
      guidance = 'PES 6 could not start. Check that the local game data exists and that your browser supports WebGL 2.\n'
        + 'More help: https://github.com/Igu2012/pes6web';
    }
    progress.hidden = true;
    hud.hidden = true;
    try { window.alert(guidance); } catch (e) {}
  }

  function formatStatus() {
    if (failed || gameStarted) return;
    var wasmLabel = document.getElementById('wasmLabel');
    var wasmProgress = document.getElementById('wasmProgress');
    var status = document.getElementById('status');
    var dependencyProgress = document.getElementById('progress');
    var core = window.PES6 && window.PES6.Core;
    var sources = core && core.sources ? core.sources : {};

    if (wasmProgress && !wasmProgress.hidden) {
      var wasmURL = sources.wasm || sources.engineScript || '/PES6Recomp.wasm.gz';
      render(actionFor(wasmURL), wasmProgress.value, wasmProgress.max);
      return;
    }

    var statusText = status ? status.textContent.trim() : '';
    var labelText = wasmLabel ? wasmLabel.textContent.trim() : '';
    var text = statusText || labelText;
    var values = text.match(/([\d,.]+)\s*MB(?:\s*\/\s*([\d,.]+)\s*MB)?/i);
    if (values) {
      var loaded = parseFloat(values[1].replace(',', '.')) * MB;
      var total = values[2] ? parseFloat(values[2].replace(',', '.')) * MB : 0;
      var dataPhase = /data|datos|juego/i.test(text);
      var source = dataPhase ? (sources.data || '/') : (sources.wasm || '/');
      render(actionFor(source), loaded, total);
      return;
    }

    if (dependencyProgress && !dependencyProgress.hidden) {
      render('Loading', 0, 0);
      return;
    }

    if (text) {
      var downloading = /download|descarg/i.test(text);
      var action = downloading && !loopback ? 'Downloading' : 'Loading';
      render(action, 0, 0);
    }
  }

  window.PES6_LOADING = {
    setPakTotal: setPakTotal,
    recordPakMetadata: recordPakMetadata,
    updateGameData: updateGameData,
    showError: showError
  };

  window.addEventListener('pes6:game-started', function () {
    if (failed) return;
    gameStarted = true;
    hud.classList.add('is-complete');
    window.setTimeout(function () { hud.hidden = true; }, 450);
  });

  window.setInterval(formatStatus, 120);
  formatStatus();
})();
