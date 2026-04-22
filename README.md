# Markdown Converter

> 本地、离线、审美在线的 Markdown 转换工具。拖一下，.md 变成 .docx / .pdf / .xlsx / .html。

![preview](assets/icon.png)

## ✨ Features

- **四种输出** · DOCX / PDF / XLSX（表格提取）/ HTML，一次选定
- **排版可调** · 4 种字体、4 档字号、5 种配色方案，实时样式预览卡
- **中英混排不乱** · 自动识别文档主导语言，中文段里的英文单词用中文字体的 Latin 字形，整段视觉协调
- **三种输入** · 拖拽到窗口 · 点击选文件 · 粘贴路径（支持 `~` 和 `*.md` 通配符）
- **真正的原生体验** · Finder 把 .md 拖到 Dock 里的应用图标即可打开；Dock 徽章显示剩余转换数；转换完成变 ✓
- **会话历史** · 转完保留在队列里做记录，下次点转换只跑新加的，不会重复处理
- **键盘驱动** · `⌘O` 选文件 / `⌘⏎` 开始 / `⌘⌫` 清空 / `⌘K` 清理已完成

## 📸 Screenshots

（UI 截图可后续加到 `docs/` 目录）

## 🚀 Quick Start

```bash
# 前置：pandoc + pango（weasyprint 渲染 PDF 需要）
brew install pandoc pango

# 克隆 & 启动
git clone https://github.com/carpediemzzsssww-cpu/markdown-converter.git
cd markdown-converter
./run.sh
```

首次运行会自动创建 Python venv 并安装依赖（pywebview / weasyprint / openpyxl / markdown-it-py / python-docx / Pillow）。之后每次直接 `./run.sh` 启动。

### 打包成 macOS App

```bash
./build-app.sh
```

生成 `Markdown Converter.app`，拖进 `/Applications`、再拖到 Dock。之后：

- **双击** Dock 图标 → 启动
- **从 Finder 拖 .md 到 Dock 图标** → 启动并加载该文件（保留源路径，sibling 输出可用）
- **Spotlight** 搜 "Markdown Converter" → 回车启动

## 🗂 Usage

### 输出位置

右上角切换：
- `源文件旁 ./converted/`（默认）— 每个 MD 的同级生成 `converted/` 子目录
- `~/Desktop/Converted/` — 全局收纳
- `每次询问` — 转换前弹 Finder 选

> **窗口内拖拽**的文件会因 Web 安全限制无法获取源路径，强制输出到 Desktop/Converted/。想要 sibling 输出，用 "点击选择文件" 或 "Finder 拖到 Dock 图标"。

### 样式自定义

控件行：**字体 · 字号 · 主要语言 · 配色**

- 字体：编辑感（Cormorant）· 现代（Inter）· 学术（Times）· 极简（Helvetica）
- 主要语言：自动 / 中文为主 / 英文为主 — 控制混排时哪种字体占主导
- 配色：梅子 × 鼠尾草 · 墨色极简 · 鼠尾草 × 米色 · 靛蓝 × 砂金 · 陶土 × 橄榄

选完的配置写入 `~/.md-converter/config.json`，下次启动自动加载。

### XLSX 说明

只提取 MD 中的**表格**（每张表一个 sheet）。无表格的 MD 会报 "该文件中没有找到表格"。

## 🛠 Tech Stack

- **Pandoc** — 核心转换引擎（MD → DOCX / HTML）
- **WeasyPrint** — HTML → PDF（支持 CSS 分页、字体嵌入）
- **python-docx** — DOCX 后处理（rFonts 分 latin/eastAsia，按主导语言设置）
- **openpyxl** — XLSX 写入
- **markdown-it-py** — 解析 MD 中的表格
- **PyWebView** — 本地 GUI 框架（Cocoa + WKWebView on macOS）
- **Pillow** — 程序化生成 App 图标

## 🧩 Project Structure

```
md-converter/
├── app.py                     # PyWebView entry, JS ↔ Python API
├── run.sh                     # One-click launcher
├── build-app.sh               # Packages into macOS .app
├── requirements.txt
├── ui/
│   ├── index.html
│   ├── styles.css
│   └── app.js                 # Drag-drop, queue, live preview, shortcuts
├── converter/
│   ├── pipeline.py            # Route by format + resolve language
│   ├── themes.py              # Font/size/color presets, CJK-aware
│   ├── docx.py                # MD → DOCX (pandoc + post-process)
│   ├── pdf.py                 # MD → HTML → PDF (pandoc + weasyprint)
│   ├── xlsx.py                # MD tables → XLSX
│   └── html.py                # MD → standalone HTML
├── assets/
│   ├── pdf-styles.css         # Base print CSS
│   ├── html-template.html
│   ├── icon.png               # App icon source (1024×1024)
│   └── make-icon.py           # Icon generator (Pillow)
└── test/
    ├── sample.md
    └── mixed.md
```

## 🎨 Customizing

- **DOCX 模板**：放一份 Word 做好的 `assets/reference.docx`，pandoc 会用它的样式
- **PDF / HTML 基础样式**：改 `assets/pdf-styles.css`
- **加新主题**：在 `converter/themes.py` 的 `FONTS` / `COLORS` 里加字典项，UI 自动拉新选项
- **换图标**：把 1024×1024 的 PNG 覆盖到 `assets/icon.png`，再跑一次 `./build-app.sh`

## 🪲 Troubleshooting

| 现象 | 排查 |
|------|------|
| `pandoc 未安装` | `brew install pandoc` |
| PDF 首次生成报 libgobject | `brew install pango` |
| PDF 中文方框 | 系统缺 Source Han Serif / Songti SC，装一个即可 |
| 双击 .app 无反应 | 看 `/tmp/md-converter.log` 尾部错误 |
| 窗口拖拽文件跑去 Desktop 了 | 这是 Web 安全限制；想 sibling，用 "点击选择" 或 "拖到 Dock 图标" |

## 📜 License

MIT © 2026 Iris Zhou

## 🙏 Credits

Built with [Pandoc](https://pandoc.org), [WeasyPrint](https://weasyprint.org), and [PyWebView](https://pywebview.flowrl.com). Palette & typography inspired by the author's personal editorial aesthetic.
