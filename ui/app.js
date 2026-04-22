// Markdown Converter — UI logic
// Talks to Python via window.pywebview.api.*

const state = {
  items: [], // { id, path, name, status, error, output, outDir, staged }
  outputMode: "sibling",
  outputPath: "—",
  converting: false,
  font: "editorial",
  size: "normal",
  color: "plum",
  lang: "auto",
};

const $ = (id) => document.getElementById(id);
let nextId = 1;

// ---------- Ready ----------
window.addEventListener("pywebviewready", async () => {
  const cfg = await api("get_config");
  if (cfg) {
    state.outputMode = cfg.output_mode || "sibling";
    state.font = cfg.font || state.font;
    state.size = cfg.size || state.size;
    state.color = cfg.color || state.color;
    state.lang = cfg.lang || state.lang;
    $("output-mode").value = state.outputMode;
    updateOutputPath();
  }
  const presets = await api("list_presets");
  if (presets) populateStyleControls(presets);

  // Files passed via Finder drop onto the .app icon
  const initial = await api("get_initial_files");
  if (initial && initial.length) {
    await addPaths(initial);
  }
});

// Fallback — if running outside pywebview (dev preview)
if (!window.pywebview) {
  setTimeout(() => {
    $("output-path").textContent = "~/Desktop/Converted/  (预览模式)";
    // stub presets so the UI still renders
    populateStyleControls({
      fonts: [
        { id: "editorial", label: "编辑感 · Cormorant + 宋体" },
        { id: "modern", label: "现代 · Inter + 苹方" },
        { id: "academic", label: "学术 · Times + 宋体" },
        { id: "minimal", label: "极简 · Helvetica + 苹方" },
      ],
      sizes: [
        { id: "compact", label: "紧凑 · 10.5pt" },
        { id: "normal", label: "标准 · 11pt" },
        { id: "large", label: "较大 · 12pt" },
        { id: "xlarge", label: "很大 · 13pt" },
      ],
      colors: [
        { id: "plum", label: "梅子 × 鼠尾草", swatch: "#6B5876", accent: "#B8A4C9" },
        { id: "ink", label: "墨色 · 极简黑白", swatch: "#1A1A1A", accent: "#333333" },
        { id: "sage", label: "鼠尾草 × 米色", swatch: "#3D5A4A", accent: "#95A89C" },
        { id: "ocean", label: "靛蓝 × 砂金", swatch: "#1F3A5F", accent: "#4A6A8C" },
        { id: "terracotta", label: "陶土 × 橄榄", swatch: "#A34A2E", accent: "#C47A5E" },
      ],
      langs: [
        { id: "auto", label: "自动" },
        { id: "zh", label: "中文为主" },
        { id: "en", label: "英文为主" },
      ],
    });
  }, 50);
}

function populateStyleControls(p) {
  const fs = $("font-select");
  fs.innerHTML = "";
  for (const f of p.fonts) {
    const o = document.createElement("option");
    o.value = f.id; o.textContent = f.label;
    fs.appendChild(o);
  }
  fs.value = state.font;
  fs.addEventListener("change", onStyleChange);

  const ss = $("size-select");
  ss.innerHTML = "";
  for (const s of p.sizes) {
    const o = document.createElement("option");
    o.value = s.id; o.textContent = s.label;
    ss.appendChild(o);
  }
  ss.value = state.size;
  ss.addEventListener("change", onStyleChange);

  const ls = $("lang-select");
  ls.innerHTML = "";
  for (const l of (p.langs || [])) {
    const o = document.createElement("option");
    o.value = l.id; o.textContent = l.label;
    ls.appendChild(o);
  }
  ls.value = state.lang;
  ls.addEventListener("change", onStyleChange);

  const sw = $("color-swatches");
  sw.innerHTML = "";
  // ensure preview reflects loaded config on first paint
  setTimeout(applyPreview, 0);
  for (const c of p.colors) {
    const b = document.createElement("button");
    b.className = "swatch" + (c.id === state.color ? " active" : "");
    b.dataset.id = c.id;
    b.title = c.label;
    b.style.background = `linear-gradient(135deg, ${c.swatch} 0 55%, ${c.accent} 55% 100%)`;
    b.addEventListener("click", () => {
      state.color = c.id;
      sw.querySelectorAll(".swatch").forEach(x => x.classList.toggle("active", x.dataset.id === c.id));
      onStyleChange();
      applyPreview();
    });
    sw.appendChild(b);
  }
}

