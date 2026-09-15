# Zotero Paper Translate（中文）

将学术 PDF（尤其是 Zotero 收藏的论文）批量翻译为中文 Markdown，并为每篇生成约 500 字结构化摘要。产物格式规范、Zotero 接入方式与附件回写说明均随 skill 分发，**不绑定任何本机路径、libraryID 或特定客户端工具**——所有环境信息一律通过用户参数、Zotero API 或环境变量动态取得。

## 功能

- 定位 Zotero 分类下带 PDF 附件的文献（支持嵌套分类）
- 提取 PDF 正文并自动剔除参考文献（独立标题行检测，优先扫描文档后半部分，降低目录页误判）
- 分段翻译为中文，数学公式保持标准 LaTeX（KaTeX 可渲染）
- 每篇生成约 500 字中文结构化总结（研究问题 → 方法/创新 → 关键结果 → 结论/意义）
- 可选：将翻译 md 作为附件挂回 Zotero 条目（仅在用户明确要求时执行）

## 前置要求

| 依赖 | 说明 |
|---|---|
| Zotero Desktop | 可选——若用户直接提供 PDF 文件则不需要；附件回写时必需且需保持运行 |
| Python 3.9+ | 运行提取与检查脚本 |
| PyMuPDF | 安装：`python -m pip install -r skills/zotero-paper-translate-zh/requirements.txt` |
| Zotero 连接器（可选） | JS Bridge 插件（推荐，用于附件回写）或 Zotero MCP，用于定位附件与回写 |

> 注意：只安装本 skill 并不等于完成全部 Zotero 集成。用户至少还需要 Zotero Desktop、PDF 提取依赖（PyMuPDF），以及一种可用的 Zotero 连接器。

## 安装

### 方式一：GitHub 安装器

安装器会复制所选 skill 目录，因此必须指向包含 `SKILL.md` 的目录：

```
https://github.com/Yuhang-dev/zotero-paper-translate-zh/tree/main/skills/zotero-paper-translate-zh
```

### 方式二：手动复制

将 `skills/zotero-paper-translate-zh/` 整个目录复制到目标客户端的 skills 目录。

## 使用

1. 在仓库根目录运行环境检查：`python skills/zotero-paper-translate-zh/scripts/check_environment.py`
2. 按 `SKILL.md` 的工作流执行：定位 PDF → 提取正文 → 分段翻译 → 组装 md → 交付 →（可选）挂回 Zotero。

## 仓库结构

```
repository/
├── README.md
├── LICENSE
├── .gitignore
└── skills/
    └── zotero-paper-translate-zh/
        ├── SKILL.md              # 核心流程（仅能力描述，无客户端工具名）
        ├── requirements.txt      # 自包含依赖（PyMuPDF>=1.24）
        ├── agents/
        │   └── openai.yaml       # Codex UI 名称与默认提示（可选）
        ├── scripts/
        │   ├── extract_pdf_body.py   # 提取正文、剔除参考文献
        │   └── check_environment.py  # 检查依赖、Zotero 运行状态与可用连接
        └── references/
            ├── zotero-access.md  # Zotero 接入：数据目录/libraryID/连接方式/适配说明
            ├── attachment.md     # 附件回写与安全清理约束
            └── output-format.md  # 翻译产物格式与公式规范
```

## 安全约束

- 本 skill **不提供任何永久删除命令**（如 `item delete --confirm`）。需要清理附件时只允许移到回收站（可恢复）。
- 绝对不要直写 `zotero.sqlite` 创建附件——附件能显示但打不开，且有损坏数据库风险。

## License

MIT
