# Markdown Converter — Claude Code 上下文

本地 MD → DOCX/PDF/XLSX/HTML 转换小工具，PyWebView + Pandoc。作者 Iris Zhou。

## 快速迭代
- **启动调试**：`./run.sh`（首次会自动建 venv + 装依赖）
- **重打包 .app**：`./build-app.sh`（改了 UI 或 Python 都要重打才能在 Applications 里生效）
- **改图标**：改 `assets/icon.png` 或 `assets/make-icon.py` → `python3 assets/make-icon.py` → `./build-app.sh`
- **Push 开源仓**：`git add . && git commit -m "..." && git push`（已配好 origin，Keychain 缓存了 PAT）

## 代码结构
```
app.py              PyWebView 入口，Api 类暴露给 JS；启动时读 sys.argv（Finder 拖到 Dock 图标场景）
run.sh              启动脚本：手动 prepend /opt/homebrew/bin 到 PATH，否则 .app 启动找不到 pandoc
build-app.sh        osacompile 打 AppleScript .app，带 on open handler + 自定义图标 + Info.plist

converter/
  pipeline.py       格式路由 + 语言检测（zh/en/auto）
  themes.py         FONTS(latin_*+cjk_* 分离) / SIZES / COLORS / LANGS
  docx.py           pandoc + 后处理 rFonts（按 primary 分设 ascii/eastAsia）
  pdf.py            pandoc→html5 + weasyprint + theme CSS 注入
  xlsx.py           markdown-it-py 抽表 + openpyxl 写
  html.py           pandoc --standalone + embed-resources + theme CSS 注入

ui/
  index.html        单页结构
  styles.css        梅子×鼠尾草 × Cormorant
  app.js            拖拽/粘贴/队列/快捷键/Dock 徽章/实时预览卡

assets/
  pdf-styles.css    PDF 基础样式
  html-template.html
  icon.png / make-icon.py
```

## 常见坑（非 bug，是约束）
1. **窗口拖拽拿不到源路径**：PyWebView 6.x 不暴露 `file.path` → FileReader 读内容 → stage 到 `~/.md-converter/staging/` → 输出强制走 `~/Desktop/Converted/`。想 sibling 输出必须用 "点击选择文件" 或 "Finder 拖到 Dock 图标"（后者走 AppleScript `on open` 拿真实路径）。
2. **weasyprint 需要 pango**：`brew install pango` + 进程 env 必须有 `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`。run.sh 和 app.py 开头都设了。
3. **中英混排的设计决定**：zh-primary 时 `w:ascii = w:hAnsi = w:eastAsia = CJK字体`（中文段里英文单词也用 CJK 字体自带的 Latin 字形，整段视觉统一）；en-primary 时走经典 ascii=Latin/eastAsia=CJK。这是用户明确要的，不是 bug。
4. **Dock 徽章** 走 `from AppKit import NSApp`（pyobjc 随 pywebview 传递装好）。
5. **队列只跑 queued 项**：`app.js` 的 convert 循环先 filter status === "queued"。done/error 保留作会话历史，关闭即丢（不持久化到磁盘）。

## 扩展落点（常见需求映射）
| 想做 | 改哪里 |
|------|--------|
| 加字体主题 | `converter/themes.py` 的 `FONTS` 加一项（记得 latin_* + cjk_*）|
| 加配色 | `COLORS` 加一项 |
| 加输出格式 | `converter/<fmt>.py` 实现 `convert(src, out, assets, style)` → `pipeline._CONVERTERS` 注册 → HTML radio 加项 |
| 改实时预览卡示例文案 | `ui/index.html` 的 `.preview-card` 里 |
| 改默认字体/字号/配色 | `converter/themes.py` 的 `DEFAULTS` |

## 快捷键（记在代码里 `app.js` 底部）
`⌘O` 选文件 · `⌘⏎` 转换 · `⌘⌫` 清空 · `⌘K` 清理已完成 · `⌘L` 聚焦粘贴框

## 遗留 / 未做
- 没单例锁：已打开的 .app 被 Finder 重新拖文件时会新开进程（罕见场景，按需加 socket lock）
- 没做 `Windows` / `Linux` 适配（run.sh 里的 brew 路径和 Dock 徽章都是 macOS 专属）
- DOCX 没自带 reference.docx 模板；用户可放一份进 `assets/reference.docx`，pandoc 自动用
