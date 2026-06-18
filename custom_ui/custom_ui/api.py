import frappe
import json
import requests

# ── Configuration ──────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"          # fast + smart, free tier available

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={api_key}"
)

MAX_TOKENS  = 1024
MAX_HISTORY = 20   # keep last N messages to avoid token overflow

SYSTEM_PROMPT = """You are an AI assistant embedded inside ERPNext, an open-source ERP system built on Frappe Framework.

Your job is to help users:
- Query and understand their ERPNext data (invoices, orders, stock, customers, suppliers, reports)
- Perform actions like creating or updating documents
- Explain ERPNext concepts and workflows
- Summarise reports and financial data

Rules:
- Be concise and direct. Users are busy business operators.
- When showing data, use markdown tables where it helps readability.
- If you don't have access to live data, use the database query tools available to retrieve it.
- When you need to fetch complex analytics, totals, or grouped data, FIRST try to use `execute_frappe_report` with standard ERPNext reports (like 'Stock Balance', 'General Ledger', 'Sales Analytics').
- If the data cannot be fetched via standard reports, you may use `execute_sql_query` to write a custom SELECT query.
- Never use `execute_sql_query` for data modification.
- When creating or updating documents, always use the tools provided. Confirm details with the user if necessary.
- Always respond in the same language the user writes in.
- Never make up data. If you don't know, say so.

Current ERPNext context:
- Company: {company}
- Logged-in user: {user}
- Date: {today}
"""

# ── Tool Definitions for Gemini ─────────────────────────────────
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
            }
        ]
    }
]

# ── Tool Execution Handlers ─────────────────────────────────────
def execute_tool(name, args):
    try:
        if name == "get_documents":
            doctype = args.get("doctype")
            filters = args.get("filters") or {}
            limit = args.get("limit") or 20
            # Fetch with all fields
            res = frappe.get_list(doctype, filters=filters, limit=limit, fields=["*"])
            return {"output": res}

        elif name == "get_document":
            doctype = args.get("doctype")
            docname = args.get("name")
            doc = frappe.get_doc(doctype, docname)
            return {"output": doc.as_dict()}

        elif name == "create_document":
            doctype = args.get("doctype")
            data = args.get("data")
            doc = frappe.get_doc(dict(doctype=doctype, **data))
            doc.insert()
            frappe.db.commit()
            return {"output": {"status": "Success", "name": doc.name, "doc": doc.as_dict()}}

        elif name == "update_document":
            doctype = args.get("doctype")
            docname = args.get("name")
            data = args.get("data")
            doc = frappe.get_doc(doctype, docname)
            doc.update(data)
            doc.save()
            frappe.db.commit()
            return {"output": {"status": "Success", "name": doc.name, "doc": doc.as_dict()}}

        elif name == "execute_frappe_report":
            report_name = args.get("report_name")
            filters = args.get("filters") or {}
            
            # Auto-map filters for financial statements to avoid mandatory fields errors
            if report_name in ["Profit and Loss Statement", "Balance Sheet", "Cash Flow Statement"]:
                if "from_date" in filters and "period_start_date" not in filters:
                    filters["period_start_date"] = filters.pop("from_date")
                if "to_date" in filters and "period_end_date" not in filters:
                    filters["period_end_date"] = filters.pop("to_date")
                if "filter_based_on" not in filters:
                    filters["filter_based_on"] = "Date Range"
                if "periodicity" not in filters:
                    filters["periodicity"] = "Yearly"

            from frappe.desk.query_report import run
            res = run(report_name, filters=filters)
            if isinstance(res, dict):
                return {"output": {"columns": res.get("columns"), "result": res.get("result")}}
            elif isinstance(res, tuple) and len(res) >= 2:
                return {"output": {"columns": res[0], "result": res[1]}}
            else:
                return {"output": str(res)}

        elif name == "execute_sql_query":
            query = args.get("query", "").strip()
            if not query.lower().startswith("select"):
                return {"error": "Only SELECT queries are allowed for security reasons."}
            res = frappe.db.sql(query, as_dict=True)
            return {"output": res}

        else:
            return {"error": f"Tool {name} not found"}
    except Exception as e:
        frappe.log_error(title=f"AI Tool Exec Error: {name}", message=frappe.get_traceback())
        return {"error": str(e)}

# ── Token Tracking & Budgeting ─────────────────────────────────
def get_model_rates(model_name):
    rate_doc = frappe.get_all("AI Model Rate", filters={"model_name": model_name}, fields=["prompt_token_price", "response_token_price"])
    if rate_doc:
        return rate_doc[0]
    return {"prompt_token_price": 0.30, "response_token_price": 2.50}

