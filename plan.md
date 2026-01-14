# DockerMonitor - 實作計劃

## 專案目標

建立一個 Python 應用程式，透過跳板機 (Jump Host) 連接到內部私有網路中的多台機器，監控並取得各機器上 Docker 容器的運作狀態。

## 架構設計

### 1. 連線架構

```
Local Machine (DockerMonitor)
    ↓ SSH
Jump Host (跳板機)
    ↓ SSH (多重連線)
├─ Server 1 (Private Network)
├─ Server 2 (Private Network)
└─ Server N (Private Network)
```

### 2. 技術堆疊

- **語言**: Python 3.8+
- **使用者介面**: `Textual` - 現代化的純文字終端介面 (TUI)
- **SSH 連線**: `asyncssh` (推薦，與 Textual 都支援 asyncio)
- **並發處理**: `asyncio` (Textual 和 asyncssh 原生支援)
- **Docker API**: 透過 SSH 執行 Docker CLI 指令 (方案 A)
- **資料處理**: `pandas` (可選，用於資料整理)
- **配置管理**: `python-dotenv` + `PyYAML`
- **日誌**: `logging` 模組

### 3. 核心元件

#### 3.1 SSH 連線管理器 (SSHTunnelManager)
- 建立與跳板機的 SSH 連線
- 管理連線池
- 支援 SSH Key 認證
- 自動重連機制

#### 3.2 主機管理器 (HostManager)
- 管理目標主機清單
- 透過跳板機建立到各主機的 SSH 連線
- 支援批次操作

#### 3.3 Docker 監控器 (DockerMonitor)
- 執行 Docker 指令 (docker ps, docker stats, docker inspect)
- 解析 Docker 輸出
- 收集容器狀態資訊

#### 3.4 資料聚合器 (DataAggregator)
- 彙整多台主機的 Docker 資訊
- 格式化輸出 (JSON, CSV, 表格)
- 狀態統計與分析

#### 3.5 配置管理器 (ConfigManager)
- 讀取配置檔案 (跳板機資訊、目標主機列表)
- 管理 SSH 認證資訊
- 環境變數處理

#### 3.6 Textual TUI 介面 (TextualApp)
- 即時顯示多主機 Docker 容器狀態
- 互動式操作介面 (鍵盤導航、篩選、排序)
- 分頁顯示不同主機資訊
- 即時更新容器狀態與資源使用
- 狀態視覺化 (顏色標示運行/停止狀態)

## 專案結構

```
DockerMonitor/
├── config/
│   ├── hosts.yaml           # 主機配置檔案
│   └── settings.yaml        # 應用程式設定
├── src/
│   ├── __init__.py
│   ├── main.py             # 程式進入點 (啟動 TUI)
│   ├── ssh/
│   │   ├── __init__.py
│   │   ├── tunnel.py       # SSH 跳板機連線
│   │   └── executor.py     # 遠端指令執行
│   ├── docker/
│   │   ├── __init__.py
│   │   ├── monitor.py      # Docker 監控核心
│   │   └── parser.py       # Docker 輸出解析
│   ├── aggregator/
│   │   ├── __init__.py
│   │   └── data.py         # 資料彙整
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py          # Textual 主應用程式
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── host_list.py      # 主機列表 Widget
│   │   │   ├── container_table.py # 容器列表表格
│   │   │   ├── status_bar.py     # 狀態列
│   │   │   └── stats_panel.py    # 統計資訊面板
│   │   ├── screens/
│   │   │   ├── __init__.py
│   │   │   ├── main_screen.py    # 主畫面
│   │   │   ├── detail_screen.py  # 容器詳細資訊畫面
│   │   │   └── settings_screen.py # 設定畫面
│   │   └── styles.css        # Textual CSS 樣式
│   └── utils/
│       ├── __init__.py
│       ├── config.py       # 配置讀取
│       └── logger.py       # 日誌設定
├── tests/
│   ├── test_ssh.py
│   ├── test_docker.py
│   ├── test_aggregator.py
│   └── test_tui.py
├── .env.example            # 環境變數範例
├── requirements.txt        # Python 依賴
├── README.md
├── CLAUDE.md
└── plan.md                 # 本文件
```

