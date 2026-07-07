import frappe
from frappe.utils import now_datetime
import requests

def get_model_rates(model_name):
    rate_doc = frappe.get_all("AI Model Rate", filters={"model_name": model_name}, fields=["input_cost_per_1m_usd", "output_cost_per_1m_usd", "markup_percentage"])
    if rate_doc:
        return rate_doc[0]
    # Default fallback if model not found
    return {
        "input_cost_per_1m_usd": 0.15,
        "output_cost_per_1m_usd": 0.60,
        "markup_percentage": 0.0
    }

def calculate_costs(model_name, prompt_tokens, response_tokens):
    rates = get_model_rates(model_name)
    settings = frappe.get_single("AI Settings")
    exchange_rate = settings.current_usd_to_inr_rate or 84.0
    markup = rates["markup_percentage"] or 0.0
    
    raw_input_usd = (prompt_tokens / 1000000.0) * rates["input_cost_per_1m_usd"]
    raw_output_usd = (response_tokens / 1000000.0) * rates["output_cost_per_1m_usd"]
    
    raw_cost_usd = raw_input_usd + raw_output_usd
    charged_cost_usd = raw_cost_usd * (1 + (markup / 100.0))
    charged_cost_inr = charged_cost_usd * exchange_rate
    
    return {
        "raw_cost_usd": raw_cost_usd,
        "charged_cost_usd": charged_cost_usd,
        "charged_cost_inr": charged_cost_inr,
        "markup_percentage_used": markup,
        "exchange_rate_used": exchange_rate
    }

def has_enough_balance():
    balance = frappe.db.get_single_value("AI Settings", "balance_inr") or 0.0
    if balance <= 0:
        return False, "Insufficient AI Credits. Please ask your administrator to recharge the wallet."
    return True, ""

def log_token_usage(model_name, prompt_tokens, response_tokens, api_method="chat"):
    try:
        total_tokens = prompt_tokens + response_tokens
        costs = calculate_costs(model_name, prompt_tokens, response_tokens)
        charged_inr = costs["charged_cost_inr"]
        
        # 1. Pessimistic Lock on AI Settings
        frappe.db.sql("SELECT name FROM `tabAI Settings` FOR UPDATE")
        settings = frappe.get_single("AI Settings")
        
        prev_balance = settings.balance_inr or 0.0
        new_balance = max(0.0, prev_balance - charged_inr)
        
        # 2. Update Settings Balance
        settings.db_set("balance_inr", new_balance, update_modified=False)
        settings.db_set("total_consumed_inr", (settings.total_consumed_inr or 0.0) + charged_inr, update_modified=False)
        
        # 3. Create Token Usage Log
        usage_doc = frappe.get_doc({
            "doctype": "AI Token Usage Log",
            "user": frappe.session.user,
            "model": model_name,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "raw_cost_usd": costs["raw_cost_usd"],
            "charged_cost_usd": costs["charged_cost_usd"],
            "charged_cost_inr": charged_inr,
            "markup_percentage_used": costs["markup_percentage_used"],
            "exchange_rate_used": costs["exchange_rate_used"],
            "request_time": now_datetime()
        })
        usage_doc.insert(ignore_permissions=True)
        usage_doc.submit()
        
        # 4. Create Audit Ledger Transaction (DEBIT)
        tx_desc = f"Chat: {model_name} ({total_tokens} tokens)"
        tx_doc = frappe.get_doc({
            "doctype": "AI Credit Transaction",
            "transaction_type": "DEBIT",
            "amount_inr": charged_inr,
            "balance_after_inr": new_balance,
            "description": tx_desc,
            "reference_token_usage": usage_doc.name
        })
        tx_doc.insert(ignore_permissions=True)
        tx_doc.submit()
        
        # Check Low Balance Notification
        LOW_BALANCE_THRESHOLD = 50.0
        if new_balance < LOW_BALANCE_THRESHOLD and not settings.low_balance_notified:
            settings.db_set("low_balance_notified", 1, update_modified=False)
            if settings.alert_email:
                try:
                    frappe.sendmail(
                        recipients=[settings.alert_email],
                        subject="ERPNext AI Assistant: Low Balance Alert \U0001f4b3",
                        message=f"The AI credit balance has dropped below \u20b9{LOW_BALANCE_THRESHOLD} (\u20b9{new_balance:.2f} remaining). Please recharge to ensure uninterrupted service."
                    )
                except Exception:
                    pass
        
        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error("Token Logging Failed", str(e))

@frappe.whitelist(allow_guest=False)
def recharge_wallet(amount_inr, description="Admin recharge"):
    frappe.only_for("System Manager")
    amount = float(amount_inr)
    if amount <= 0:
        frappe.throw("Recharge amount must be greater than zero.")
        
    try:
        frappe.db.sql("SELECT name FROM `tabAI Settings` FOR UPDATE")
        settings = frappe.get_single("AI Settings")
        
        prev_balance = settings.balance_inr or 0.0
        new_balance = prev_balance + amount
        
        settings.db_set("balance_inr", new_balance, update_modified=False)
        settings.db_set("total_purchased_inr", (settings.total_purchased_inr or 0.0) + amount, update_modified=False)
        
        if new_balance >= 50.0:
            settings.db_set("low_balance_notified", 0, update_modified=False)
            
        tx_doc = frappe.get_doc({
            "doctype": "AI Credit Transaction",
            "transaction_type": "CREDIT",
            "amount_inr": amount,
            "balance_after_inr": new_balance,
            "description": description
        })
        tx_doc.insert(ignore_permissions=True)
        tx_doc.submit()
        
        frappe.db.commit()
        return {"status": "success", "new_balance": new_balance}
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(f"Failed to recharge wallet: {str(e)}")

def sync_exchange_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/USD")
        response.raise_for_status()
        data = response.json()
        inr_rate = data.get("rates", {}).get("INR")
        
        if inr_rate:
            settings = frappe.get_single("AI Settings")
            settings.db_set("current_usd_to_inr_rate", inr_rate)
            frappe.db.commit()
            print(f"[Currency Sync] Updated USD->INR rate: {inr_rate}")
    except Exception as e:
        frappe.log_error("AI Exchange Rate Sync Failed", str(e))
