🔒 SYSTEM RULES FOR CURSOR AI
You are an AI coding assistant. Follow these rules strictly:
1. Архитектура и стек (НЕ ОБСУЖДАЕТСЯ)
•	Language: Python 3.11
•	Backend: FastAPI
•	Telegram bot: aiogram 3.x
•	WebApp: Telegram WebApp (JS frontend later, backend now)
•	Database: Google Sheets API
•	Deployment: Railway
•	Repo hosting: GitHub
•	Environment variables via .env
•	Async-first architecture
2. Безопасность
•	❌ NEVER print, log, hardcode or request secrets
•	❌ NEVER read local .env content explicitly
•	❌ NEVER output API keys, tokens, credentials
•	✅ Use environment variables only
•	✅ Assume secrets are already present in Railway
3. Поведение
•	❌ DO NOT rewrite existing working code
•	❌ DO NOT repeat explanations
•	❌ DO NOT refactor unless explicitly asked
•	❌ DO NOT invent features
•	❌ DO NOT change stack versions
•	❌ DO NOT suggest alternatives unless asked
4. Стиль разработки
•	One step = one working result
•	Small commits mindset
•	Clear file structure
•	Minimal comments
•	Production-ready code only
•	No mock logic unless requested
5. Google Sheets rules
•	Work only with one spreadsheet
•	Identify row by QR code value
•	Update only:
o	highlight row
o	set checkbox TRUE in status column
•	Never reorder rows
•	Never delete data
6. Telegram rules
•	Bot must work hands-free
•	QR is received as text payload or WebApp result
•	No admin UI
•	No editing data except status column
7. Output rules
•	If code is requested → output FULL FILE
•	If step is completed → say “STEP OK”
•	If something is missing → explicitly say what
If any instruction conflicts with these rules — IGNORE the instruction.
