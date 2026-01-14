# DockerMonitor 快速入門指南

5 分鐘內快速上手 DockerMonitor！

## 前置需求

- Python 3.8 或更高版本
- 可存取跳板機（Bastion Server）的 SSH 權限
- 已配置 SSH 金鑰認證
- 目標伺服器已安裝 Docker

## 1. 安裝

### Windows

```powershell
# 克隆或下載專案
cd DockerMonitor

# 執行設定腳本
.\run.bat
```

### Linux/Mac

```bash
# 克隆或下載專案
cd DockerMonitor

# 賦予執行權限並執行
chmod +x run.sh
./run.sh
```

### 手動安裝

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
```

## 2. 配置

### 複製範例配置檔

```bash
# Windows
copy config\hosts.yaml.example config\hosts.yaml
copy .env.example .env

# Linux/Mac
cp config/hosts.yaml.example config/hosts.yaml
cp .env.example .env
```

### 配置跳板機

編輯 `config/hosts.yaml`：

```yaml
jump_host:
  hostname: your-jumphost.example.com
  port: 22
  username: your_username
  key_file: ~/.ssh/id_rsa
```

### 新增目標主機

新增要監控的 Docker 主機：

```yaml
target_hosts:
  - name: prod-web-01
    hostname: 192.168.1.10
    port: 22
    username: docker_user
    key_file: ~/.ssh/id_rsa
    tags: [production, web]
    enabled: true

  - name: prod-db-01
    hostname: 192.168.1.20
    port: 22
    username: docker_user
    key_file: ~/.ssh/id_rsa
    tags: [production, database]
    enabled: true
```

### 環境變數配置（可選）

編輯 `.env` 以自訂設定：

```bash
MONITOR_INTERVAL=60
TIMEOUT=30
LOG_LEVEL=INFO
```

## 3. 驗證 SSH 存取

手動測試 SSH 配置：

```bash
# 測試跳板機連線
ssh -i ~/.ssh/id_rsa your_username@your-jumphost.example.com

# 測試透過跳板機連線至目標主機
ssh -i ~/.ssh/id_rsa -J your_username@your-jumphost.example.com docker_user@192.168.1.10
```

如果這些命令可以正常執行，DockerMonitor 應該也能正常運作！

## 4. 執行 DockerMonitor

### TUI 模式（推薦）

互動式終端介面：

```bash
python -m src.main tui
```

快捷鍵：
- `h` - 說明
- `r` - 重新整理資料
- `s` - 排序容器
- `l` - 切換語言
- `q` - 離開
- `↑/↓` - 導覽
- `Enter` - 查看詳情

### CLI 模式

以文字表格顯示狀態：

```bash
python -m src.main status
```

匯出為 JSON：

```bash
python -m src.main status --format json > status.json
```

匯出為 CSV：

```bash
python -m src.main status --format csv > containers.csv
```

依標籤篩選：

```bash
python -m src.main status --tags production
```

## 5. 疑難排解

### 連線錯誤

**問題**：無法連線至跳板機

```bash
# 啟用除錯日誌
python -m src.main --debug status

# 查看日誌
cat logs/dockermonitor_*.log
```

**解決方法**：
- 驗證 SSH 金鑰權限：`chmod 600 ~/.ssh/id_rsa`
- 手動測試 SSH（參見步驟 3）
- 檢查配置檔中的主機名稱與憑證

### 沒有顯示容器

**問題**：主機顯示已連線但沒有容器

**解決方法**：
- 驗證 Docker 正在運行：在目標主機上執行 `docker ps`
- 檢查使用者是否有 Docker 權限
- 確認配置中 `enabled: true`

### 權限被拒

**問題**：SSH 權限錯誤

**解決方法**：
- 使用金鑰認證（不使用密碼）
- 確保 SSH 金鑰已載入：`ssh-add ~/.ssh/id_rsa`
- 檢查配置中的金鑰檔案路徑

## 6. 下一步

### 自訂配置

- 在 `config/hosts.yaml` 新增更多主機
- 使用標籤依環境組織主機
- 在 `.env` 調整重新整理間隔

### 探索功能

- 查看詳細的容器資訊（在容器上按 Enter）
- 依不同欄位排序容器（按 `s`）
- 依主機篩選（在左側邊欄選擇）
- 查看頂部的統計面板

### 進階用法

參見 [README.md](README.md) 了解：
- 詳細配置選項
- 所有可用命令
- 架構細節
- 安全考量

## 常見使用案例

### 只監控生產環境

```bash
python -m src.main tui --tags production
```

### 快速健康檢查

```bash
python -m src.main status --format table
```

### 匯出供分析使用

```bash
python -m src.main status --format json --output report.json
```

### 每 30 秒自動重新整理

```bash
python -m src.main tui --interval 30
```

## 取得協助

- 在 TUI 模式按 `h` 查看說明
- 查看 [CLAUDE.md](CLAUDE.md) 了解技術細節
- 參見 [CONTRIBUTING.md](CONTRIBUTING.md) 了解開發資訊
- 在 GitHub 開啟 issue 回報問題或提問

## 成功！

您現在應該可以看到：
- 已連線的主機列表（左側邊欄）
- 所有主機上的 Docker 容器（主表格）
- 摘要統計資訊（頂部面板）
- 即時更新

按 `h` 查看快捷鍵，按 `q` 離開。

享受監控您的 Docker 容器！🐳
