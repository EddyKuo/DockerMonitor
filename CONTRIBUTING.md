# 為 DockerMonitor 做出貢獻

感謝您有興趣為 DockerMonitor 做出貢獻！

## 開始使用

1. Fork 此儲存庫
2. 克隆您的 fork：
   ```bash
   git clone https://github.com/yourusername/dockermonitor.git
   cd dockermonitor
   ```

3. 建立虛擬環境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

4. 安裝開發依賴：
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

## 開發工作流程

### 執行測試

```bash
# 執行所有測試
pytest tests/

# 執行測試並顯示覆蓋率
pytest --cov=src tests/

# 執行特定測試檔案
pytest tests/test_config.py
```

### 程式碼品質

在提交 Pull Request 之前，請確保您的程式碼通過所有檢查：

```bash
# 格式化程式碼
black src/ tests/

# 執行 linter
flake8 src/ tests/

# 型別檢查
mypy src/
```

### 執行應用程式

```bash
# 啟動 TUI
python -m src.main tui

# 獲取狀態
python -m src.main status

# 啟用除錯模式
python -m src.main --debug tui
```

## 專案結構

```
DockerMonitor/
├── src/              # 原始碼
│   ├── ssh/         # SSH 連線管理
│   ├── docker/      # Docker 監控
│   ├── aggregator/  # 資料彙整
│   ├── tui/         # Textual TUI 介面
│   └── utils/       # 工具程式
├── tests/           # 測試檔案
├── config/          # 配置檔案
└── docs/            # 文件
```

## Pull Request 指南

1. **建立功能分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **撰寫測試**：確保您的變更包含適當的測試

3. **更新文件**：如有需要，更新 README.md 和 CLAUDE.md

4. **遵循程式碼風格**：
   - 使用型別提示
   - 遵循 PEP 8
   - 為公開函式撰寫文件字串
   - 保持函式專注且精簡

5. **提交訊息**：
   - 使用清晰、描述性的提交訊息
   - 如適用，引用相關 issue
   - 範例：「新增容器表格的篩選支援 (#42)」

6. **提交 PR**：
   - 提供清晰的變更說明
   - 連結相關 issue
   - 確保所有 CI 檢查通過

## 程式碼風格

### Python 風格

- 遵循 PEP 8
- 使用型別提示
- 最大行長度：100 字元
- 使用 `black` 進行格式化

### 文件

- 為所有公開函式/類別撰寫文件字串
- 使用 Google 風格的文件字串
- 架構變更時更新 CLAUDE.md

### 文件字串範例

```python
def monitor_host(host_config: dict) -> HostStatus:
    """
    監控單一主機的 Docker 容器。

    Args:
        host_config: 包含主機配置的字典。

    Returns:
        包含監控結果的 HostStatus 物件。

    Raises:
        ConnectionError: 如果 SSH 連線失敗。
    """
    pass
```

## 測試指南

### 單元測試

- 獨立測試個別函式/類別
- 使用 pytest fixtures 進行常見設定
- Mock 外部依賴（SSH、Docker）

### 整合測試

- 測試元件互動
- 使用 `@pytest.mark.integration` 標記
- 可能需要實際的 SSH 連線（可選）

### 測試範例

```python
def test_parse_container_output(parser):
    """測試解析 Docker ps 輸出。"""
    output = '{"ID":"abc123","Names":"test"}'
    result = parser.parse_ps_output(output)

    assert len(result) == 1
    assert result[0].name == "test"
```

## 新增功能

### 新增 Widget

1. 在 `src/tui/widgets/` 建立檔案
2. 繼承 `Widget` 或適當的基礎類別
3. 定義 `DEFAULT_CSS` 用於樣式
4. 實作 `compose()` 方法
5. 加入至 `src/tui/widgets/__init__.py`
6. 在 `tests/test_widgets.py` 撰寫測試

### 新增 Docker 命令

1. 在 `src/docker/monitor.py` 新增命令
2. 在 `src/docker/parser.py` 新增解析邏輯
3. 如需要，更新配置架構
4. 撰寫測試
5. 更新文件

## 回報問題

回報問題時，請包含：

- 作業系統與版本
- Python 版本
- DockerMonitor 版本
- 重現步驟
- 預期與實際行為
- 相關日誌（來自 `logs/` 目錄）

## 功能請求

歡迎功能請求！請：

- 先檢查現有 issue
- 提供清晰的使用案例
- 說明預期行為
- 考慮實作複雜度

## 有問題？

- 開啟 issue 提出一般問題
- 查看 CLAUDE.md 了解架構細節
- 參見 README.md 了解使用說明

## 授權

透過貢獻，您同意您的貢獻將依 MIT 授權條款授權。

## 貢獻者行為準則

### 我們的承諾

為了營造開放且友善的環境，我們作為貢獻者和維護者承諾，無論年齡、體型、殘疾、族群、性別認同與表達、經驗程度、國籍、個人外貌、種族、宗教或性取向，參與我們的專案和社群對每個人都是無騷擾的體驗。

### 我們的標準

有助於建立正面環境的行為範例包括：

- 使用友善和包容的語言
- 尊重不同的觀點和經驗
- 優雅地接受建設性批評
- 專注於對社群最有利的事情
- 對其他社群成員表現同理心

### 執行

如有任何不當行為，請聯繫專案團隊。所有投訴都會被審查和調查，並將做出必要且適當的回應。

## 感謝

感謝所有貢獻者讓 DockerMonitor 變得更好！🙏