async function onStyleChange() {
  state.font = $("font-select").value;
  state.size = $("size-select").value;
  state.lang = $("lang-select").value;
  await api("set_style", state.font, state.size, state.color, state.lang);
  applyPreview();
}

// ---------- Live preview ----------
const FONT_DATA = {
  editorial: {
    display_latin: '"Cormorant Garamond", Georgia, serif',
    display_cjk:   '"Source Han Serif SC", "Songti SC"',
    body_latin:    '"Cormorant Garamond", Georgia, serif',
    body_cjk:      '"Source Han Serif SC", "Songti SC"',
    mono_latin:    '"JetBrains Mono", Menlo, monospace',
    mono_cjk:      '"Source Han Serif SC", "Songti SC"',
  },
  modern: {
    display_latin: '"Inter", sans-serif',
    display_cjk:   '"PingFang SC", "Hiragino Sans GB"',
    body_latin:    '"Inter", -apple-system, sans-serif',
    body_cjk:      '"PingFang SC", "Hiragino Sans GB"',
    mono_latin:    '"JetBrains Mono", Menlo, monospace',
    mono_cjk:      '"PingFang SC"',
  },
  academic: {
    display_latin: '"Times New Roman", serif',
    display_cjk:   '"Songti SC", "SimSun"',
    body_latin:    '"Times New Roman", serif',
    body_cjk:      '"Songti SC", "SimSun"',
    mono_latin:    '"Courier New", Menlo, monospace',
    mono_cjk:      '"Songti SC"',
  },
  minimal: {
    display_latin: '"Helvetica Neue", sans-serif',
    display_cjk:   '"PingFang SC"',
    body_latin:    '"Helvetica Neue", sans-serif',
    body_cjk:      '"PingFang SC"',
    mono_latin:    '"Menlo", monospace',
    mono_cjk:      '"PingFang SC"',
  },
};
const SIZE_PT = { compact: 10.5, normal: 11, large: 12, xlarge: 13 };
const COLOR_DATA = {
  plum:       { heading: "#6B5876", accent: "#B8A4C9", accent_dark: "#4E3F5A", rule: "#95A89C", muted: "#4E3F5A", code_bg: "#F7F2E9" },
  ink:        { heading: "#1A1A1A", accent: "#333333", accent_dark: "#000000", rule: "#CCCCCC", muted: "#555555", code_bg: "#F4F4F4" },
  sage:       { heading: "#3D5A4A", accent: "#95A89C", accent_dark: "#2E4438", rule: "#B8C6BB", muted: "#4E6155", code_bg: "#F1EFE4" },
  ocean:      { heading: "#1F3A5F", accent: "#4A6A8C", accent_dark: "#122645", rule: "#C8B57A", muted: "#3C4F6B", code_bg: "#F3F1EA" },
  terracotta: { heading: "#A34A2E", accent: "#C47A5E", accent_dark: "#6E2E1A", rule: "#8E9A5F", muted: "#6A4A3A", code_bg: "#F6EEE3" },
};

function detectLangFromSample() {
  // sample text contains both CJK and Latin; detect uses sample itself
  const sample = "暮色与长廊 Twilight Passage 雨后的砖缝里渗出青草气息 the quiet hour before dusk";
  const cjk = (sample.match(/[\u4E00-\u9FFF\u3400-\u4DBF]/g) || []).length;
  return cjk / sample.replace(/\s+/g, "").length >= 0.05 ? "zh" : "en";
}

function composeStack(latin, cjk, primary) {
  if (!cjk) return latin;
  if (!latin) return cjk;
  return primary === "zh" ? `${cjk}, ${latin}` : `${latin}, ${cjk}`;
}

