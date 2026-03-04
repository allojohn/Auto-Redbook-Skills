---
name: xhs-note-creator
description: 小红书笔记素材创作技能。当用户需要创建小红书笔记素材时使用这个技能。技能包含：根据用户的需求和提供的资料，撰写小红书笔记内容（标题+正文），生成图片卡片（封面+正文卡片），以及发布小红书笔记。
---

# 小红书笔记创作技能

这个技能用于创建专业的小红书笔记素材，包括内容撰写、图片卡片生成和笔记发布。

## 使用场景

- 用户需要创建小红书笔记时
- 用户提供资料需要转化为小红书风格内容时
- 用户需要生成精美的图片卡片用于发布时

## 工作流程

这个技能遵循“内容先行，确认后渲染”的原则，支持灵活的人工干预。
### 第一阶段：内容创作（生成中间态 Markdown）

根据内容长度和复杂度，采用不同的创作策略：

#### 方案 A：长内容策略（多图模式）
- **适用场景：** 推文翻译原文较长，包含多个深度观点或复杂技术术语。
- **内容结构：** 
  1. 封面元数据
  2. 精华总结
  3. **💡 背景知识/术语百科**（针对推文涉及的 nanoGPT、tmux、智能体等术语进行 1-2 句的大白话解释）
  4. `---` 分隔
  5. `# 📜 完整翻译原文`
- **目标：** 降低阅读门槛，通过精华和科普吸引用户，通过全文提供深度价值。

#### 方案 B：短内容策略（单图模式）
...

- **适用场景：** 推文翻译内容简短（通常在 500-600 字以内，如 Karpathy 的随笔或短评）。
- **内容结构：** 封面元数据（仅包含 `title`）+ 翻译正文（不包含“精华总结”和多余的分隔符）。
- **目标：** 将所有内容紧凑地平铺在一张封面图中，实现最高效的信息传递。

#### 核心要求：
1.  **展示并存储：** 将生成的 Markdown 文件保存到本地，并**务必在对话中完整展示给用户**供其审核修改。
2.  **视觉纯净度：** 无论是哪种方案，都必须严格执行下方的“推文处理专项规则”，剔除元数据和交互数据。

### 第二阶段：用户审核与干预

在此步骤，用户可以进行两种选择：
- **路径 A（直接渲染）：** 用户对 Markdown 内容满意，直接指令进行图片生成。
- **路径 B（人工修改）：** 用户自行修改 Markdown 文件（或要求 AI 修改）后，再指令 AI 基于新版本进行图片生成。

### 第三阶段：图片渲染

将最终定稿的 Markdown 文档渲染为图片卡片。

```bash
python scripts/render_xhs.py <定稿的markdown文件> [options]
```

- **推荐样式：** 默认使用 `-t terminal`（终端风）以符合 Karpathy 推文调性。
- **分页模式：** 必须使用 `-m auto-split` 以确保长原文能自动分页。


- 默认输出目录为当前工作目录
- 生成的图片包括：封面（cover.png）和正文卡片（card_1.png, card_2.png, ...）

#### 渲染参数（Python）

| 参数 | 简写 | 说明 | 默认值 |
|---|---|---|---|
| `--output-dir` | `-o` | 输出目录 | 当前工作目录 |
| `--theme` | `-t` | 排版主题 | `default` |
| `--mode` | `-m` | 分页模式 | `separator` |
| `--width` | `-w` | 图片宽度 | `1080` |
| `--height` |  | 图片高度（`dynamic` 下为最小高度） | `1440` |
| `--max-height` |  | `dynamic` 最大高度 | `4320` |
| `--dpr` |  | 设备像素比（清晰度） | `2` |

#### 排版主题（`--theme`）

- `default`：默认简约浅灰渐变背景（`#f3f3f3 -> #f9f9f9`）
- `playful-geometric`：活泼几何（Memphis）
- `neo-brutalism`：新粗野主义
- `botanical`：植物园自然
- `professional`：专业商务
- `retro`：复古怀旧
- `terminal`：终端命令行
- `sketch`：手绘素描

#### 分页模式（`--mode`）

- `separator`：按 `---` 分隔符分页（适合内容已手动控量）
- `auto-fit`：固定尺寸下自动缩放文字，避免溢出/留白（适合封面+单张图片但尺寸固定的情况）
- `auto-split`：按渲染后高度自动切分分页（适合切分不影响阅读的长文内容）
- `dynamic`：根据内容动态调整图片高度（注意：图片最高 4320，字数超过 550 的不建使用此模式）

#### 常用示例

```bash
# 1) 默认主题 + 手动分隔分页
python scripts/render_xhs.py content.md -m separator

# 2) 固定 1080x1440，自动缩放文字，尽量填满画面
python scripts/render_xhs.py content.md -m auto-fit

# 3) 自动切分分页（推荐：内容长短不稳定）
python scripts/render_xhs.py content.md -m auto-split

# 4) 动态高度（允许不同高度卡片）
python scripts/render_xhs.py content.md -m dynamic --max-height 4320

# 5) 切换主题
python scripts/render_xhs.py content.md -t playful-geometric -m auto-split
```

#### Node.js 渲染（可选）

```bash
node scripts/render_xhs.js content.md -t default -m separator
```

Node.js 参数与 Python 基本一致：`--output-dir/-o`、`--theme/-t`、`--mode/-m`、`--width/-w`、`--height`、`--max-height`、`--dpr`。

### 第四步：发布小红书笔记（可选）

使用发布脚本将生成的图片发布到小红书：

```bash
python scripts/publish_xhs.py --title "笔记标题" --desc "笔记描述" --images card_1.png card_2.png cover.png
```

**前置条件**：

1. 需配置小红书 Cookie：
```
XHS_COOKIE=your_cookie_string_here
```

2. Cookie 获取方式：
   - 在浏览器中登录小红书（https://www.xiaohongshu.com）
   - 打开开发者工具（F12）
   - 在 Network 标签中查看请求头的 Cookie

## 图片规格说明

### 封面卡片
- 尺寸比例：3:4（小红书推荐比例）
- 基准尺寸：1080×1440px
- 包含：Emoji 装饰、大标题、副标题
- 样式：渐变背景 + 圆角内容区

### 正文卡片
- 尺寸比例：3:4
- 基准尺寸：1080×1440px
- 支持：标题、段落、列表、引用、代码块、图片
- 样式：白色卡片 + 渐变背景边框

## 技能资源

### 脚本文件
- `scripts/render_xhs.py` - Python 渲染脚本
- `scripts/render_xhs.js` - Node.js 渲染脚本
- `scripts/publish_xhs.py` - 小红书发布脚本

### 资源文件
- `assets/cover.html` - 封面 HTML 模板
- `assets/card.html` - 正文卡片 HTML 模板
- `assets/styles.css` - 共用样式表

## 注意事项

1. Markdown 文件应保存在工作目录，渲染后的图片也保存在工作目录
2. 技能目录 (`md2Redbook/`) 仅存放脚本和模板，不存放用户数据
3. 图片尺寸会根据内容自动调整，但保持 3:4 比例
4. Cookie 有有效期限制，过期后需要重新获取
5. 发布功能依赖 xhs 库，需要安装：`pip install xhs`
6. **推文处理专项规则：**
   - **禁止展示元数据：** 在渲染原始推文翻译时，必须移除“时间”、“链接”等元数据信息。
   - **禁止展示交互数据：** 必须移除推文末尾的“评论、转发、点赞、浏览量”等数据行（即包含 💬🔄❤️👀📊 符号的那一行）。
   - **保持纯净：** 仅保留推文的正文翻译内容，确保卡片视觉纯净度。
