# 换电脑继续开发

仓库同时保存 **开发源文件 `dev/`** 和 **根目录的 GitHub Pages 发布文件**。克隆整个仓库即可继续编辑、构建和发布，无需旧电脑的临时目录、简历 PDF 或原参考站在线服务。

## 首次准备

安装 Git 和 Python 3.10 或更新版本。Node.js 只在使用原本的草稿服务器时需要，标准构建和预览不需要它。

```bash
git clone https://github.com/ShaojieLiang/ShaojieLiang.github.io.git
cd ShaojieLiang.github.io
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

如果系统使用 `python3` 命令，创建虚拟环境时改用 `python3`。如果 PowerShell 不允许激活，可直接用 `.\.venv\Scripts\python.exe` 代替后续的 `python`，无需修改系统策略。

## 修改 → 构建 → 检查 → 预览

```bash
python build.py
python check.py
python -m http.server 8000
```

手动打开 http://localhost:8000/ 。`check.py` 自动启动临时静态服务器，检查页面、经历路由和素材，完成后自动关闭；它不打开浏览器。

日常修改入口：

| 文件 | 用途 |
| --- | --- |
| `dev/content.json` | 个人介绍、技能、教育、实习和项目经历 |
| `dev/site/personal.css` | 中文排版、个人布局与视觉调整 |
| `dev/site/personal.js` | 施工告示板和默认静音逻辑 |
| `dev/tools/build_mirror.py` | 页面结构与导航文案的转换规则 |
| `dev/tools/resume_content.py` | 时间线、详情和关于页组件 |
| `dev/upstream/` | 原始 HTML、CSS、JS 模板，已存入仓库 |
| `dev/site/public/` | 图片、字体、木偶部件、声音和前端库 |
| `dev/README.github.md` | GitHub 仓库介绍页的编辑源文件 |
| `dev/readme-assets/cover.svg` | 仓库介绍封面 |
| `dev/tools/export_pages.py` | 为 GitHub Pages 生成真实静态路径 |

`dev/site/home.html`、`history.html`、`about.html` 与 `dev/fields.json` 是构建产物，不应作为主要编辑入口。根目录 `index.html`、`pl/`、`public/` 等也是发布产物，直接编辑会在下一次构建时被覆盖。

构建默认只使用仓库内素材，不访问原参考站。首次安装 Python 依赖需要联网。若手动删除了素材，应先用 Git 恢复；仅在明确需要重新抓取公开素材时使用 `python dev/tools/build_mirror.py --fetch-assets`。

可选择输出到其他目录：`python build.py --output dist`。独立摄像头工具和历史兼容文件已随仓库保留，常规构建直接输出到仓库根目录即可。

## 发布

```bash
git pull --ff-only
python build.py
python check.py
git add .
git commit -m "Update personal website"
git push origin main
```

建议开始修改前先 `git pull --ff-only`。GitHub Pages 继续从 `main` 的根目录发布；推送后的部署进度见仓库 Actions。无需额外服务器。

## 项目约定

- 开场使用 hello，完整播放，不提供跳过按钮。
- 开场后保留原告示板的下落摇摆动画，展示施工提示，每次刷新或新访问可见。
- 当前木偶贴图和动作保留；真实经历文字存于 `content.json`，同一年用不同事件 `id` 区分。
- 个人联系方式、简历原件、聊天记录、凭据和本机绝对路径不作为源码上传。
- 当前开发源代码已压缩为原站公开前端的可编辑模板形式；更早的独立设计实验不属于这个线上版本。
- 第三方动画、字体和图片来源说明保留在 README；历史配图不是个人经历实拍。
