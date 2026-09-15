# Zotero 接入说明

本文件说明如何在本机**发现** Zotero 环境，并列出可用的连接方式。所有路径、ID、端口都是动态发现或由用户提供的，**不在代码中硬编码**。

## 1. 发现本机 Zotero 数据目录

Zotero 数据目录（存放 `zotero.sqlite` 与 `storage/` 附件）的位置因机器而异：

- 图形界面：Zotero → 设置（首选项）→ 高级 → 文件和文件夹 → **数据目录位置**。
- Windows 默认：`%APPDATA%\Zotero\Zotero\Profiles\<profile>\`；用户也可自定义到任意盘符（见图形界面设置）。
- 通过连接器：部分 Zotero 连接器接口会返回附件的本地路径（`resolvedPath`）。

> `storage/<key>/<filename>.pdf` 是附件在数据目录内的标准布局，但**根路径必须动态取得**，不要假设盘符。

## 2. libraryID 不要写死

一个 Zotero 配置可能有多个文库（我的文库、组文库）。每次操作前先调用连接器的"获取文库"能力（如 `get_libraries`）确认 `libraryID`。示例中常见"1 = 我的文库"，仅作示意，**务必以连接器返回值为准**。

## 3. 可用的连接方式

按可用性优先排序：

### 3.1 JS Bridge 插件（cli-anything-zotero，推荐用于附件回写）

- 安装：`python -m pip install cli-anything-zotero`（装到**任意** Python 环境即可，不必是特定 conda 环境）。
- 生成插件：`zotero-cli app install-plugin`，在 Zotero 中 Tools → Add-ons → 齿轮 → Install Add-on From File 选择生成的 xpi，重启 Zotero。
- 定位 `zotero-cli`：安装后通过 `Get-Command zotero-cli`（PowerShell）或 `where zotero-cli` 找到可执行文件；未加入 PATH 时使用其完整路径。
- 验证：`zotero-cli app plugin-status`，期望 `endpoint_active=true, js_ok=true, ready=true`。
- 前提：**Zotero 必须正在运行**（JS Bridge 需要 Zotero 运行时）。

### 3.2 Zotero MCP server

- 默认端口 **23120**（可在服务配置中修改）。若调用报 `Transport send error`，先 `netstat -ano | findstr 23120` 确认端口在监听，再重试一次。
- 客户端通过自己的 MCP 工具名调用（Doubao 中可能是 `mcp__zotero__*`，Codex 中通过 MCP 配置注入）。**工具名因客户端而异，按当前环境可用的名字调用。**

### 3.3 Zotero Connector HTTP API

- 默认端口 **23119**，提供 `saveItems` 等接口。
- 限制：**不能创建文件附件**（attachments 数组会被忽略），只能创建条目元数据。

## 4. 分类与附件判断

- 分类可能嵌套：父分类 `numItems=0` 不代表空，必须递归展开子分类（如 `get_collections(recursive=true)`）。
- 判断 PDF 附件：查看附件数组是否非空且存在 `contentType: application/pdf`（或全文索引标记 `hasFulltext: true`）。`attachments: []` 表示无 PDF。
- 父条目 key：连接器返回的条目 key 就是父条目 key（文献本身），PDF 附件是其子条目。若只拿到 PDF 附件 key，需通过数据库反查父条目：

```sql
SELECT parentItemID FROM itemAttachments WHERE itemID = (SELECT itemID FROM items WHERE key = ?);
```

## 5. 数据库被锁时用副本查询

Zotero 运行时 `zotero.sqlite` 被独占锁定。需要直接查询数据库时，先把数据库复制到临时文件再查询副本，**不要关闭用户的 Zotero**。

## 6. 客户端适配说明

不同客户端提供的工具名不同（文件读取、编辑、执行、交付、MCP 调用等）。`SKILL.md` 只使用**能力描述**（如"分块读取正文""保存到用户可访问的输出目录""使用当前可用的 Zotero 连接器"），具体工具名按当前环境选择：

- **Doubao 环境**：文件操作与交付用其内置工具；MCP 工具可能需要先激活（tool_search）再调用。
- **Codex 环境**：文件操作用其内置能力；Zotero MCP 通过 `agents/openai.yaml` 与 MCP 配置注入。
- 任何环境都可用：`scripts/check_environment.py` 检查连接可用性。