## 配置檔案範例

### config/hosts.yaml
```yaml
jump_host:
  hostname: jump.example.com
  port: 22
  username: your_username
  key_file: ~/.ssh/id_rsa

target_hosts:
  - name: server-1
    hostname: 192.168.1.10
    port: 22
    username: docker_user
    key_file: ~/.ssh/id_rsa

  - name: server-2
    hostname: 192.168.1.11
    port: 22
    username: docker_user
    key_file: ~/.ssh/id_rsa
```

### .env
```bash
# Jump Host Configuration
JUMP_HOST=jump.example.com
JUMP_USER=your_username
JUMP_KEY_PATH=~/.ssh/id_rsa

# Monitoring Settings
MONITOR_INTERVAL=60
TIMEOUT=30
MAX_WORKERS=10

# Output Settings
OUTPUT_FORMAT=json  # json, table, csv
LOG_LEVEL=INFO
```

## 實作階段

### Phase 1: 基礎設施 (Week 1)
- [x] 專案結構建立
- [ ] 配置管理系統 (ConfigManager)
- [ ] 日誌系統設置
- [ ] SSH 基礎連線功能 (連接跳板機)
- [ ] 單元測試框架

### Phase 2: SSH 隧道與遠端執行 (Week 1-2)
- [ ] SSH 跳板機連線管理
- [ ] 透過跳板機連接內網主機
- [ ] 遠端指令執行器
- [ ] 連線池管理
- [ ] 錯誤處理與重連機制

### Phase 3: Docker 監控功能 (Week 2)
- [ ] Docker 指令執行封裝
  - `docker ps` - 列出容器
  - `docker stats --no-stream` - 資源使用
  - `docker inspect` - 容器詳細資訊
- [ ] Docker 輸出解析器
- [ ] 容器狀態資料結構定義
- [ ] 基本監控功能測試

### Phase 4: 資料聚合與輸出 (Week 3)
- [ ] 多主機並發監控
- [ ] 資料彙整與格式化
- [ ] 多種輸出格式支援 (JSON, Table, CSV)
- [ ] 統計分析功能 (總容器數、運行/停止狀態等)

### Phase 5: Textual TUI 介面開發 (Week 3-4)
- [ ] Textual 應用程式架構設置
- [ ] 主畫面佈局設計 (Header, Sidebar, Content, Footer)
- [ ] 核心 Widgets 開發
  - [ ] 主機列表 Widget (可選擇、顯示連線狀態)
  - [ ] 容器表格 Widget (支援排序、篩選)
  - [ ] 狀態列 Widget (顯示總計資訊、更新時間)
  - [ ] 統計面板 Widget (圖表、資源使用)
- [ ] 多畫面導航系統
  - [ ] 主監控畫面
  - [ ] 容器詳細資訊畫面
  - [ ] 設定畫面
- [ ] 鍵盤快捷鍵綁定 (h: 說明, q: 離開, r: 重新整理等)
- [ ] 即時資料更新機制 (背景任務)
- [ ] 顏色主題與樣式 (CSS)
- [ ] 錯誤處理與使用者提示
- [ ] 效能優化 (大量容器時的顯示效能)
- [ ] 文件撰寫 (README, 使用說明)

## 核心功能需求

### 必要功能 (MVP)
1. ✅ 透過跳板機建立 SSH 連線
2. ✅ 連接到內網多台主機
3. ✅ 取得各主機 Docker 容器列表
4. ✅ 顯示容器狀態 (運行中/停止)
5. ✅ 基本錯誤處理

### 進階功能
6. 容器資源使用監控 (CPU, Memory)
7. 定時自動監控
8. 狀態變化告警
9. Web Dashboard (可選)
10. 歷史資料記錄

