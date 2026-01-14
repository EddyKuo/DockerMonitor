# CLAUDE.md

此檔案為 Claude Code (claude.ai/code) 在處理此儲存庫程式碼時提供指引。

## 專案概述

**DockerMonitor** - 一個透過跳板機（Bastion Server）監控多台主機上 Docker 容器的 Python 應用程式。使用 SSH 隧道連線至私有網路主機，並執行 Docker CLI 命令以獲取容器狀態與資源使用情況。

**實作方法**：方法 A（透過 SSH 的 Docker CLI）- 遠端執行 Docker 命令並解析 JSON 輸出。

## 開發狀態

**目前階段**：第 1 階段完成 - 核心基礎設施已實作

- ✅ 配置管理系統
- ✅ 日誌系統
- ✅ SSH 隧道管理器（asyncssh）
- ✅ 遠端命令執行器
- ✅ Docker 監控核心（基於 CLI）
- ✅ Docker 輸出解析器
- ✅ 資料彙整器
- ✅ 支援多種輸出格式的 CLI 介面
- ✅ Textual TUI 介面（已完成）
- ✅ 多語言支援（繁體中文/英文）

## 建置與開發命令

### 設定

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt

# 配置應用程式
copy .env.example .env
copy config\hosts.yaml.example config\hosts.yaml
# 使用您的設定編輯 .env 和 config\hosts.yaml
```

### 執行應用程式

```bash
# 獲取所有容器狀態（表格格式）
python -m src.main status

# 依標籤篩選
python -m src.main status --tags production,web

# 輸出為 JSON
python -m src.main status --format json

# 儲存至檔案
python -m src.main status --format json --output status.json

# 匯出為 CSV
python -m src.main status --format csv --output containers.csv

# 啟用除錯日誌
python -m src.main --debug status

# 啟動 TUI
python -m src.main tui

# TUI 模式下依標籤篩選
python -m src.main tui --tags production

# 自訂重新整理間隔
python -m src.main tui --interval 30
```

### 測試

```bash
# 執行所有測試
pytest tests/

# 執行測試並顯示覆蓋率
pytest --cov=src tests/

# 執行特定測試檔案
pytest tests/test_config.py
```

### 程式碼品質

```bash
# 格式化程式碼
black src/ tests/

# Lint 程式碼
flake8 src/ tests/

# 型別檢查
mypy src/
```

## 架構概述

### 主要元件

1. **ConfigManager** (`src/utils/config.py`)
   - 載入並驗證 `config/hosts.yaml`
   - 與 `.env` 的環境變數合併
   - 提供跳板機、目標主機與監控設定的存取

2. **SSHTunnelManager** (`src/ssh/tunnel.py`)
   - 管理跳板機連線
   - 透過跳板機建立至目標主機的隧道連線
   - 處理連線池與清理
   - 使用 asyncssh 進行非同步 SSH 操作

3. **RemoteExecutor** (`src/ssh/executor.py`)
   - 透過 SSH 在遠端主機執行命令
   - 處理逾時與重試
   - 擷取 stdout/stderr 與退出狀態
   - 回傳結構化的 CommandResult 物件

4. **DockerMonitor** (`src/docker/monitor.py`)
   - 在遠端主機執行 Docker CLI 命令
   - 檢查 Docker 可用性
   - 獲取容器列表與資源統計
   - 提供主機狀態資訊

5. **DockerOutputParser** (`src/docker/parser.py`)
   - 解析 Docker CLI 命令的 JSON 輸出
   - 轉換為結構化的 ContainerInfo 物件
   - 合併容器列表與統計資料
   - 處理各種 Docker 輸出格式

6. **DataAggregator** (`src/aggregator/data.py`)
   - 彙整來自多台主機的資料
   - 格式化輸出為 JSON、CSV 或表格
   - 計算統計與摘要
   - 儲存資料至檔案

7. **TUI 介面** (`src/tui/`)
   - 基於 Textual 的互動式終端介面
   - 主機列表側邊欄
   - 容器表格（可排序、可篩選）
   - 統計面板
   - 容器詳情檢視
   - 說明系統
   - 多語言支援

8. **CLI 介面** (`src/main.py`)
   - 使用 Click 的命令列介面
   - 協調所有主機的監控
   - 提供多種輸出格式
   - 處理錯誤與日誌

### 資料流

```
ConfigManager → 載入 hosts.yaml + .env
    ↓
SSHTunnelManager → 連線至跳板機
    ↓
對於每個目標主機：
    SSHTunnelManager → 透過跳板機連線至目標
    RemoteExecutor → 執行 Docker 命令
    DockerOutputParser → 解析 JSON 輸出
    DockerMonitor → 收集容器資訊
    ↓
DataAggregator → 合併所有主機資料
    ↓
輸出（表格/JSON/CSV）
```

### 外部依賴

- **asyncssh**: 非同步 SSH 客戶端函式庫
- **PyYAML**: YAML 配置檔案解析
- **click**: CLI 框架
- **rich**: 終端格式化與表格
- **textual**: TUI 框架
- **python-dotenv**: 環境變數管理

## Docker 整合

**方法 A：透過 SSH 的 Docker CLI**（目前實作）

- 透過 SSH 執行 `docker ps`、`docker stats`、`docker inspect` 命令
- 使用 `--format '{{json .}}'` 解析 JSON 輸出
- 不需要開放 Docker API
- 更安全，因為使用標準 SSH 認證
- 從 JSON 格式輸出解析容器資訊

**使用的 Docker 命令：**
```bash
# 列出所有容器
docker ps -a --format '{{json .}}'

