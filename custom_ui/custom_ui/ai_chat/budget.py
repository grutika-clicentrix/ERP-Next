import frappe

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
