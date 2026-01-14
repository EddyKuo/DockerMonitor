# SSH 連接策略說明 / SSH Connection Strategy

## 繁體中文

### 連接策略：臨時連接（Ephemeral Connections）

DockerMonitor 現在採用**臨時連接策略**，而非持久連接。

### 工作原理

#### 每次更新時：
1. **建立新連接** → 連接到跳板機
2. **連接所有目標主機** → 透過跳板機連接 AP1, AP2, DB1, DB2
3. **執行 Docker 命令** → 收集容器資訊
4. **關閉所有連接** ✅ → 立即斷開，不保持連接

#### 更新觸發時機：
- **自動更新**：每 60 秒（可在 `config/hosts.yaml` 調整）
- **手動更新**：按 `r` 鍵
- **首次啟動**：程式啟動時

### 時間預估

#### 每次更新需要的時間：
- **連接階段**：10-15 秒
  - 連接跳板機：3-5 秒
  - 連接 4 台目標主機：5-10 秒（並發連接）
- **資料收集**：3-5 秒
  - 執行 `docker ps` 和 `docker stats`
- **總計**：約 **15-20 秒**

### 優點 ✅

1. **不會卡住**
   - 每次都是全新連接
   - 沒有超時或斷線問題

2. **可預測性**
   - 每次更新時間一致
   - UI 回應可預期

3. **資源效率**
   - 不佔用持久連接
   - SSH 資源及時釋放

4. **更可靠**
   - 不受長時間連接超時影響
   - 自動恢復連接問題

### 缺點 ⚠️

1. **每次都需要重新連接**
   - 每次更新都需要 15-20 秒
   - 無法利用已建立的連接

2. **更多的 SSH 握手**
   - 對跳板機有更多連接請求
   - 可能觸發連接速率限制（如果有）

### 建議配置

#### 如果覺得更新太慢：

**減少監控的主機數量**（在 `config/hosts.yaml`）：
```yaml
target_hosts:
  - name: AP1
    enabled: true   # 保持啟用
  - name: AP2
    enabled: false  # 暫時停用
  - name: DB1
    enabled: false  # 暫時停用
  - name: DB2
    enabled: true   # 保持啟用
```

**增加自動更新間隔**（在 `config/hosts.yaml`）：
```yaml
monitoring:
  default_interval: 120  # 從 60 秒改為 120 秒
```

**減少連接超時時間**（在 `config/hosts.yaml`）：
```yaml
monitoring:
  command_timeout: 20  # 從 30 秒減少到 20 秒
```

**增加並發連接數**（在 `config/hosts.yaml`）：
```yaml
monitoring:
  max_concurrent_connections: 10  # 從 5 增加到 10
```

### 日誌監控

查看詳細的連接日誌：
```bash
tail -f logs/dockermonitor.log
```

您會看到：
```
Connecting to AP1...
Connected to AP1, collecting data...
Connecting to AP2...
Connected to AP2, collecting data...
...
Closing all SSH connections after refresh...
All connections closed
```

---

## English

### Connection Strategy: Ephemeral Connections

DockerMonitor now uses an **ephemeral connection strategy** instead of persistent connections.

### How It Works

#### On Each Update:
1. **Establish new connections** → Connect to jump host
2. **Connect to all targets** → Connect through jump host to AP1, AP2, DB1, DB2
3. **Execute Docker commands** → Collect container information
4. **Close all connections** ✅ → Immediately disconnect, no persistent connections

#### Update Triggers:
- **Auto-refresh**: Every 60 seconds (configurable in `config/hosts.yaml`)
- **Manual refresh**: Press `r` key
- **Initial startup**: When program starts

### Time Estimates

#### Time Required Per Update:
- **Connection Phase**: 10-15 seconds
  - Connect to jump host: 3-5 seconds
  - Connect to 4 target hosts: 5-10 seconds (concurrent)
- **Data Collection**: 3-5 seconds
  - Execute `docker ps` and `docker stats`
- **Total**: Approximately **15-20 seconds**

### Advantages ✅

1. **Won't Get Stuck**
   - Fresh connection every time
   - No timeout or disconnection issues

2. **Predictable**
   - Consistent update time
   - Predictable UI response

3. **Resource Efficient**
   - No persistent connection overhead
   - SSH resources released promptly

4. **More Reliable**
   - Not affected by long-running connection timeouts
   - Automatically recovers from connection issues

### Disadvantages ⚠️

1. **Reconnection Required Every Time**
   - Each update takes 15-20 seconds
   - Cannot leverage established connections

2. **More SSH Handshakes**
   - More connection requests to jump host
   - May trigger rate limiting (if configured)

### Recommended Configuration

#### If Updates Feel Too Slow:

**Reduce Number of Monitored Hosts** (in `config/hosts.yaml`):
```yaml
target_hosts:
  - name: AP1
    enabled: true   # Keep enabled
  - name: AP2
    enabled: false  # Temporarily disable
  - name: DB1
    enabled: false  # Temporarily disable
  - name: DB2
    enabled: true   # Keep enabled
```

**Increase Auto-Update Interval** (in `config/hosts.yaml`):
```yaml
monitoring:
  default_interval: 120  # Change from 60 to 120 seconds
```

**Reduce Connection Timeout** (in `config/hosts.yaml`):
```yaml
monitoring:
  command_timeout: 20  # Reduce from 30 to 20 seconds
```

**Increase Concurrent Connections** (in `config/hosts.yaml`):
```yaml
monitoring:
  max_concurrent_connections: 10  # Increase from 5 to 10
```

### Log Monitoring

View detailed connection logs:
```bash
tail -f logs/dockermonitor.log
```

You will see:
```
Connecting to AP1...
Connected to AP1, collecting data...
Connecting to AP2...
Connected to AP2, collecting data...
...
Closing all SSH connections after refresh...
All connections closed
```
