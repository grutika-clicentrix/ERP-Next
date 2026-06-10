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

        else:
            return {"error": f"Tool {name} not found"}
    except Exception as e:
        frappe.log_error(title=f"AI Tool Exec Error: {name}", message=frappe.get_traceback())
        return {"error": str(e)}

# ── Main handler ───────────────────────────────────────────────
@frappe.whitelist()
def chat(messages):
    """
    Endpoint called by the chat page.
    messages: JSON string of [{role, content}, ...]
    Returns: assistant reply string
    """
    try:
        history = json.loads(messages) if isinstance(messages, str) else messages
    except Exception:
        frappe.throw("Invalid messages format")

    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    api_key = frappe.conf.get("gemini_api_key")
    if not api_key:
        frappe.throw(
            "Gemini API key not configured. "
            "Run: bench --site manufactoring_site set-config gemini_api_key 'AIza-your-key'"
        )

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

    # Call Gemini in a loop to resolve multiple tool calls sequentially
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
        candidate = data["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])

        # Check for function calls
        function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]

        if function_calls:
            # Add the model's tool request message to contents history
            contents.append(content)

            # Execute the function calls
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
                return parts[0].get("text", "")
            except IndexError:
                return "No response text returned."

    return "Max tool execution turns reached."


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
    """
    Triggers the monthly expenses and profitability seeding script
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_16_expenses
    phase_16_expenses.execute()
    return "Expenses seeding completed successfully"

@frappe.whitelist()
def execute_verify_expenses():
    """
    Triggers the verification script for GP and NP ratios
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_16_expenses
    phase_16_expenses.verify()
    return "Expenses verification completed successfully"

@frappe.whitelist()
def execute_seed_stock_transfers():
    """
    Triggers the stock transfers and closing stock seeding script
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_17_stock_transfers
    phase_17_stock_transfers.execute()
    return "Stock transfers seeding completed successfully"

@frappe.whitelist()
def execute_verify_stock_transfers():
    """
    Triggers the verification script for stock transfers and closing stock percentage
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import phase_17_stock_transfers
    phase_17_stock_transfers.verify()
    return "Stock transfers verification completed successfully"


@frappe.whitelist()
def list_companies():
    """
    Returns list of companies and their abbreviations
    """
    companies = frappe.get_all("Company", fields=["name", "abbr"])
    return companies


@frappe.whitelist()
def find_woodcraft_records():
    """
    Finds and counts all records for Wood Craft Furniture Pvt. Ltd. across all DocTypes
    """
    import frappe
    company = "Wood Craft Furniture Pvt. Ltd."
    results = {}
    
    # Get all standard non-child DocTypes
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
            
    # Special check for tables that might refer to company or have abbr
    # check for GL Entry and Stock Ledger Entry (they have company field)
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
    """
    Triggers the cleanup script for Wood Craft Furniture Pvt. Ltd.
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import cleanup_woodcraft
    cleanup_woodcraft.execute()
    return "Wood Craft cleanup completed successfully"


@frappe.whitelist()
def execute_verify_cleanup_woodcraft():
    """
    Triggers the verification script for Wood Craft cleanup
    """
    import sys
    sys.path.append("/mnt/d/Erp-bench/data_seeding_scripts")
    import cleanup_woodcraft
    success = cleanup_woodcraft.verify()
    if success:
        return "Wood Craft verification passed: no records remaining"
    else:
        return "Wood Craft verification failed: records remaining"