function applyPreview() {
  const card = $("preview-card");
  if (!card) return;
  const f = FONT_DATA[state.font] || FONT_DATA.editorial;
  const c = COLOR_DATA[state.color] || COLOR_DATA.plum;
  const size = SIZE_PT[state.size] || 11;
  const primary = state.lang === "auto" ? detectLangFromSample() : state.lang;

  const bodyStack = composeStack(f.body_latin, f.body_cjk, primary);
  const displayStack = composeStack(f.display_latin, f.display_cjk, primary);
  const monoStack = composeStack(f.mono_latin, f.mono_cjk, primary);

  card.style.setProperty("--pv-body", bodyStack);
  card.style.setProperty("--pv-display", displayStack);
  card.style.setProperty("--pv-mono", monoStack);
  card.style.setProperty("--pv-size", size + "pt");
  card.style.setProperty("--pv-heading", c.heading);
  card.style.setProperty("--pv-accent", c.accent);
  card.style.setProperty("--pv-accent-dark", c.accent_dark);
  card.style.setProperty("--pv-rule", c.rule);
  card.style.setProperty("--pv-muted", c.muted);
  card.style.setProperty("--pv-code-bg", c.code_bg);
}

async function api(method, ...args) {
  if (!window.pywebview || !window.pywebview.api) return null;
  try {
    return await window.pywebview.api[method](...args);
  } catch (e) {
    console.error("api error", method, e);
    return null;
  }
}

// ---------- Drag & drop ----------
const dz = $("dropzone");

["dragenter", "dragover"].forEach(ev => {
  dz.addEventListener(ev, (e) => {
    e.preventDefault();
    dz.classList.add("drag-over");
  });
});
["dragleave", "drop"].forEach(ev => {
  dz.addEventListener(ev, (e) => {
    e.preventDefault();
    if (ev === "dragleave" && e.target !== dz) return;
    dz.classList.remove("drag-over");
  });
});

dz.addEventListener("drop", async (e) => {
  e.preventDefault();
  dz.classList.remove("drag-over");

  const files = Array.from(e.dataTransfer.files || []);
  if (!files.length) return;

  // Try native path first (Electron / some pywebview backends)
  const realPaths = [];
  const needStaging = [];
  for (const f of files) {
    const p = f.pywebviewFullPath || f.path;
    if (p) realPaths.push(p);
    else needStaging.push(f);
  }
  if (realPaths.length) await addPaths(realPaths);

  // Stage the rest by reading contents and sending to Python
  if (needStaging.length) {
    setSummary(`读取 ${needStaging.length} 个文件…`);
    const staged = [];
    for (const f of needStaging) {
      if (!/\.(md|markdown)$/i.test(f.name)) continue;
      try {
        const b64 = await fileToBase64(f);
        const p = await api("stage_dropped", f.name, b64);
        if (p) staged.push(p);
      } catch (err) {
        console.error("staging failed for", f.name, err);
      }
    }
    if (staged.length) {
      await addPaths(staged);
      setSummary("");
    } else {
      flashSummary("读取拖入文件失败", "error");
    }
  }
});

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      // reader.result is "data:...;base64,<payload>"
      const s = reader.result;
      const i = s.indexOf(",");
      resolve(i >= 0 ? s.slice(i + 1) : s);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

// Click dropzone → native picker
dz.addEventListener("click", async (e) => {
  if (e.target.closest(".paste-row")) return;
  if (e.target.tagName === "BUTTON" && e.target.id !== "pick-btn") return;
  const picked = await api("pick_files");
  if (picked && picked.length) await addPaths(picked);
});

// Paste path
$("paste-add").addEventListener("click", async () => {
  const val = $("paste-input").value.trim();
  if (!val) return;
  const resolved = await api("resolve_paths", val);
  if (resolved && resolved.length) {
    await addPaths(resolved);
    $("paste-input").value = "";
  } else {
    flashSummary("找不到匹配的 .md 文件", "error");
  }
});
$("paste-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("paste-add").click();
});

