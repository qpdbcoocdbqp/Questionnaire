# Answer Collector Agent 使用指南

## 概述

Answer Collector Agent 是一個基於 Google ADK 的多代理系統，專門用於進行問卷調查的對話式收集。該系統採用 LoopAgent 和 SequentialAgent 模式，結合迭代對話收集與順序資料庫上傳工作流程。

主要功能：
- 智能對話式問卷調查
- 自動檢測問卷完成狀態
- 結構化答案提取與格式化
- 自動儲存至本地檔案和 Google Sheets

## Agent 工作架構

```
┌─────────────────────────────────────────────────────────────┐
│                    ADK Web Interface                        │
│                   (Port 9000)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AnswersCollectorWorkflow                       │
│                 (SequentialAgent)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────▼─────────────────┐
    │        Stage 1: 對話收集階段        │
    │      AnswersCollector (Loop)      │
    │  ┌─────────────┬─────────────────┐ │
    │  │QuestionAsker│ SurveyCompleted │ │
    │  │ (LlmAgent)  │    Agent        │ │
    │  │             │  (BaseAgent)    │ │
    │  └─────────────┴─────────────────┘ │
    └─────────────────┬─────────────────┘
                      │ escalate=True
    ┌─────────────────▼─────────────────┐
    │       Stage 2: 答案結構化階段       │
    │   SurveyAnswersHandler (LlmAgent) │
    └─────────────────┬─────────────────┘
                      │
    ┌─────────────────▼─────────────────┐
    │       Stage 3: 資料儲存階段        │
    │   DatabaseUploader (LlmAgent)     │
    │   ┌─────────────────────────────┐ │
    │   │   save_to_storage_tool      │ │
    │   │   ├─ Local JSON File       │ │
    │   │   └─ Google Sheets         │ │
    │   └─────────────────────────────┘ │
    └───────────────────────────────────┘
```

## 啟動 Web UI

### 前置需求
1. 確保已安裝 Google ADK
2. 設置環境變數 (參考 `.env-example` 文件)
   - `LOCAL_SURVEY_ID`: 問卷 ID
   - `LOCAL_SURVEY_DIRECTORY`: 問卷檔案目錄
   - `LOCAL_RESPONSE_DIRECTORY`: 回應儲存目錄
   - `GEMINI_API_KEY`: Gemini API Key
   - `GEMINI_MODEL`: 使用的 Gemini 模型 (預設: gemini-2.5-flash-lite)
   - `GOOGLE_DRIVE_FOLDER_ID`: Google Sheets 目錄 ID
   - `GOOGLE_SPREADSHEET_ID`: Google Sheets ID
   - Google Sheets API 認證相關環境變數

 ### 環境變數設置範例

 ```env
 # 問卷設定
 LOCAL_SURVEY_ID=your_survey_id
 LOCAL_SURVEY_DIRECTORY=your_survey_directory
 LOCAL_RESPONSE_DIRECTORY=your_response_directory

 # Gemini API 設定
 GEMINI_API_KEY=your_api_key
 GEMINI_MODEL=gemini-2.5-flash-lite

 # Google Sheets 設定
 GOOGLE_DRIVE_FOLDER_ID=your_folder_id
 GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
 GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
 DEFAULT_SHEET_NAME=your_default_sheet_name

```

### 啟動命令

```sh
# 啟動 ADK Web 界面，指定 agents 目錄
adk web --port 9000 agents/

# 或使用自定義端口
adk web --port 8080 agents/
```

### 訪問界面

啟動後在瀏覽器中訪問：
- 預設: http://localhost:9000
- 自定義端口: http://localhost:8080

## 功能特性

### 1. 智能對話收集
- **QuestionAsker**: 友善的問卷調查員，逐一提出問題
- **自然語言理解**: 智能解析用戶回答
- **對話記錄**: 完整記錄問答過程，包含時間戳

### 2. 自動完成檢測
- **SurveyCompletedAgent**: 監控問卷進度
- **智能判斷**: 根據回答數量自動判斷是否完成
- **狀態管理**: 維護會話狀態和完成時間

### 3. 結構化資料處理
- **SurveyAnswersHandler**: 從對話中提取結構化答案
- **Pydantic 模型**: 確保資料格式正確性
- **答案映射**: 將對話內容對應到問卷題目

### 4. 雙重儲存機制
- **本地儲存**: JSON 格式儲存至本地檔案
- **雲端同步**: 自動上傳至 Google Sheets
- **錯誤處理**: 完善的異常處理和日誌記錄

## 已知問題
### TODO
- **對話開啟時, 須手動輸入訊息 (start 之類的訊息), 才會觸發答案蒐集流程**
- **未設計單題重新提問**
- **未對使用者輸入答案進行完備性與正確性撿查**
- **整份問卷完成前, 不觸發持久化儲存工具**
- **整份問卷完成後, 尚未隱藏工作訊息**

## 使用範例

### 基本對話流程

```
Agent: 您好！歡迎參與我們的問卷調查。這是一份關於「用戶體驗滿意度」的調查。

第 1 題: 您對我們的產品整體滿意度如何？(題型: single_choice)
選項: 1. 非常滿意, 2. 滿意, 3. 普通, 4. 不滿意, 5. 非常不滿意

User: 我選擇 2，滿意

Agent: 好的，謝謝您的回答。

第 2 題: 您最常使用哪個功能？(題型: text)

User: 我最常使用搜尋功能

Agent: 收到了。

第 3 題: 您會推薦給朋友嗎？(題型: single_choice)
選項: 1. 會, 2. 不會, 3. 不確定

User: 1

Agent: 謝謝您完成了所有問題！您的回答已經成功儲存。
```

### 資料儲存格式

**本地 JSON 檔案** (`response/{session_id}.json`):
```json
{
  "answers": [
    {
      "question_id": "q1",
      "value": "滿意"
    },
    {
      "question_id": "q2", 
      "value": "搜尋功能"
    }
  ]
}
```

**Google Sheets 格式**:
| survey_id | user_id | session_id | q1 | q2 | q3 | completed_at |
|-----------|---------|------------|----|----|----| -------------|
| survey123 | user456 | sess789    | 滿意| 搜尋功能| 會 | 2024-01-01T10:00:00 |

## 注意事項

### 系統限制
- LoopAgent 最大迭代次數: 10 次
- 問卷完成判斷基於回答數量 (可能需要調整邏輯)
- 需要有效的 Google Sheets API 認證

### 最佳實踐
1. **環境設定**: 確保所有環境變數正確設置
2. **問卷設計**: 使用 Designer Agent 預先設計好問卷結構
3. **測試驗證**: 在正式使用前進行完整測試
4. **錯誤監控**: 關注日誌輸出，及時處理異常

### 故障排除
- **認證失敗**: 檢查 Google API 憑證設置
- **問卷載入失敗**: 確認問卷 ID 和目錄路徑正確
- **儲存失敗**: 檢查檔案權限和網路連線
