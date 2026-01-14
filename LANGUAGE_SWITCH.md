# 語言切換功能說明 / Language Switching Guide

## 繁體中文

### 功能說明
DockerMonitor 現在支援多語言介面！您可以在運行時動態切換語言。

### 支援的語言
- **繁體中文** (`zh_TW`)
- **English** (`en`)

### 如何切換語言

#### 方法 1: 在 TUI 中使用快捷鍵
執行 TUI 後，按 **`l`** 鍵即可切換語言：
```bash
python -m src.main tui
```
- 按一次 `l` → 從繁體中文切換到 English
- 再按一次 `l` → 從 English 切換回繁體中文

#### 方法 2: 修改配置檔案
在 `config/hosts.yaml` 中設定預設語言：
```yaml
app:
  locale: zh_TW  # 繁體中文
  # 或
  locale: en     # English
```

#### 方法 3: 使用環境變數
```bash
# 使用英文
export LOCALE=en
python -m src.main tui

# 使用繁體中文
export LOCALE=zh_TW
python -m src.main tui
```

### 快捷鍵列表
- `h` - 顯示說明
- `r` - 重新整理資料
- `l` - **切換語言** ⭐ 新功能！
- `s` - 切換排序
- `q` - 離開程式

### 翻譯涵蓋範圍
所有 UI 元素都已完整翻譯：
- ✅ 主機列表
- ✅ 容器表格（包括所有欄位）
- ✅ 統計面板
- ✅ 狀態列
- ✅ 詳細資訊畫面
- ✅ 所有通知訊息
- ✅ 按鈕和提示文字

---

## English

### Overview
DockerMonitor now supports multi-language interface! You can dynamically switch languages at runtime.

### Supported Languages
- **Traditional Chinese** (`zh_TW`)
- **English** (`en`)

### How to Switch Language

#### Method 1: Use Keyboard Shortcut in TUI
After launching the TUI, press **`l`** key to switch language:
```bash
python -m src.main tui
```
- Press `l` once → Switch from Traditional Chinese to English
- Press `l` again → Switch from English back to Traditional Chinese

#### Method 2: Modify Configuration File
Set default language in `config/hosts.yaml`:
```yaml
app:
  locale: zh_TW  # Traditional Chinese
  # or
  locale: en     # English
```

#### Method 3: Use Environment Variable
```bash
# Use English
export LOCALE=en
python -m src.main tui

# Use Traditional Chinese
export LOCALE=zh_TW
python -m src.main tui
```

### Keyboard Shortcuts
- `h` - Show help
- `r` - Refresh data
- `l` - **Switch language** ⭐ New feature!
- `s` - Cycle sort
- `q` - Quit

### Translation Coverage
All UI elements are fully translated:
- ✅ Host list
- ✅ Container table (all columns)
- ✅ Statistics panel
- ✅ Status bar
- ✅ Detail screen
- ✅ All notification messages
- ✅ Buttons and tooltips
