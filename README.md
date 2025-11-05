# Survey AI Agent for Google ADK

這是符合 Google ADK (Agent Development Kit) 格式的 Survey AI Agent，可以通過 `adk web` 啟動並提供 Web UI 界面。

## 功能

這個 ADK Agent 提供了以下功能：

- **問卷設計器 (Survey Designer)**: 智能問卷生成系統，能根據主題和目標受眾自動設計問卷結構和問題內容。詳細使用說明請參考 [問卷設計器指南](guide_agent_designer.md)

- **答案收集器 (Answer Collector)**: 自動化答案收集和處理系統，支援多種回應格式和數據驗證功能。詳細使用說明請參考 [答案收集器指南](guide_agent_answercollector.md)

## 安裝和配置

### 1. 安裝依賴

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 2. 環境變數設置

創建 `.env` 文件（在項目根目錄）並設置以下環境變數。您可以參考 `env-example` 文件作為模板：

```env
# Google Gemini API 配置（必需）
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=512

# Google Sheets API 配置（可選，如果需要寫入 Google Sheets）
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_drive_folder_id
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
DEFAULT_SHEET_NAME=Survey_Responses
DATA_RANGE=A:Z

# 問卷配置
LOCAL_SURVEY_DIRECTORY=your_survey_directory
LOCAL_SURVEY_ID=your_survey_id
LOCAL_RESPONSE_DIRECTORY=your_response_directory
DEFAULT_QUESTION_COUNT=3
MAX_CONVERSATION_HISTORY=10
ANSWER_VALIDATION_TIMEOUT=30

# 日誌配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 開發配置
DEBUG=False
ENVIRONMENT=test
```

#### 必需配置

- `GEMINI_API_KEY`: Google Gemini API 金鑰（必需）

#### Google Sheets 配置

如果您需要將問卷結果寫入 Google Sheets，請配置以下項目：

- `GOOGLE_SHEETS_CREDENTIALS_PATH`: Google Sheets API 認證文件路徑
- `GOOGLE_DRIVE_FOLDER_ID`: Google Drive 資料夾 ID
- `GOOGLE_SPREADSHEET_ID`: Google Sheets 試算表 ID

#### 其他配置說明

- `GEMINI_MODEL`: 使用的 Gemini 模型版本（預設：gemini-2.5-flash-lite）
- `GEMINI_TEMPERATURE`: AI 回應的創意程度（0.0-1.0，預設：0.7）
- `GEMINI_MAX_TOKENS`: 最大回應長度（預設：512）
- `DEFAULT_QUESTION_COUNT`: 預設問題數量（預設：3）
- `LOCAL_SURVEY_DIRECTORY`: 本地問卷存儲目錄（預設：survey）
- `LOCAL_RESPONSE_DIRECTORY`: 本地回應存儲目錄（預設：response）


## 啟動 Agent

### 使用 ADK Web UI

在根目錄執行：

```bash
adk web --port 9000 agents/
```

這將啟動 ADK 開發工具界面，您可以在瀏覽器中與 Survey Agent 進行交互。

## 架構說明

### 系統概覽

這個 ADK Agent 系統是一個智能問卷管理平台，整合了問卷設計、數據收集、處理和輸出的完整工作流程。系統採用模組化設計，每個組件都有明確的職責分工。

### 核心模組架構

#### 1. 代理層 (Agents)
- **`agents.question_designer`**: 智能問卷設計器，負責根據需求生成問卷結構
- **`agents.survey_templates`**: 問卷模板管理，提供預設模板和自定義模板功能

#### 2. 服務層 (Services)
- **`module.services.sheet_writer`**: Google Sheets 整合服務，負責數據輸出和同步
- **`module.services.data_formatter`**: 數據格式化服務，處理不同格式間的轉換
- **`module.services.local_survey_handle`**: 本地問卷處理服務，管理問卷的存儲和檢索

#### 3. 模型層 (Models)
- **`modlue.models.survey_models`**: 問卷數據模型，定義問卷結構和驗證規則
- **`modlue.models.config_models`**: 配置模型，管理系統設置和參數
- **`modlue.models.exceptions`**: 異常處理模型，統一錯誤管理

#### 4. 提示層 (Prompts)
- **`modlue.prompts.agent_instruction`**: 代理指令模板，定義 AI 行為模式
- **`modlue.prompts.response_templates`**: 回應模板，標準化輸出格式

### 數據流程

1. **問卷創建**: 用戶需求 → 問卷設計器 → 結構化問卷
2. **數據收集**: 問卷發布 → 答案收集器 → 驗證和存儲

## 參考資料

- [Google ADK 文檔](https://google.github.io/adk-docs/)
- [Google ADK 和 MCP 整合指南](https://cloud.google.com/blog/topics/developers-practitioners/use-google-adk-and-mcp-with-an-external-server)


## 目錄結構

```
survey-ai-agent/
├── agents/                # AI 代理模組
│   ├── answercollector/   # 答案收集器
│   ├── designer/          # 問卷設計器
│   ├── question_designer.py  # 問題設計器
│   ├── survey_templates.py   # 問卷模板
│   └── __init__.py
├── config/                # 配置模組
│   ├── settings.py        # 設定管理
│   └── __init__.py
├── module/
│   ├── models/                # 數據模型
│   │   ├── config_models.py   # 配置模型
│   │   ├── exceptions.py      # 異常定義
│   │   ├── survey_models.py   # 問卷模型
│   │   └── __init__.py
│   ├── prompts/               # 提示詞模組
│   │   ├── agent_instruction.py  # 代理指令
│   │   ├── response_templates.py # 回應模板
│   │   └── __init__.py
│   ├── services/              # 服務模組
│   │   ├── data_formatter.py  # 數據格式化
│   │   ├── local_survery_handle.py  # 本地問卷處理
│   │   ├── sheet_writer.py    # Google Sheets 寫入
│   │   └── __init__.py
│   └── mock/                  # 模擬數據
│   │   ├── mock_data.py       # 模擬數據
│   │   └── __init__.py
├── output/
│   ├── survey/                # 問卷存儲目錄
│   │   ├── *.json             # 問卷 JSON 文件
│   └── response/              # 回應存儲目錄
│       └── *.json             # 答案 JSON 文件
├── .env                   # 環境變數配置文件
├── .env-example           # 環境變數範例
├── guide_agent_answercollector.md  # 答案收集器指南
├── guide_agent_designer.md         # 設計器指南
└── README.md              # 本說明文件
```