def calculate_cost(model_name, prompt_tokens, response_tokens):
    rates = get_model_rates(model_name)
    cost = (prompt_tokens / 1000000.0) * rates["prompt_token_price"] + (response_tokens / 1000000.0) * rates["response_token_price"]
    return cost

@frappe.whitelist()
def get_current_month_cost():
    from frappe.utils import nowdate, get_first_day
    try:
        first_day = get_first_day(nowdate())
        usage_logs = frappe.get_all("AI Token Usage Log", filters={"request_time": [">=", first_day]}, fields=["total_cost"])
        return sum(log.total_cost for log in usage_logs if log.total_cost)
    except Exception:
        return 0.0

def check_budget():
    try:
        settings = frappe.get_single("AI Settings")
        if not settings.enable_budget_checking:
            return True, ""
        
        monthly_budget = settings.monthly_budget or 0.0
        if monthly_budget <= 0:
            return True, ""
        
        current_cost = get_current_month_cost()
        
        if current_cost >= monthly_budget:
            if settings.alert_email:
                try:
                    frappe.sendmail(
                        recipients=[settings.alert_email],
                        subject="ERPNext AI Assistant: Monthly Budget Exceeded",
                        message=f"The monthly budget of ${monthly_budget} has been exceeded. Current cost: ${current_cost:.4f}. API calls are now blocked."
                    )
                except Exception:
                    pass
            return False, f"Monthly AI budget of ${monthly_budget} exceeded. Please contact your administrator."
    except Exception:
        pass
    return True, ""

def log_token_usage(model_name, prompt_tokens, response_tokens, api_method="chat"):
    from frappe.utils import now_datetime
    try:
        total_tokens = prompt_tokens + response_tokens
        cost = calculate_cost(model_name, prompt_tokens, response_tokens)
        
        doc = frappe.get_doc({
            "doctype": "AI Token Usage Log",
            "user": frappe.session.user,
            "model": model_name,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "total_cost": cost,
            "api_method": api_method,
            "request_time": now_datetime()
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error("Token Logging Failed", str(e))

# ── Main handler ───────────────────────────────────────────────
@frappe.whitelist()
def chat(messages, approved_action=None):
    """
    Endpoint called by the chat page.
    messages: JSON string of [{role, content}, ...]
    approved_action: JSON string of tool to execute directly (after user approval)
    Returns: assistant reply string or approval required dict
    """
    try:
        history = json.loads(messages) if isinstance(messages, str) else messages
        if approved_action and isinstance(approved_action, str):
            approved_action = json.loads(approved_action)
    except Exception:
        frappe.throw("Invalid messages format")

    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    api_key = frappe.conf.get("gemini_api_key")
    if not api_key:
        frappe.throw(
            "Gemini API key not configured. "
            "Run: bench set-config gemini_api_key 'AIza-your-key'"
        )

    budget_ok, budget_msg = check_budget()
    if not budget_ok:
        return {"error": budget_msg}

    system_text = SYSTEM_PROMPT.format(
        company=frappe.defaults.get_global_default("company") or "Your Company",
        user=frappe.session.user,
        today=frappe.utils.nowdate(),
    )

    # Convert chat history to Gemini format
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
        })

    # If the user just approved an action, artificially inject it so Gemini knows it executed
    if approved_action:
        contents.append({
            "role": "model",
            "parts": [{"functionCall": {"name": approved_action["name"], "args": approved_action["args"]}}]
        })
        result = execute_tool(approved_action["name"], approved_action["args"])
        contents.append({
            "role": "user",
            "parts": [{"functionResponse": {"name": approved_action["name"], "response": result}}]
        })

    # Call Gemini in a loop to resolve multiple tool calls sequentially
    accumulated_prompt_tokens = 0
    accumulated_response_tokens = 0
    
    for loop_count in range(8):  # limit to 8 turns to avoid infinite loops
        payload = {
            "system_instruction": {"parts": [{"text": system_text}]},
            "contents": contents,
            "tools": GEMINI_TOOLS,
            "generationConfig": {
                "maxOutputTokens": MAX_TOKENS,
                "temperature": 0.2,  # lower temperature is better for tool calling
            }
        }

        url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL, api_key=api_key)
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, default=str),
            timeout=30,
        )

        if response.status_code != 200:
            try:
                error_body = response.json()
            except Exception:
                error_body = {"error": {"message": response.text}}
            frappe.throw(f"Gemini API error {response.status_code}: {error_body.get('error', {}).get('message', 'Unknown error')}")

        data = response.json()
        
        usage_meta = data.get("usageMetadata", {})
        pt = usage_meta.get("promptTokenCount", 0)
        rt = usage_meta.get("candidatesTokenCount", 0)
        
        if pt > 0 or rt > 0:
            log_token_usage(GEMINI_MODEL, pt, rt, "chat")
            accumulated_prompt_tokens += pt
            accumulated_response_tokens += rt

        candidate = data["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        # Check for function calls
        function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]

        if function_calls:
            # INTERCEPT RISKY TOOLS FOR APPROVAL
            risky_tools = ["create_document", "update_document", "execute_sql_query"]
            for call in function_calls:
                name = call.get("name")
                args = call.get("args") or {}
                
                if name in risky_tools:
                    # Return immediate dict response asking for frontend approval
                    return {
                        "requires_approval": True,
                        "tool_call": {"name": name, "args": args},
                        "tokens": {
                            "prompt": accumulated_prompt_tokens,
                            "response": accumulated_response_tokens,
                            "total": accumulated_prompt_tokens + accumulated_response_tokens
                        }
                    }

            # Add the model's tool request message to contents history
            contents.append(content)

            # Execute the function calls safely
            response_parts = []
            for call in function_calls:
                name = call.get("name")
                args = call.get("args") or {}
                result = execute_tool(name, args)
                response_parts.append({
                    "functionResponse": {
                        "name": name,
                        "response": result
                    }
                })

            # Append the tool results message to contents history
            contents.append({
                "role": "user",
                "parts": response_parts
            })
            # Continue the loop to let Gemini process the tool outputs
            continue
        else:
            # No tool call; return the text response
            try:
                reply_text = parts[0].get("text", "")
                return {
                    "reply": reply_text,
                    "tokens": {
                        "prompt": accumulated_prompt_tokens,
                        "response": accumulated_response_tokens,
                        "total": accumulated_prompt_tokens + accumulated_response_tokens
                    }
                }
            except IndexError:
                return {"reply": "No response text returned.", "tokens": {}}

    return {"error": "Max tool execution turns reached."}