## 關鍵技術決策

### 1. SSH 函式庫選擇
**推薦: asyncssh**
- 優點: 原生支援 asyncio，效能好，API 現代化
- 適合: 需要同時監控多台主機的場景

**替代: paramiko**
- 優點: 成熟穩定，社群支援好
- 適合: 簡單的同步場景

### 2. 並發策略
- 使用 `asyncio` 實現非同步並發
- 限制同時連線數量 (使用 Semaphore)
- 避免跳板機負載過高

### 3. Docker 資料收集方式

**方式 A: Docker CLI** (推薦用於 MVP)
```python
# 透過 SSH 執行
ssh.run("docker ps --format '{{json .}}'")
```
- 優點: 簡單直接，不需額外設置
- 缺點: 解析文字輸出

**方式 B: Docker API over SSH Tunnel**
```python
# 建立 SSH Tunnel 然後使用 docker-py
tunnel = ssh.create_tunnel(2375, 'localhost', 2375)
client = docker.DockerClient(base_url='tcp://localhost:2375')
```
- 優點: 結構化資料，功能完整
- 缺點: 需要 Docker API 開放

### 4. 使用者介面設計 - Textual TUI

**選擇 Textual 的理由:**
- 純文字介面，適合 SSH 遠端操作
- 現代化的 Python TUI 框架，支援 asyncio
- 豐富的 Widget 元件與 CSS 樣式系統
- 優秀的效能與即時更新能力
- 易於測試與維護

**TUI 介面架構:**

```
┌─────────────────────────────────────────────────────────────┐
│  DockerMonitor v1.0              [Connected]  2026-01-13    │  ← Header
├──────────┬──────────────────────────────────────────────────┤
│ Hosts    │  Container Status - prod-web-01                  │
│          │  ┌────────────────────────────────────────────┐  │
│ ● prod-  │  │ NAME      IMAGE    STATUS   CPU   MEMORY  │  │
│   web-01 │  │ nginx     nginx:.. Up 2d    2%    128MB   │  │
│ ● prod-  │  │ webapp    app:1.0  Up 5h    45%   512MB   │  │  ← Content
│   api-01 │  │ redis     redis:.. Up 10d   1%    64MB    │  │     Area
│ ○ prod-  │  └────────────────────────────────────────────┘  │
│   db-01  │                                                   │
│ ● prod-  │  Statistics:                                     │
│   cache  │  Total Containers: 24  Running: 20  Stopped: 4  │
│          │  Total CPU: 45%   Total Memory: 4.2GB / 16GB    │
├──────────┴──────────────────────────────────────────────────┤
│ [h] Help  [r] Refresh  [f] Filter  [s] Sort  [q] Quit       │  ← Footer
└─────────────────────────────────────────────────────────────┘
```

**主要 Widgets:**

1. **HostListWidget** (左側邊欄)
   - 顯示所有主機列表
   - 連線狀態指示 (● 連線中, ○ 斷線)
   - 支援上下鍵選擇主機
   - 顯示每台主機的容器數量

2. **ContainerTableWidget** (主內容區)
   - DataTable 顯示容器列表
   - 支援欄位排序 (點擊欄位標題)
   - 顏色標示狀態 (綠色: Running, 紅色: Exited, 黃色: Paused)
   - 支援篩選功能 (按名稱、狀態)
   - 可捲動瀏覽大量容器

3. **StatsPanelWidget** (統計面板)
   - 顯示總計統計資訊
   - CPU/Memory 使用率進度條
   - 容器狀態分佈圖

4. **StatusBarWidget** (底部狀態列)
   - 快捷鍵提示
   - 最後更新時間
   - 連線狀態

**鍵盤快捷鍵:**
- `h` - 顯示說明畫面
- `q` - 離開程式
- `r` - 手動刷新資料
- `f` - 開啟篩選對話框
- `s` - 切換排序方式
- `Tab` - 切換焦點 Widget
- `Enter` - 查看容器詳細資訊
- `↑/↓` - 上下移動選擇
- `←/→` - 切換主機