// ---------- Queue ----------
async function addPaths(paths, opts = {}) {
  const mdPaths = await api("filter_md", paths) || paths;
  const stagedFlag = !!opts.staged;
  for (const p of mdPaths) {
    if (state.items.some(i => i.path === p)) continue;
    const item = {
      id: nextId++,
      path: p,
      name: p.split("/").pop(),
      status: "queued",
      error: null,
      output: null,
      staged: stagedFlag || /\/\.md-converter\/staging\//.test(p),
      outDir: "—",
    };
    state.items.push(item);
    // fetch per-item output preview (fire and forget)
    api("preview_output_for", p).then(out => {
      if (out) { item.outDir = out; render(); }
    });
  }
  render();
  updateDragWarning();
}

function updateDragWarning() {
  const w = $("drag-warning");
  if (!w) return;
  const hasStaged = state.items.some(i => i.staged && i.status !== "done");
  if (hasStaged && state.outputMode === "sibling") {
    const n = state.items.filter(i => i.staged && i.status !== "done").length;
    w.innerHTML = `⚠ ${n} 个拖入文件无源路径，将输出到 <code>~/Desktop/Converted/</code>。想输出到源文件夹？<a id="use-picker">点击选择文件</a>。`;
    w.classList.remove("hidden");
    const p = document.getElementById("use-picker");
    if (p) p.addEventListener("click", async () => {
      const picked = await api("pick_files");
      if (picked && picked.length) await addPaths(picked);
    });
  } else {
    w.classList.add("hidden");
  }
}

function render() {
  const fmt = document.querySelector('input[name="fmt"]:checked').value;
  const ul = $("queue");
  ul.innerHTML = "";
  for (const it of state.items) {
    const li = document.createElement("li");
    li.className = `q-item status-${it.status}`;

    const main = document.createElement("div");
    main.innerHTML = `<div class="name">${escape(it.name)}</div><div class="path">${escape(it.path)}</div>`;

    const badge = document.createElement("div");
    badge.className = "badge";
    badge.textContent = `md → ${fmt}`;

    const status = document.createElement("div");
    status.className = "status";
    status.textContent = statusLabel(it.status);

    li.append(main, badge, status);

    // per-item output-path preview
    if (it.outDir && it.status !== "done") {
      const op = document.createElement("div");
      op.className = "outpath" + (it.staged ? " staged" : "");
      op.textContent = "→ " + it.outDir;
      li.appendChild(op);
    }

    if (it.error) {
      const err = document.createElement("div");
      err.className = "error-msg";
      err.textContent = it.error;
      li.appendChild(err);
    }

    if (it.status === "done" && it.output) {
      const actions = document.createElement("div");
      actions.className = "row-actions";
      actions.innerHTML = `
        <button data-act="open-file" data-path="${escapeAttr(it.output)}">打开产物</button>
        <button data-act="reveal" data-path="${escapeAttr(it.output)}">定位文件夹</button>
      `;
      li.appendChild(actions);
    } else if (it.status === "error") {
      const actions = document.createElement("div");
      actions.className = "row-actions";
      actions.innerHTML = `<button class="retry-btn" data-act="retry" data-id="${it.id}">重试</button>`;
      li.appendChild(actions);
    }
    ul.appendChild(li);
  }
  $("empty-hint").classList.toggle("hidden", state.items.length > 0);
  const hasQueued = state.items.some(i => i.status === "queued");
  const hasDone = state.items.some(i => i.status === "done");
  $("convert-btn").disabled = !hasQueued || state.converting;
  $("clear-btn").disabled = state.items.length === 0 || state.converting;
  $("sweep-btn").disabled = !hasDone || state.converting;
}

function statusLabel(s) {
  return {
    queued: "⏳ 排队",
    running: "转换中…",
    done: "✓ 完成",
    error: "✗ 失败",
  }[s] || s;
}

$("queue").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const act = btn.dataset.act;
  const path = btn.dataset.path;
  if (act === "open-file") await api("open_path", path);
  if (act === "reveal") await api("reveal_path", path);
  if (act === "retry") {
    const id = Number(btn.dataset.id);
    const it = state.items.find(x => x.id === id);
    if (it) { it.status = "queued"; it.error = null; render(); }
  }
});

// ---------- Controls ----------
document.querySelectorAll('input[name="fmt"]').forEach(r =>
  r.addEventListener("change", render)
);

