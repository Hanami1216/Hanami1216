# 修复 GitHub Profile 更新脚本

由于当前的 `update.py` 存在严重的数据覆盖风险和硬编码用户问题，我们需要重构更新逻辑。

## 1. 保护现有内容 (创建模板)
目前的 `update.py` 包含一个简陋的内置模板，会覆盖你精美的 `README.md`。
- **操作**：将当前 `README.md` 的内容复制并保存为 `TEMPLATE.md`。
- **修改**：在 `TEMPLATE.md` 中需要动态更新的区域（如 GitHub 数据统计、最近更新列表）插入占位符（例如 `<!-- START_SECTION:top_repos -->` 或 Python 格式化变量）。

## 2. 修正用户硬编码
- **操作**：修改 `TEMPLATE.md` 或脚本。
- **细节**：将残留的 `quanpeng` (LeetCode) 和 `songwonderful` (知乎) 替换为你的用户名 `Hanami1216`，或者配置为从环境变量读取。

## 3. 重构 update.py
- **读取方式**：改为读取 `TEMPLATE.md` 文件，而不是使用脚本内硬编码的 `abstract_tpl` 字符串。
- **写入逻辑**：将获取到的 GitHub 数据填充进模板，生成新的 `README.md`。
- **保留**：保留你现有的“技术栈”、“精选项目”等手动维护的板块不被破坏。

## 4. 验证 Workflow 分支
- **检查**：确认 `.github/workflows/update.yml` 中的分支名称。
- **修正**：如果你的仓库主分支是 `main` 而不是 `master`，需要将 workflow 中的 `master` 批量替换为 `main` 以免运行失败。
