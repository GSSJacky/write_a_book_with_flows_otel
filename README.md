# Gemini-Powered Japanese Book Writing Flow with Traceloop + Instana Integration

This project is a customized fork of [crewAI's `write_a_book_with_flows`](https://github.com/crewAIInc/crewAI-examples/tree/main/write_a_book_with_flows), enhanced to support Google Gemini, Japanese language book generation, and telemetry tracing with Instana.

## 🔧 Improvements Made

1. **Switched to Google Gemini SDK** for all LLM tasks via `langchain-google-genai`.
2. **Improved output logic**, ensuring `book.md` is generated even if partial content exists.
3. **Japanese Book Writing**: The entire outline and chapter content is generated in Japanese.
4. **Traceloop + Instana** integration via OTLP/HTTP to monitor task-level agent traces.

## 📦 Setup Instructions

```bash
cd write_a_book_with_flows_otel
python3.11 -m venv venv3.11
source venv3.11/bin/activate
pip install crewai
crewai install
````

### `.env` Setup

Create an `.env` file as follows under the main directory:

```dotenv
# Optional for web search tools
# SERPER_API_KEY=

GEMINI_API_KEY='XXXXXXXXX'  # Required for Gemini LLM
PYTHONPATH=src
CREWAI_DISABLE_TELEMETRY=true

# Optional Traceloop + Instana Integration
TRACELOOP_BASE_URL=http://localhost:4318
TRACELOOP_HEADERS=x-instana-key=XXXXXAgentKeyXXXXXX
OTEL_EXPORTER_OTLP_INSECURE=false
```

## ▶️ Running the Book Flow

```bash
crewai flow kickoff
```

This command will:

1. Generate the book outline in Japanese.
2. Use Gemini to write each chapter via an agent crew.
3. Save the full book to `output/book.md`.

## 📄 Output

The final result will be a complete book saved as:

```
./output/book.md
```

If chapters cannot be generated, fallback placeholder text will still be saved to ensure you have output visibility.

## 📊 Tracing Integration (Optional)

If you have Instana Agent running locally and listening on port `4318`, all flows will export OpenTelemetry traces for task/agent lifecycle tracking.





# Gemini × Traceloop × Instana 対応 日本語書籍生成フロー

本プロジェクトは、[crewAI公式の `write_a_book_with_flows`](https://github.com/crewAIInc/crewAI-examples/tree/main/write_a_book_with_flows) を基に、日本語での書籍執筆・Gemini対応・Instanaトレース連携に対応した強化版です。

## 🔧 改善点

1. **Google Gemini SDK に対応**（LLM処理を `langchain-google-genai` に切り替え）
2. **出力処理の改善**：章が不完全でも `book.md` を必ず出力
3. **日本語での本執筆**：アウトラインも章の内容もすべて日本語で生成
4. **Traceloop + Instana統合**：OTLP/HTTP 経由で各エージェントのタスクをトレース

## 📦 セットアップ手順

```bash
cd write_a_book_with_flows_otel
python3.11 -m venv venv3.11
source venv3.11/bin/activate
pip install crewai
crewai install
````

### `.env` 設定例

```dotenv
# Optional（検索系ツール未使用の場合は不要）
# SERPER_API_KEY=

GEMINI_API_KEY='XXXXXXXXX'  # Gemini使用に必要
PYTHONPATH=src
CREWAI_DISABLE_TELEMETRY=true

# Traceloop + Instana の設定（任意）
TRACELOOP_BASE_URL=http://localhost:4318
TRACELOOP_HEADERS=x-instana-key=XXXXXAgentKeyXXXXXX
OTEL_EXPORTER_OTLP_INSECURE=false
```

## ▶️ 実行方法

```bash
crewai flow kickoff
```

以下の処理が自動的に実行されます：

1. 書籍の章立てを日本語で生成
2. 各章の内容を Gemini で作成（エージェントCrew使用）
3. 完成した書籍を `output/book.md` に保存

## 📄 出力結果

生成された本は以下のパスに保存されます：

```
./output/book.md
```

章が一部でも生成できれば内容を保存。不足していてもテンプレートで出力されます。

## 📊 Traceloop + Instana 連携（オプション）

ローカルで Instana Agent がポート `4318` で待機していれば、OpenTelemetry を通じてエージェントのタスク実行状況を Instana で確認できます。