$("clear-btn").addEventListener("click", () => {
  state.items = [];
  render();
  setSummary("");
});

$("output-mode").addEventListener("change", async (e) => {
  state.outputMode = e.target.value;
  await api("set_output_mode", state.outputMode);
  updateOutputPath();
  // refresh per-item output previews
  for (const it of state.items) {
    if (it.status === "done") continue;
    api("preview_output_for", it.path).then(out => {
      if (out) { it.outDir = out; render(); }
    });
  }
  updateDragWarning();
});

$("open-output").addEventListener("click", async () => {
  await api("open_output_dir");
});

async function updateOutputPath() {
  const p = await api("describe_output_path");
  if (p) $("output-path").textContent = p;
}

// ---------- Convert ----------
$("convert-btn").addEventListener("click", async () => {
  if (state.converting) return;
  const pending = state.items.filter(i => i.status === "queued");
  if (!pending.length) { flashSummary("队列里没有待转换项", "error"); return; }
  const prevDone = state.items.filter(i => i.status === "done").length;

  state.converting = true;
  render();
  const fmt = document.querySelector('input[name="fmt"]:checked').value;
  setSummary("转换中…");
  setProgress(0);
  api("set_dock_badge", String(pending.length));

  const start = performance.now();
  let done = 0;
  let failed = 0;

  for (const it of pending) {
    it.status = "running";
    it.error = null;
    render();
    const res = await api("convert_one", it.path, fmt);
    if (res && res.ok) {
      it.status = "done";
      it.output = res.output;
    } else {
      it.status = "error";
      it.error = (res && res.error) || "转换失败";
      failed++;
    }
    done++;
    const remaining = pending.length - done;
    api("set_dock_badge", remaining > 0 ? String(remaining) : "");
    setProgress(done / pending.length * 100);
    render();
  }

  const secs = ((performance.now() - start) / 1000).toFixed(1);
  const success = pending.length - failed;
  const pastSuffix = prevDone > 0 ? ` · ${prevDone} 项此前已完成` : "";
  if (failed === 0) {
    setSummary(`✓ ${success} 项新完成${pastSuffix} · 用时 ${secs}s`, "success");
    api("set_dock_badge", "✓");
    setTimeout(() => api("set_dock_badge", ""), 3000);
  } else {
    setSummary(`完成 ${success} · 失败 ${failed}${pastSuffix} · 用时 ${secs}s`, "error");
    api("set_dock_badge", String(failed));
  }
  state.converting = false;
  render();
  updateDragWarning();
});

$("sweep-btn").addEventListener("click", () => {
  state.items = state.items.filter(i => i.status !== "done");
  render();
  updateDragWarning();
});

function setProgress(pct) {
  document.querySelector(".progress-fill").style.width = pct + "%";
}
function setSummary(text, cls) {
  const el = $("summary");
  el.textContent = text;
  el.className = "summary" + (cls ? " " + cls : "");
}
function flashSummary(text, cls) {
  setSummary(text, cls);
  setTimeout(() => setSummary(""), 2500);
}

// ---------- Keyboard shortcuts ----------
// ⌘O pick files · ⌘⏎ convert · ⌘⌫ clear · ⌘K clear completed · ⌘L focus paste
document.addEventListener("keydown", async (e) => {
  if (!e.metaKey || e.ctrlKey) return;
  const tag = (e.target?.tagName || "").toLowerCase();
  const inInput = tag === "input" || tag === "textarea" || tag === "select";
  const key = e.key.toLowerCase();

  if (key === "o" && !inInput) {
    e.preventDefault();
    const picked = await api("pick_files");
    if (picked && picked.length) await addPaths(picked);
  } else if (key === "enter") {
    e.preventDefault();
    $("convert-btn").click();
  } else if (key === "backspace" && !inInput) {
    e.preventDefault();
    $("clear-btn").click();
  } else if (key === "k" && !inInput) {
    e.preventDefault();
    $("sweep-btn").click();
  } else if (key === "l") {
    e.preventDefault();
    $("paste-input").focus();
    $("paste-input").select();
  }
});

// ---------- Utils ----------
function escape(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}
function escapeAttr(s) { return escape(s); }
