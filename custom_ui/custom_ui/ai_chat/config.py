GEMINI_MODEL = "gemini-2.5-flash"          # fast + smart, free tier available

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={api_key}"
)

MAX_TOKENS  = 8192
MAX_HISTORY = 20   # keep last N messages to avoid token overflow

SYSTEM_PROMPT = """You are an AI assistant embedded inside ERPNext, an open-source ERP system built on Frappe Framework.

Your job is to help users:
- Query and understand their ERPNext data (invoices, orders, stock, customers, suppliers, reports)
- Perform actions like creating or updating documents
- Explain ERPNext concepts and workflows
- Summarise reports and financial data

Rules:
- Be concise and direct. Users are busy business operators.
- NEVER perform mathematical calculations yourself. LLMs hallucinate math. If the user asks for a total, average, or sum, you MUST write a SQL query using SUM(), AVG(), or use execute_frappe_report. The database is 100% accurate; you are just the translator.
- Always display financial figures exactly as returned by the database. Do not round numbers. Use exactly 2 decimal places and the correct currency symbol.
- When the user asks for "reporting" or any kind of report, data analysis, trends, or comparisons, you MUST show visual reports. Generate an interactive chart to visualize the information. Output a valid JSON configuration for Frappe Charts enclosed EXACTLY within ```chart and ``` markdown blocks.
  You MUST ALSO provide a brief text summary or a small markdown table (e.g. top 5 results) IN ADDITION to the chart, so the user can read the data directly.
  Example Format:
  ```chart
  {{
    "title": "Chart Title",
    "data": {{ "labels": ["A", "B"], "datasets": [{{ "name": "Val", "values": [10, 20] }}] }},
    "type": "bar"
  }}
  ```
  Allowed types: bar, line, pie, percentage, donut. DO NOT wrap the chart block in any other code blocks.
- When showing secondary data or if a chart is impossible, use markdown tables where it helps readability.
- If you don't have access to live data, use the database query tools available to retrieve it.
- When you need to fetch complex analytics, totals, or grouped data, FIRST try to use `execute_frappe_report` with standard ERPNext reports (like 'Accounts Receivable', 'Stock Balance', 'General Ledger', 'Sales Analytics').
- If the data cannot be fetched via standard reports, you may use `execute_sql_query` to write a custom SELECT query.
- Never use `execute_sql_query` for data modification.
- When creating or updating documents, always use the tools provided. Confirm details with the user if necessary.
- To trigger backend workflows on an existing document (e.g. submitting an Invoice, or canceling a document), use the `execute_document_method` tool.
- To send an email, ALWAYS use the `send_email` tool. DO NOT use `create_document` for the `Communication` DocType, as that bypasses the mailer.
- Always respond in the same language the user writes in.
- Never make up data. If you don't know, say so.
- CONTEXT HINT (Branches): In this ERPNext instance, "Branches" (e.g. Bhosari Plant, Chakan Plant, Vellore Plant, Nalagarh Plant) are tracked via the `cost_center` field on transaction items (e.g. `Sales Invoice Item`, `Purchase Invoice Item`, `GL Entry`). If the user asks for branch-wise sales or expenses, you MUST join the item table and group by `cost_center`.

Current ERPNext context:
- Company: {company}
- Logged-in user: {user}
- Date: {today}
"""

GEMINI_TOOLS = [
    {
        "functionDeclarations": [
            {
                "name": "get_documents",
                "description": "Retrieve a list of documents for a specific DocType (e.g., Customer, Item, Sales Order) with optional filters.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name (e.g. Customer, Item, Sales Order)"},
                        "filters": {"type": "OBJECT", "description": "Filters as key-value pairs (e.g. {'status': 'Draft'}) (optional)"},
                        "limit": {"type": "INTEGER", "description": "Max documents to return (default: 20) (optional)"}
                    },
                    "required": ["doctype"]
                }
            },
            {
                "name": "get_document",
                "description": "Retrieve details of a single document by DocType and Name/ID (including all fields and table rows).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name"},
                        "name": {"type": "STRING", "description": "The document name/ID (e.g. SO-2026-00001)"}
                    },
                    "required": ["doctype", "name"]
                }
            },
            {
                "name": "create_document",
                "description": "Create a new document in ERPNext (e.g., Sales Order, Purchase Order). Note: For Sales Orders and Purchase Orders, you must supply the 'warehouse' field inside each row of the 'items' list (e.g., {'item_code': 'MAR-011-S0', 'qty': 1, 'warehouse': 'Finished Goods Store - SFPL'}).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name"},
                        "data": {"type": "OBJECT", "description": "Fields and child tables for the new document"}
                    },
                    "required": ["doctype", "data"]
                }
            },
            {
                "name": "update_document",
                "description": "Update an existing document in ERPNext.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name"},
                        "name": {"type": "STRING", "description": "The document name/ID"},
                        "data": {"type": "OBJECT", "description": "Fields to update"}
                    },
                    "required": ["doctype", "name", "data"]
                }
            },
            {
                "name": "delete_document",
                "description": "Delete a document in ERPNext.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name"},
                        "name": {"type": "STRING", "description": "The document name/ID"}
                    },
                    "required": ["doctype", "name"]
                }
            },
            {
                "name": "execute_frappe_report",
                "description": "Execute a standard Frappe Report and get the result. Example reports: 'General Ledger', 'Stock Balance', 'Sales Analytics'.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "report_name": {"type": "STRING", "description": "Name of the report (e.g. 'Stock Balance')"},
                        "filters": {"type": "OBJECT", "description": "Filters for the report as key-value pairs (e.g. {'company': 'Your Company', 'from_date': '2026-01-01'})"}
                    },
                    "required": ["report_name"]
                }
            },
            {
                "name": "execute_sql_query",
                "description": "Execute a raw SQL SELECT query for custom analytics. MUST ONLY BE A SELECT QUERY.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "The raw SQL SELECT query (e.g. 'SELECT item_code, sum(qty) FROM `tabStock Ledger Entry` GROUP BY item_code')"},
                        "target_doctype": {"type": "STRING", "description": "The primary DocType being accessed (e.g. 'Sales Order', 'Stock Ledger Entry')"}
                    },
                    "required": ["query", "target_doctype"]
                }
            },
            {
                "name": "execute_document_method",
                "description": "Execute a specific backend method on an existing document (e.g., 'send' to send a Communication, 'submit' to submit an invoice).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "doctype": {"type": "STRING", "description": "The DocType name"},
                        "name": {"type": "STRING", "description": "The document name/ID"},
                        "method": {"type": "STRING", "description": "The method to execute (e.g., 'send', 'submit', 'cancel')"},
                        "args": {"type": "OBJECT", "description": "Optional keyword arguments for the method"}
                    },
                    "required": ["doctype", "name", "method"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email. This correctly adds the email to the Frappe Email Queue and creates the Communication record.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "recipients": {"type": "STRING", "description": "Comma-separated list of email addresses"},
                        "subject": {"type": "STRING", "description": "Email subject"},
                        "message": {"type": "STRING", "description": "Email body content (HTML allowed)"},
                        "reference_doctype": {"type": "STRING", "description": "DocType this email relates to (e.g., 'Purchase Order')"},
                        "reference_name": {"type": "STRING", "description": "Document name this email relates to (e.g., 'PUR-ORD-2026-00490')"}
                    },
                    "required": ["recipients", "subject", "message"]
                }
            }
        ]
    }
]
