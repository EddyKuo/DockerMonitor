# 更新日誌

DockerMonitor 的所有重要變更都會記錄在此檔案中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
本專案遵循[語意化版本](https://semver.org/lang/zh-TW/)。

## [未發布]

### 計劃功能
- 容器篩選與搜尋
- 歷史資料追蹤
- 告警通知（Email/Slack）
- 匯出排程報告
- 容器日誌檢視器
- 資源使用圖表
- 多使用者支援
- Web 儀表板（可選）

## [0.1.1] - 2026-01-14

### 修正

#### TUI 介面
- 修正 TUI 模式下日誌輸出干擾畫面的問題
  - 在 TUI 模式下停用 console 日誌處理器
  - 日誌僅寫入檔案，不輸出至終端
  - 解決按 `r` 重新整理時畫面被日誌覆蓋的問題

- 修正重新整理後狀態訊息未清除的問題
  - 資料更新完成後自動清除「正在重新整理資料」訊息
  - 改善使用者體驗

- 優化離開時的日誌輸出
  - 移除不必要的除錯警告訊息
  - 簡化 `on_unmount()` 的日誌輸出
  - 清理過程中的錯誤會被靜默處理

#### Docker 監控
- 修正 CPU 與記憶體統計資料未顯示的問題
  - 將 `get_containers()` 的 `with_stats` 參數改為 `True`
  - 現在會正確執行 `docker stats` 命令獲取資源使用率
  - CPU 與記憶體欄位正常顯示數據

### 技術細節
- 更新 `src/utils/logger.py` 新增 `console_enabled` 參數
- 更新 `src/main.py` 在 TUI 模式下禁用 console 日誌
- 更新 `src/tui/app.py` 在資料更新後清除狀態訊息
- 更新 `src/docker/monitor.py` 啟用統計資料收集

## [0.1.0] - 2026-01-13

### 新增

#### 核心功能
- 透過跳板機的 SSH 隧道管理
- 非同步監控多台 Docker 主機
- Docker CLI 整合（方法 A - 無需 Docker API）
- 容器狀態收集與彙整
- 即時資源使用監控（CPU、記憶體）

#### TUI 介面
- 基於 Textual 的互動式終端介面
- 主機列表側邊欄與連線狀態
- 可排序與篩選的容器表格
- 統計面板與摘要資訊
- 狀態列與快捷鍵提示
- 說明畫面與文件
- 容器詳情檢視
- 即時自動重新整理
- 鍵盤導覽與快捷鍵

#### CLI 介面
- status 命令支援多種輸出格式（表格、JSON、CSV）
- 基於標籤的主機篩選
- 匯出至檔案
- 除錯模式

#### 配置
- 基於 YAML 的配置（hosts.yaml）
- 環境變數支援（.env）
- 主機標籤系統
- 啟用/停用個別主機
- 可自訂的監控參數

#### 開發
- 完整的測試套件（pytest）
- 整個程式碼庫的型別提示
- 檔案與主控台輸出的日誌系統
- 程式碼格式化（black）
- Linting（flake8、mypy）
- 常用任務的 Makefile
- Windows 與 Linux/Mac 執行腳本

#### 文件
- README.md 包含完整使用說明
- QUICKSTART.md 快速設定指南
- CLAUDE.md 技術架構說明
- CONTRIBUTING.md 開發者指南
- 範例配置檔案
- 應用程式內建說明系統

### 技術細節

**依賴套件：**
- Python 3.8+
- Textual 0.47+（TUI 框架）
- AsyncSSH 2.14+（SSH 客戶端）
- PyYAML 6.0+（配置）
- Click 8.1+（CLI 框架）
- Rich 13.7+（終端格式化）

**架構：**
- 使用 asyncio 的非同步 I/O
- 清晰關注點分離的模組化設計
- SSH 連線池與重用
- 優雅的錯誤處理與恢復
- Docker CLI 輸出解析（JSON 格式）

**支援平台：**
- Windows 10/11
- Linux（Ubuntu、Debian、CentOS 等）
- macOS

**安全性：**
- 基於 SSH 金鑰的認證
- 配置中不儲存密碼
- 跳板機隔離
- 最小必要權限
- 連線日誌記錄

## [0.0.1] - 2026-01-13

### 初始發布
- 建立專案結構
- 基本概念驗證

---

## 發布說明

### 版本 0.1.1 重點

此版本主要修正 TUI 使用體驗問題：

**主要修正：**
- 🐛 修正日誌輸出干擾 TUI 畫面
- 🐛 修正 CPU/記憶體資料未顯示
- 🐛 修正狀態訊息未清除
- ✨ 優化離開時的日誌輸出

這些修正大幅改善了 TUI 模式的使用體驗，讓介面更加穩定流暢。

### 版本 0.1.0 重點

這是 DockerMonitor 的第一個功能版本！🎉

主要功能：
- **完整功能的 TUI**：美觀的互動式終端介面
- **多主機監控**：監控無限數量的 Docker 主機
- **跳板機支援**：透過堡壘伺服器安全存取
- **即時更新**：可配置間隔的自動重新整理
- **多種格式**：匯出資料為 JSON、CSV 或表格
- **基於標籤的篩選**：依環境或角色組織主機

此版本專注於核心監控功能與使用者體驗。
所有 Docker 容器監控的必要功能都已實作。

### 遷移指南

#### 從 0.1.0 升級至 0.1.1

無需特殊遷移步驟，只需：

```bash
git pull origin main
pip install -r requirements.txt
```

所有配置檔案保持相容。

#### 首次安裝

這是第一個穩定版本 - 無需遷移！

### 已知問題

- 搜尋/篩選對話框尚未實作（計劃於 0.2.0 推出）
- 容器日誌檢視器尚未提供
- 歷史資料追蹤計劃於未來版本推出

### 升級指示

```bash
# 更新程式碼
git pull origin main

# 更新依賴套件
pip install -r requirements.txt

# 重新啟動應用程式
python -m src.main tui
```

---

[未發布]: https://github.com/yourusername/dockermonitor/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/yourusername/dockermonitor/releases/tag/v0.1.1
[0.1.0]: https://github.com/yourusername/dockermonitor/releases/tag/v0.1.0
[0.0.1]: https://github.com/yourusername/dockermonitor/releases/tag/v0.0.1
