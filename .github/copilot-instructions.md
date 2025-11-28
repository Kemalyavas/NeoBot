# NeoBI - AI Agent Instructions

## Project Overview

**NeoBI** is a Turkish-language AI assistant for NeoOne's field sales team. It analyzes product performance, identifies low-selling products with visual reports, and creates **passive discounts** with user confirmation.

**Business Context**: NeoOne is building this as Phase 1. Phase 2 will add WhatsApp notifications for order status updates.

## Architecture

```
┌─────────────────┐     HTTP      ┌─────────────────┐    OpenAI API    ┌─────────────────┐
│  React/Vite     │◄────────────►│  FastAPI        │◄────────────────►│  GPT-4o         │
│  Frontend:5173  │              │  Backend:8000   │                  │  Assistant API  │
└─────────────────┘              └────────┬────────┘                  └─────────────────┘
                                          │ REST API (JWT)
                                          ▼
                                 ┌─────────────────┐
                                 │  NeoOne .NET    │
                                 │  Backend (Exp)  │
                                 │  test.neoone.com.tr
                                 └─────────────────┘
```

```
backend/
  main.py              # FastAPI app, CORS, 3 endpoints
  app/
    assistant.py       # OpenAI Assistant lifecycle & tool execution polling loop
    tools.py           # Tool functions + tools_schema + available_functions registry
    api_client.py      # NeoOneClient - JWT auth with 55-min token cache
    models.py          # Pydantic request/response models
frontend/
  src/components/ChatInterface.jsx  # Chat UI + Recharts bar chart rendering
```

### Data Flow

1. Frontend → `POST /api/chat/start` → creates OpenAI thread
2. User message → `POST /api/chat/message` → `add_message_to_thread` → `run_assistant`
3. Polling loop: if `requires_action` → execute tool → `submit_tool_outputs` → continue polling
4. Final response returned (may contain embedded chart JSON)

## Environment Variables (backend/.env)

```env
OPENAI_API_KEY=sk-...
ASSISTANT_ID=asst_...        # If missing, new assistant created on startup
NEOONE_API_URL=https://test.neoone.com.tr/api/v1
NEOONE_EMAIL=...
NEOONE_PASSWORD=...
```

⚠️ **Critical**: If `ASSISTANT_ID` exists in `.env`, code changes to system prompt have NO effect. Delete the ID to recreate assistant with new instructions.

## Key Patterns

### Adding a New Tool (3 steps in `app/tools.py`)

```python
# 1. Define function (must return JSON string)
def my_new_tool(param: str):
    result = {"data": "..."}
    return json.dumps(result, ensure_ascii=False)  # Turkish chars!

# 2. Add schema to tools_schema list
{"type": "function", "function": {"name": "my_new_tool", ...}}

# 3. Register in available_functions dict
available_functions = {..., "my_new_tool": my_new_tool}
```

### Chart Rendering Protocol

AI embeds this JSON in markdown code block → Frontend parses and renders `<BarChart>`:

```json
{
  "type": "chart",
  "title": "Satış Dağılımı",
  "data": [{ "name": "Ürün A", "value": 150 }]
}
```

### Safety Layer (CEO Requirement)

1. **User Confirmation**: `create_discount` requires `confirmed=true`. AI must ask for explicit "evet"/"onaylıyorum" first.
2. **Passive Discounts**: All bot-created discounts are `isActive: false` - requires admin approval to go live.

### NeoOne API Integration

- Auth: `POST /Auth/login` → JWT token (cached 55 min)
- Products: `GET /orders/reports/product-sales`
- Discounts: `POST /Discounts` (creates passive)
- Customer Groups: `GET /CustomerGroups`

## Running the Project

```powershell
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload  # http://localhost:8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev  # http://localhost:5173
```

## Conventions

- **Language**: All UI text, AI prompts, and responses in Turkish
- **Tool outputs**: Always `json.dumps(..., ensure_ascii=False)`
- **Error format**: `{"error": "message"}` JSON on failure
- **Data filtering**: Skip `[BONUS]` and `[BEDELSİZ]` products in aggregations

## Roadmap Context

- **Current**: MVP - Chat widget with discount management
- **Next**: Embed as widget in NeoOne web panel (iframe/script), pass user token
- **Phase 2**: NeoBI - WhatsApp Business API integration for order notifications

## Conventions

- **Language**: All user-facing text and AI prompts in Turkish
- **Tool outputs**: Always `json.dumps(..., ensure_ascii=False)` for Turkish chars
- **Error handling**: Tools return `{"error": "message"}` JSON on failure
- **Filtering**: Skip products with `[BONUS]` or `[BEDELSİZ]` in name when aggregating sales