@frappe.whitelist()
def check_ai_page():
    from frappe.desk.desk_page import get
    page_data = get("ai")
    print("PAGE OBJECT RETRIEVED:")
    print(f"Standard: {page_data.get('standard')}")
    print(f"Module: {page_data.get('module')}")
    print(f"Script length: {len(page_data.get('script', ''))}")
    print(f"Style length: {len(page_data.get('style', ''))}")
    print("Script prefix (first 250 chars):")
    print(page_data.get("script", "")[:250])
    return True

@frappe.whitelist()
def execute_seed_expenses():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_16_expenses
    phase_16_expenses.execute()
    return "Expenses seeding completed successfully"

@frappe.whitelist()
def execute_verify_expenses():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_16_expenses
    phase_16_expenses.verify()
    return "Expenses verification completed successfully"

@frappe.whitelist()
def execute_seed_stock_transfers():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_17_stock_transfers
    phase_17_stock_transfers.execute()
    return "Stock transfers seeding completed successfully"

@frappe.whitelist()
def execute_verify_stock_transfers():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_17_stock_transfers
    phase_17_stock_transfers.verify()
    return "Stock transfers verification completed successfully"

@frappe.whitelist()
def list_companies():
    companies = frappe.get_all("Company", fields=["name", "abbr"])
    return companies

@frappe.whitelist()
def find_woodcraft_records():
    import frappe
    company = "Wood Craft Furniture Pvt. Ltd."
    results = {}
    
    all_doctypes = frappe.get_all("DocType", filters={"istable": 0})
    for d in all_doctypes:
        dt = d.name
        try:
            meta = frappe.get_meta(dt)
            if meta.has_field("company"):
                count = frappe.db.count(dt, filters={"company": company})
                if count > 0:
                    results[dt] = count
        except Exception:
            pass
            
    for dt in ["GL Entry", "Stock Ledger Entry"]:
        try:
            count = frappe.db.count(dt, filters={"company": company})
            if count > 0:
                results[dt] = count
        except Exception:
            pass
            
    return results

@frappe.whitelist()
def execute_cleanup_woodcraft():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import cleanup_woodcraft
    cleanup_woodcraft.execute()
    return "Wood Craft cleanup completed successfully"

@frappe.whitelist()
def execute_verify_cleanup_woodcraft():
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import cleanup_woodcraft
    success = cleanup_woodcraft.verify()
    if success:
        return "Wood Craft verification passed: no records remaining"
    else:
        return "Wood Craft verification failed: records remaining"
