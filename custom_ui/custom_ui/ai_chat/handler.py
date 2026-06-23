import frappe
import json
import requests
from custom_ui.custom_ui.ai_chat.config import (
    GEMINI_MODEL,
    GEMINI_ENDPOINT,
    MAX_TOKENS,
    MAX_HISTORY,
    SYSTEM_PROMPT,
    GEMINI_TOOLS
)
from custom_ui.custom_ui.ai_chat.tools import execute_tool
from custom_ui.custom_ui.ai_chat.budget import check_budget, log_token_usage

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
    new_history = []
    
    def truncate_result(res):
        res_str = json.dumps(res, default=str)
        if len(res_str) > 2000:
            return res_str[:2000] + "... [Truncated]"
        return res_str

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
        new_history.append({
            "role": "assistant",
            "content": f"[System: Executed tool {approved_action['name']} with args {json.dumps(approved_action['args'])}]"
        })
        new_history.append({
            "role": "user",
            "content": f"[System: Tool result: {truncate_result(result)}]"
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
            risky_tools = ["create_document", "update_document", "delete_document", "execute_document_method", "send_email"]
            for call in function_calls:
                name = call.get("name")
                args = call.get("args") or {}
                
                if name in risky_tools:
                    # Return immediate dict response asking for frontend approval
                    return {
                        "requires_approval": True,
                        "tool_call": {"name": name, "args": args},
                        "new_history": new_history,
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
                new_history.append({
                    "role": "assistant",
                    "content": f"[System: Executed tool {name} with args {json.dumps(args)}]"
                })
                new_history.append({
                    "role": "user",
                    "content": f"[System: Tool result: {truncate_result(result)}]"
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
                reply_text = "".join([p.get("text", "") for p in parts if "text" in p])
                return {
                    "reply": reply_text,
                    "new_history": new_history,
                    "tokens": {
                        "prompt": accumulated_prompt_tokens,
                        "response": accumulated_response_tokens,
                        "total": accumulated_prompt_tokens + accumulated_response_tokens
                    }
                }
            except IndexError:
                return {"reply": "No response text returned.", "new_history": new_history, "tokens": {}}

    return {"error": "Max tool execution turns reached."}
