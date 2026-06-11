import frappe
from frappe.desk.query_report import run

@frappe.whitelist()
def test():
    try:
        filters = frappe._dict({
            "company": "Wood Craft Furniture Pvt. Ltd.",
            "filter_based_on": "Date Range",
            "periodicity": "Yearly",
            "period_start_date": "2025-04-01",
            "period_end_date": "2026-03-31"
        })
        res = run("Profit and Loss Statement", filters=filters)
        print("Success! Result type: " + str(type(res)))
        if isinstance(res, dict) and "result" in res:
            print("Row count: " + str(len(res["result"])))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR: " + str(e))