**即時更新機制:**
```python
# 使用 Textual 的 set_interval 實現定時更新
class DockerMonitorApp(App):
    def on_mount(self):
        # 每 60 秒自動刷新資料
        self.set_interval(60, self.refresh_data)

    async def refresh_data(self):
        # 非同步獲取最新容器狀態
        containers = await self.monitor.get_all_containers()
        # 更新 UI
        self.query_one(ContainerTable).update(containers)
```

## 安全考量

1. **SSH Key 管理**
   - 使用 SSH Key 而非密碼
   - 設定適當的檔案權限 (600)
   - 考慮使用 ssh-agent

2. **憑證保護**
   - 敏感資訊不寫入版本控制
   - 使用 .env 檔案
   - 考慮使用密鑰管理工具 (如 HashiCorp Vault)

3. **網路安全**
   - 限制跳板機存取權限
   - 使用最小權限原則
   - 記錄所有連線活動

## 範例使用方式

### Textual TUI 模式 (主要使用方式)

```bash
# 啟動 TUI 介面 (預設模式)
python src/main.py

# 或明確指定 TUI 模式
python src/main.py tui

# 指定配置檔案
python src/main.py --config config/hosts.yaml

# 自訂更新間隔 (秒)
python src/main.py --interval 30

# 只監控特定標籤的主機
python src/main.py --tags production,web

# 啟用除錯模式
python src/main.py --debug
```

### CLI 模式 (輸出資料用)

```bash
# 輸出 JSON 格式 (用於其他工具處理)
python src/main.py export --format json > docker_status.json

# 輸出 CSV 格式
python src/main.py export --format csv > docker_status.csv

# 只輸出特定主機
python src/main.py export --hosts prod-web-01,prod-api-01

# 只輸出運行中的容器
python src/main.py export --status running

# 快速檢查所有主機狀態 (表格輸出)
python src/main.py status
```

### TUI 互動操作

程式啟動後，可使用以下快捷鍵：

- `h` - 顯示完整說明
- `q` 或 `Ctrl+C` - 離開程式
- `r` - 立即刷新所有資料
- `f` - 開啟篩選對話框
- `s` - 切換排序欄位
- `Tab` - 在不同區域間切換焦點
- `Enter` - 查看選中容器的詳細資訊
- `↑/↓` - 在列表中上下移動
- `←/→` - 切換不同主機
- `Space` - 標記/取消標記容器
- `/` - 快速搜尋

## 下一步行動

1. ✅ 審閱此計劃文件
2. ✅ 建立 hosts.yaml 配置檔案
3. 確認跳板機與目標主機的連線資訊
4. 準備 SSH Key 與權限設定
5. 建立 requirements.txt 並安裝依賴套件
6. 開始 Phase 1 實作 (配置管理與 SSH 連線)
7. 更新 CLAUDE.md 文件與專案資訊

## 參考資源

### 核心技術文件
- [Textual Documentation](https://textual.textualize.io/) - Textual TUI 框架官方文件
- [Textual Widget Gallery](https://textual.textualize.io/widget_gallery/) - 預建 Widget 範例
- [AsyncSSH Documentation](https://asyncssh.readthedocs.io/) - AsyncSSH 完整文件
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/) - Docker 指令參考

### 相關範例與教學
- [Textual Examples](https://github.com/Textualize/textual/tree/main/examples) - 官方範例程式
- [Building TUIs with Textual](https://www.textualize.io/blog/) - Textual 官方部落格
- [AsyncSSH Examples](https://asyncssh.readthedocs.io/en/latest/#client-examples) - SSH 客戶端範例

### 其他工具
- [Rich](https://rich.readthedocs.io/) - 終端機格式化輸出 (Textual 內建支援)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation) - YAML 解析

---

**建立日期**: 2026-01-13
**最後更新**: 2026-01-13
**版本**: 1.1 (新增 Textual TUI 設計)
