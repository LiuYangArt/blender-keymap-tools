# Keymap Tools 设计文档

## 背景
Blender 的 keymap 不是唯一快捷键表，而是由 `keyconfig -> keymap -> keymap_item` 多层叠加组成。同一个 operator 可以在不同 context、不同属性参数、不同 modal 状态下绑定多组快捷键。因此本插件不试图替代 Blender 原生系统，而是提供清理、诊断、预览能力。

## 目标
- 清理导入 keymap preset 后产生的完全重复条目。
- 在设置快捷键前检查当前 context 下的冲突。
- 显示当前 keymap 中常用键位的占用情况。
- 输出可读日志，方便 agent 或开发者复现、验证和继续排查。

## 非目标
- MVP 阶段不替代 Blender 的 keymap preset 导入流程。
- 不强制保证一个功能只能有一个快捷键，因为 Blender 原生允许多绑定。
- 不处理任意 preset Python 脚本的执行语义，只处理导入后的当前 keyconfig 状态。

## 冲突分级
- `Exact Duplicate`：同一 keymap、同一 operator、同一快捷键、同一 modifier、同一 properties。通常可安全删除重复项。
- `Same Hotkey Same Context`：同一 keymap 中同一快捷键触发多个不同 operator。高风险，需要人工确认。
- `Same Operator Different Hotkey`：同一 operator 有多个快捷键。通常合法，只提示。
- `Same Hotkey Different Context`：不同 keymap/context 复用同一快捷键。通常合法，但需要显示作用范围。
- `Modal Conflict`：modal keymap 内部冲突，单独标记，不和普通全局快捷键混判。

## MVP 功能
1. `Scan Exact Duplicates`
   扫描当前 active keyconfig，按签名聚合完全重复 keymap item，并把结果打印到控制台。

2. `Remove Exact Duplicates`
   删除完全重复项，每组保留第一个 active item。执行前后报告删除数量。

3. `Check Hotkey Conflict`
   根据 UI 中的 keymap 名和按键组合，列出当前 context 下所有匹配 item。

4. `List Available Keys`
   对字母、数字、F 键和常见 modifier 组合做可用性粗筛，输出 free / occupied 数量。

## 数据签名
Exact Duplicate 使用以下字段建立签名：
- keymap name
- modal flag
- operator idname
- operator properties
- event type / value
- modifier：ctrl / shift / alt / oskey
- key_modifier
- map_type
- direction
- repeat



## 项目结构
- `__init__.py`：插件入口，只调用 `auto_load`。
- `auto_load.py`：自动发现并注册 Blender class。
- `functions/`：纯扫描和分析逻辑。
- `properties/`：UI 参数和 WindowManager 属性挂载。
- `operators/`：扫描、删除、冲突检查、可用键位操作。
- `panels/`：View3D Sidebar 面板。
- `scripts/`：本地校验和打包脚本。

## 后续迭代
- 导入 preset 前的 dry-run diff。
- operator 相同但 properties 不同的差异解释。
- context 优先级建模，区分真实遮挡和合法复用。
- 将扫描结果写入 JSON artifact，供自动化测试和 agent 读取。
- 做快捷键矩阵 UI，而不是只输出文本列表。