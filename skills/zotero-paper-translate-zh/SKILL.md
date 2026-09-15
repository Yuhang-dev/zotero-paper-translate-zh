---
name: zotero-paper-translate-zh
description: 将学术 PDF，尤其是 Zotero 附件，翻译为中文 Markdown，并可生成结构化摘要。当用户明确要求翻译或总结 Zotero PDF 时使用；仅在用户要求且连接器支持时把结果挂回 Zotero。
license: MIT
---

# Zotero Paper Translate（中文）

## 概述

把学术论文 PDF（通常来自 Zotero 收藏）批量转换为"中文翻译 + 约 500 字结构化总结"的 Markdown 文件。输出头部为文章总结（用 `---` 与正文隔开），正文为完整中译（不含参考文献）。翻译产物保存到用户可访问的输出目录。

本 skill **不绑定任何客户端工具、本机路径或 libraryID**。Zotero 数据目录、libraryID、端口等一律通过用户参数、Zotero API 或环境变量动态取得。

## 前置条件

- Zotero Desktop 已安装（可选：若用户直接提供 PDF 文件，可不依赖 Zotero）。
- Python 3.9+，依赖见本目录 `requirements.txt`（PyMuPDF>=1.24）。
- 首次使用先运行环境检查：`python scripts/check_environment.py`。

## 工作流

### Step 1 定位 PDF 附件

通过当前可用的 Zotero 连接器（JS Bridge / MCP / Connector HTTP API）定位文献与附件：

1. 先获取文库信息，确认 `libraryID`（**不要假设为 1**，以连接器返回为准）。
2. 定位目标分类；分类可能嵌套，父分类条目数为 0 时仍需展开子分类。
3. 逐分类取条目，判断是否带 PDF 附件（附件内容类型为 `application/pdf` 或含全文索引）。
4. 记录每篇文献的**父条目 key**（文献本身的 key，不是 PDF 附件 key）。

详细接入方式与客户端适配说明见 `references/zotero-access.md`。

### Step 2 提取正文（剔除参考文献）

用本 skill 自带脚本提取正文（不要在命令行内联多行 Python）：

```powershell
python scripts/extract_pdf_body.py "<PDF 绝对路径>" --out "<输出 txt 路径>"
```

脚本特性：

- 只在**独立标题行**（References / Bibliography 等，容忍尾部标点与章节编号）判定参考文献起点，正文中出现的引用词不误判；
- 优先扫描文档**后半部分**，降低目录页误判；
- 页码按 PyMuPDF 的 **0 起始索引**计，JSON 输出同时给出 1 起始的人类可读页码；
- 未提取到文字时提示**可能是扫描 PDF，需要 OCR**；
- 自动创建输出目录，错误信息清晰、退出码非 0。

### Step 3 翻译正文

- 长正文**分块读取、分块翻译、追加写入** md 文件，不要一次读全文；被截断时缩小读取范围，绝不基于截断内容下结论。
- 保留原文专有名词/缩写（如 RoPE、KV-cache、SparseGPT），引用编号 `[n]` 原样保留。
- 数学公式必须用标准 LaTeX 语法（KaTeX 可渲染），规范见 `references/output-format.md`。

### Step 4 写总结并组装 md

每篇 md 结构固定（总结在前，`---` 分隔）：

```markdown
# <论文中文标题>

> **原文标题**: ...
> **作者**: ...
> **出处**: ...
> **DOI**: ...
> **本文为正文中译，参考文献部分未翻译。**

---

## 文章总结

<约 500 字中文总结：研究问题 → 方法/创新 → 关键结果 → 结论/意义>

---

## 摘要
<正文翻译从这里开始，按原文章节继续：## 一、...、## 二、...>
```

- 总结必须放文件前面，用 `---` 隔开；正文从摘要/引言开始。
- 总结约 500 字，覆盖：背景问题 → 方法/创新 → 关键结果 → 结论/意义。

### Step 5 交付

- 将每篇 `.md` 保存到用户可访问的输出目录（当前工作目录或用户指定目录），并明确告知文件路径。
- 交付说明中注明：每篇已翻译、参考文献未翻译、总结字数与覆盖章节。

### Step 6 挂回 Zotero（可选）

仅在用户**明确要求**"在 Zotero 里能看到 / 挂到条目下"时执行：

- 使用当前可用的 Zotero 连接能力注册附件（JS Bridge 插件优先）。
- 父条目 key 是文献本身的 key，不是 PDF 附件的 key；libraryID 动态获取。
- **安全约束**：本 skill 不提供任何永久删除命令。需要清理时只允许移到回收站（可恢复），并明确告知用户。

详细方式与注意事项见 `references/attachment.md`。

## 环境检查与故障排查

- 运行 `python scripts/check_environment.py` 检查：Python 版本、PyMuPDF、Zotero 是否运行、可用连接方式。
- 常见问题：
  - 参考文献定位：逐页扫独立标题行；未找到时默认全文为正文。
  - Zotero 数据库被锁：运行时 `zotero.sqlite` 被锁定，用副本查询（见 `references/zotero-access.md` §5）。
  - MCP 并发：批量操作时并行调用超过 2-3 个会失败，逐个调用并在失败后等待重试。
  - 附件回写前确认 Zotero 正在运行。
