# 附件回写与安全清理说明

用户**不明确说不要挂附件、不要附上翻译等**都要执行本流程

## 1. 前置检查

- Zotero 正在运行。
- 已有可用的连接方式（见 `zotero-access.md` §3）。
- 已取得**父条目 key**（文献本身的 key，不是 PDF 附件 key）与正确的 **libraryID**（`get_libraries` 动态获取）。

## 2. 三种回写方式

### 2.1 JS Bridge（推荐，全自动）

```bash
zotero-cli --json item attach <父条目key> "<md 文件绝对路径>"
```

- 支持 md/pdf/任意文件；md 会自动设 `contentType: text/markdown`。
- 返回 `{"ok": true, "key": "附件key", ...}`。
- 批量：循环调用 `item attach`，或用 `zotero-cli js` 执行批量脚本。

### 2.2 Zotero 内置 JS API（手动）

Zotero → Tools → Developer → Run JavaScript，粘贴（`<libraryID>`、`<workdir>` 替换为本机值）：

```javascript
(async () => {
    const libraryID = <libraryID>; // 由 get_libraries 返回，不要写死 1
    const workdir = '<本机工作目录，Windows 路径用双反斜杠，如 C:\\path\\to\\workdir\\>';
    const mapping = [
        { parentKey: '<父条目key>', file: '<文件名>.md', title: '<标题>(中文翻译)' },
    ];
    let ok = 0, fail = 0, log = '';
    for (const m of mapping) {
        try {
            const parent = Zotero.Items.getByLibraryAndKey(libraryID, m.parentKey);
            if (!parent) { log += `FAIL ${m.parentKey}: parent not found\n`; fail++; continue; }
            const file = Zotero.File.pathToFile(workdir + m.file);
            if (!file.exists()) { log += `FAIL ${m.parentKey}: file not found\n`; fail++; continue; }
            await Zotero.Attachments.importFromFile({
                file: file, parentItemID: parent.id,
                title: m.title, contentType: 'text/markdown'
            });
            log += `OK   ${m.parentKey}: ${m.title}\n`; ok++;
        } catch (e) { log += `FAIL ${m.parentKey}: ${e}\n`; fail++; }
    }
    log += `\n=== Done. OK=${ok}, FAIL=${fail} ===\n`;
    await Zotero.File.putContentsAsync(workdir + 'attach_log.txt', log);
    return log;
})();
```

注意事项：

- 返回 `undefined` 是正常的（异步不被自动 await），以结果文件为准。
- **不要做重复检查**：`parentItem.getAttachments()` 返回的对象无 `getDisplayTitle()` 方法。
- `contentType`: md 用 `'text/markdown'`。

### 2.3 Zotero MCP（少量时可用）

若当前连接器提供导入附件能力（`action=import`），传入文件路径、父条目 key 与显示名即可。

- **并发不稳定**：并行调用超过 2-3 个会频繁报"连接器暂时不可用"。建议逐个调用，失败后等待 5-10 秒重试。
- 大批量（>5 篇）改用 2.1 的 JS Bridge。

## 3. 安全约束（重要）

- **本 skill 不提供任何永久删除命令**（如 `item delete --confirm`、`Zotero.Items.erase`），防止误删用户文献。
- 需要清理附件时，只允许**移到回收站**（可恢复）：

  ```javascript
  const item = Zotero.Items.get(<附件id>);
  item.deleted = 1;
  await item.saveTx();
  ```

  执行后提示用户在 Zotero 中按 F5 刷新查看。
- **绝对不要直写 zotero.sqlite 创建附件**——附件能显示但打不开，且有损坏数据库的风险。Zotero Connector HTTP API 也不支持文件附件。

## 4. 已知限制

- Zotero 内置阅读器只支持 PDF；md 附件双击会用系统默认程序打开，这是正常行为。
- `getAttachments()` 返回 ID 数组，需 `Zotero.Items.get(ids)` 取完整对象后再调用方法，直接对返回值调方法会报 `not a function`。
- `zotero-cli js` 只接受**单行字符串**：多行 JS 需压成一行（分号分隔），或写 Python 脚本用 subprocess 调用。含空格的路径用双引号包裹。