# 列出運行中的容器
docker ps --format '{{json .}}'

# 獲取資源使用統計
docker stats --no-stream --format '{{json .}}'

# 獲取詳細容器資訊
docker inspect <container_id>

# 檢查 Docker 版本
docker --version
```

## 配置

### config/hosts.yaml

定義跳板機與目標伺服器：

```yaml
jump_host:
  hostname: jump.example.com
  port: 22
  username: your_username
  key_file: ~/.ssh/id_rsa

target_hosts:
  - name: prod-web-01
    hostname: 192.168.1.10
    port: 22
    username: docker_user
    key_file: ~/.ssh/id_rsa
    description: "生產環境 Web 伺服器"
    tags: [production, web]
    enabled: true

monitoring:
  command_timeout: 30
  max_retries: 3
  retry_delay: 5
  max_concurrent_connections: 5

docker:
  docker_bin: /usr/bin/docker
```

### .env

執行時配置的環境變數：

```bash
# 跳板機（覆寫 hosts.yaml）
JUMP_HOST=jump.example.com
JUMP_USER=your_username
JUMP_KEY_PATH=~/.ssh/id_rsa

# 監控設定
MONITOR_INTERVAL=60
TIMEOUT=30
MAX_WORKERS=5

# 輸出
OUTPUT_FORMAT=table
LOG_LEVEL=INFO
DEBUG=false

# 語言
LANGUAGE=zh_TW
```

## 未來開發注意事項

### 下一步（第 2-5 階段）

- [x] 實作 Textual TUI 介面：
  - 主機列表側邊欄
  - 可排序/篩選的容器表格
  - 即時更新
  - 鍵盤快捷鍵
  - 狀態列與統計面板

- [ ] 新增告警功能：
  - 容器停止告警
  - 高 CPU/記憶體使用告警
  - Email/Slack 通知

- [ ] 新增歷史資料：
  - 儲存監控結果
  - 趨勢分析
  - 效能圖表

### 設計決策

1. **為何選擇 asyncssh 而非 paramiko？**
   - 原生 asyncio 支援，可並發監控
   - 多主機效能更佳
   - 更簡潔的 async/await 語法

2. **為何選擇方法 A（Docker CLI）而非 Docker API？**
   - 更安全（無需開放 Docker API）
   - 設定更簡單（只需 SSH 存取）
   - 與基於 SSH 的架構一致

3. **為何選擇 Textual 作為 TUI？**
   - 現代化的 Python TUI 框架
   - 原生 asyncio 支援
   - 豐富的 widget 函式庫
   - CSS-like 樣式設定

4. **為何使用臨時連線策略？**
   - 避免長時間連線逾時問題
   - 更可預測的行為
   - 資源及時釋放
   - 自動恢復連線問題

### 常見開發任務

**新增主機：**
1. 編輯 `config/hosts.yaml`
2. 在 `target_hosts` 列表新增項目
3. 執行 `python -m src.main status` 驗證

**新增 Docker 命令：**
1. 在 `src/docker/monitor.py` 新增方法
2. 如需要，在 `DockerOutputParser` 新增解析邏輯
3. 撰寫測試

**除錯連線問題：**
```bash
# 啟用除錯日誌
python -m src.main --debug status

# 檢查日誌
cat logs/dockermonitor_*.log

# 手動測試 SSH 連線
ssh -i ~/.ssh/id_rsa user@jump.example.com
```

**TUI 模式除錯：**
```bash
# TUI 模式下日誌只寫入檔案，不輸出至終端
python -m src.main --debug tui

# 查看日誌檔案
tail -f logs/dockermonitor_*.log
```

### 程式碼風格指南

- 所有函式簽章使用型別提示
- 使用 dataclass 處理結構化資料
- 保持函式精簡且專注
- I/O 操作使用 async/await
- 記錄重要事件與錯誤
- 優雅地處理例外

### 重要實作細節

**連線管理：**
- 每次重新整理建立新連線
- 完成後立即關閉所有連線
- 避免連線池堆積
- 錯誤處理與重試機制

**日誌系統：**
- TUI 模式：日誌只寫入檔案（`console_enabled=False`）
- CLI 模式：日誌輸出至終端與檔案
- 除錯模式：詳細日誌記錄

**多語言支援：**
- 翻譯檔案位於 `locales/` 目錄
- 支援繁體中文（zh_TW）與英文（en）
- 執行時可透過 `l` 鍵切換語言
- 使用 YAML 格式的翻譯檔案

## 疑難排解

### 常見問題

1. **TUI 畫面被日誌覆蓋**
   - 已修正：TUI 模式下停用 console 日誌
   - 日誌只寫入 `logs/` 目錄

2. **CPU/記憶體資料未顯示**
   - 已修正：啟用 `with_stats=True`
   - 現在會正確執行 `docker stats`

3. **重新整理訊息不消失**
   - 已修正：資料更新後自動清除狀態訊息

### 效能優化

- 調整 `max_concurrent_connections` 控制並發數
- 增加 `command_timeout` 避免逾時
- 使用標籤篩選減少監控主機數量
- 調整 `refresh_interval` 降低更新頻率

## 版本歷史

- **v0.1.1** (2026-01-14): 修正 TUI 問題、CPU/記憶體統計
- **v0.1.0** (2026-01-13): 初始版本，完整 TUI 與 CLI 功能
- **v0.0.1** (2026-01-13): 專案結構建立

---

**最後更新**: 2026-01-14
**維護者**: DockerMonitor Team
