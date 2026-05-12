import frappe

def setup_phase1():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"

    # ─── 1. TERRITORIES / ZONES ───────────────────────────────────────────────
    zone_tree = {
        "Local Zone - Maharashtra": {
            "parent": "India",
            "children": ["Mumbai Metropolitan", "Pune Region", "Nashik & Aurangabad", "Rest of Maharashtra"]
        },
        "Domestic - North Zone": {
            "parent": "India",
            "children": ["Delhi NCR", "Rajasthan", "Punjab & Haryana", "Uttar Pradesh", "Himachal & Uttarakhand"]
        },
        "Domestic - South Zone": {
            "parent": "India",
            "children": ["Tamil Nadu", "Karnataka", "Telangana & Andhra Pradesh", "Kerala"]
        },
        "Domestic - East Zone": {
            "parent": "India",
            "children": ["West Bengal", "Odisha", "Bihar & Jharkhand", "North East India"]
        },
        "Domestic - West Zone": {
            "parent": "India",
            "children": ["Gujarat", "Goa", "Madhya Pradesh", "Chhattisgarh"]
        },
        "International Zone": {
            "parent": "India",
            "children": ["Middle East", "Southeast Asia", "Europe", "Americas"]
        },
    }

    for zone_name, info in zone_tree.items():
        if not frappe.db.exists("Territory", zone_name):
            frappe.get_doc({"doctype": "Territory", "territory_name": zone_name,
                            "parent_territory": info["parent"], "is_group": 1}).insert()
        for child in info["children"]:
            if not frappe.db.exists("Territory", child):
                frappe.get_doc({"doctype": "Territory", "territory_name": child,
                                "parent_territory": zone_name, "is_group": 0}).insert()
    print("✅ Territories created")

    # ─── 2. PAYMENT TERMS ─────────────────────────────────────────────────────
    payment_terms = [
        {
            "template_name": "Immediate Payment",
            "terms": [{"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 100, "credit_days": 0}]
        },
        {
            "template_name": "Net 30 Days",
            "terms": [{"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 100, "credit_days": 30}]
        },
        {
            "template_name": "Net 60 Days",
            "terms": [{"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 100, "credit_days": 60}]
        },
        {
            "template_name": "50% Advance 50% on Delivery",
            "terms": [
                {"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 50, "credit_days": 0},
                {"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 50, "credit_days": 15}
            ]
        },
        {
            "template_name": "30% Advance 70% on Delivery",
            "terms": [
                {"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 30, "credit_days": 0},
                {"due_date_based_on": "Day(s) after invoice date", "invoice_portion": 70, "credit_days": 20}
            ]
        },
    ]
    for pt in payment_terms:
        if not frappe.db.exists("Payment Terms Template", pt["template_name"]):
            doc = frappe.get_doc({"doctype": "Payment Terms Template", "template_name": pt["template_name"]})
            for t in pt["terms"]:
                doc.append("terms", {
                    "due_date_based_on": t["due_date_based_on"],
                    "invoice_portion": t["invoice_portion"],
                    "credit_days": t["credit_days"]
                })
            doc.insert()
    print("✅ Payment Terms created")

    # ─── 3. CUSTOMER GROUPS ───────────────────────────────────────────────────
    cg_tree = {
        "Local Customers": {
            "parent": "All Customer Groups",
            "children": ["Local Retailers", "Local Corporates", "Local Interior Designers"]
        },
        "Domestic Customers": {
            "parent": "All Customer Groups",
            "children": ["Domestic Retailers", "Domestic Corporates - North", "Domestic Corporates - South",
                         "Domestic Corporates - East", "Domestic Corporates - West"]
        },
        "International Customers": {
            "parent": "All Customer Groups",
            "children": ["Export Clients - Middle East", "Export Clients - Europe", "Export Clients - Americas",
                         "Overseas Distributors"]
        },
        "Online Customers": {
            "parent": "All Customer Groups",
            "children": ["E-Commerce Buyers", "D2C Online Buyers"]
        },
    }
    for grp, info in cg_tree.items():
        if not frappe.db.exists("Customer Group", grp):
            frappe.get_doc({"doctype": "Customer Group", "customer_group_name": grp,
                            "parent_customer_group": info["parent"], "is_group": 1}).insert()
        for child in info["children"]:
            if not frappe.db.exists("Customer Group", child):
                frappe.get_doc({"doctype": "Customer Group", "customer_group_name": child,
                                "parent_customer_group": grp, "is_group": 0}).insert()
    print("✅ Customer Groups created")

    # ─── 4. SUPPLIER GROUPS ───────────────────────────────────────────────────
    sg_tree = {
        "Local Suppliers": {
            "parent": "All Supplier Groups",
            "children": ["Local Raw Material", "Local Hardware & Fittings", "Local Chemical & Consumables",
                         "Local Contract Labour", "Local Services"]
        },
        "Domestic Suppliers": {
            "parent": "All Supplier Groups",
            "children": ["Domestic Raw Material", "Domestic Hardware", "Domestic Chemicals",
                         "Domestic Logistics & Transport", "Domestic Maintenance Services"]
        },
        "International Suppliers": {
            "parent": "All Supplier Groups",
            "children": ["Import - Hardware & Machinery", "Import - Raw Material", "Import - Chemicals"]
        },
    }
    for grp, info in sg_tree.items():
        if not frappe.db.exists("Supplier Group", grp):
            frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": grp,
                            "parent_supplier_group": info["parent"], "is_group": 1}).insert()
        for child in info["children"]:
            if not frappe.db.exists("Supplier Group", child):
                frappe.get_doc({"doctype": "Supplier Group", "supplier_group_name": child,
                                "parent_supplier_group": grp, "is_group": 0}).insert()
    print("✅ Supplier Groups created")

    # ─── 5. PURCHASE TAX TEMPLATES ────────────────────────────────────────────
    purchase_tax_templates = [
        {"name": "GST 18% Input - WCFPL",  "rate": 18, "account": f"GST payable - {abbr}"},
        {"name": "GST 12% Input - WCFPL",  "rate": 12, "account": f"GST payable - {abbr}"},
        {"name": "GST 5% Input - WCFPL",   "rate": 5,  "account": f"GST payable - {abbr}"},
    ]
    for tpl in purchase_tax_templates:
        if not frappe.db.exists("Purchase Taxes and Charges Template", tpl["name"]):
            doc = frappe.get_doc({
                "doctype": "Purchase Taxes and Charges Template",
                "title": tpl["name"],
                "company": company,
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": tpl["account"],
                    "description": tpl["name"],
                    "rate": tpl["rate"]
                }]
            })
            doc.insert()
    print("✅ Purchase Tax Templates created")

    # ─── 6. MISSING EXPENSE / INCOME ACCOUNTS ─────────────────────────────────
    parent_map = {
        "Expense": {
            "Factory Overheads": "5100 - Direct Expenses - WCFPL",
            "Packaging Expenses": "5100 - Direct Expenses - WCFPL",
            "Repair & Maintenance Expenses": "5200 - Indirect Expenses - WCFPL",
            "Vehicle Running Expenses": "5200 - Indirect Expenses - WCFPL",
            "Bad Debts Written Off": "5200 - Indirect Expenses - WCFPL",
            "Sales Commission Expenses": "5200 - Indirect Expenses - WCFPL",
            "Staff Welfare Expenses": "5200 - Indirect Expenses - WCFPL",
            "Insurance Expenses": "5200 - Indirect Expenses - WCFPL",
            "Bank Charges": "5200 - Indirect Expenses - WCFPL",
            "Salary & Wages": "5100 - Direct Expenses - WCFPL",
        },
        "Income": {
            "Rental Income": "4200 - Indirect Income - WCFPL",
            "Scrap Sale Income": "4200 - Indirect Income - WCFPL",
            "Interest Received": "4200 - Indirect Income - WCFPL",
            "Job Work Charges Received": "4200 - Indirect Income - WCFPL",
            "Training & Consultancy Income": "4200 - Indirect Income - WCFPL",
        },
        "Liability": {
            "TDS Payable": "2120 - Duties and Taxes - WCFPL",
            "TCS Payable": "2120 - Duties and Taxes - WCFPL",
            "Salary Payable": "2100 - Current Liabilities - WCFPL",
        },
    }
    root_type_map = {"Expense": "Expense", "Income": "Income", "Liability": "Liability"}
    for category, accounts in parent_map.items():
        for acc_name, parent in accounts.items():
            full_name = f"{acc_name} - {abbr}"
            if not frappe.db.exists("Account", full_name):
                frappe.get_doc({
                    "doctype": "Account",
                    "account_name": acc_name,
                    "parent_account": parent,
                    "company": company,
                    "root_type": root_type_map[category],
                    "is_group": 0,
                    "account_type": "Bank" if "Bank" in acc_name else ""
                }).insert()
    print("✅ Missing Accounts created")

    # ─── 7. BANK ACCOUNT ──────────────────────────────────────────────────────
    bank_acc_name = f"WCFPL Current Account - HDFC - {abbr}"
    if not frappe.db.exists("Account", bank_acc_name):
        frappe.get_doc({
            "doctype": "Account",
            "account_name": "WCFPL Current Account - HDFC",
            "parent_account": f"1103 - Bank Accounts - {abbr}",
            "company": company,
            "root_type": "Asset",
            "is_group": 0,
            "account_type": "Bank"
        }).insert()
    print("✅ Bank Account created")

    # ─── 8. REDISTRIBUTE EXISTING CUSTOMERS ──────────────────────────────────
    import random
    local_groups   = ["Local Retailers", "Local Corporates", "Local Interior Designers"]
    domestic_north = "Domestic Corporates - North"
    domestic_south = "Domestic Corporates - South"
    domestic_east  = "Domestic Corporates - East"
    domestic_west  = "Domestic Corporates - West"
    dom_retail     = "Domestic Retailers"

    local_territories  = ["Mumbai Metropolitan", "Pune Region", "Nashik & Aurangabad"]
    north_territories  = ["Delhi NCR", "Rajasthan", "Punjab & Haryana", "Uttar Pradesh"]
    south_territories  = ["Tamil Nadu", "Karnataka", "Telangana & Andhra Pradesh"]
    east_territories   = ["West Bengal", "Odisha", "Bihar & Jharkhand"]
    west_territories   = ["Gujarat", "Goa", "Madhya Pradesh"]

    retail_cust = frappe.get_all("Customer", filters={"customer_group": "Retail"},   fields=["name"])
    corp_cust   = frappe.get_all("Customer", filters={"customer_group": "Corporate"}, fields=["name"])

    # Distribute retailers: 8 local, rest domestic
    for idx, c in enumerate(retail_cust):
        if idx < 8:
            grp = random.choice(local_groups)
            ter = random.choice(local_territories)
        else:
            grp = dom_retail
            ter = random.choice(north_territories + south_territories + east_territories + west_territories)
        frappe.db.set_value("Customer", c.name, {
            "customer_group": grp,
            "territory": ter,
            "payment_terms": random.choice(["Immediate Payment", "50% Advance 50% on Delivery"])
        })

    # Distribute corporates: 15 local, rest across zones
    zone_groups = [domestic_north, domestic_south, domestic_east, domestic_west]
    zone_terrs  = [north_territories, south_territories, east_territories, west_territories]
    for idx, c in enumerate(corp_cust):
        if idx < 15:
            grp = "Local Corporates"
            ter = random.choice(local_territories)
        else:
            zi  = (idx - 15) % 4
            grp = zone_groups[zi]
            ter = random.choice(zone_terrs[zi])
        frappe.db.set_value("Customer", c.name, {
            "customer_group": grp,
            "territory": ter,
            "payment_terms": random.choice(["Net 30 Days", "Net 60 Days", "30% Advance 70% on Delivery"])
        })
    print("✅ Customers redistributed across zones")

    # ─── 9. REDISTRIBUTE EXISTING SUPPLIERS ──────────────────────────────────
    local_sg   = ["Local Raw Material", "Local Hardware & Fittings", "Local Chemical & Consumables"]
    dom_sg     = ["Domestic Raw Material", "Domestic Hardware", "Domestic Chemicals", "Domestic Logistics & Transport"]

    all_suppliers = frappe.get_all("Supplier", filters={"supplier_group": "General"}, fields=["name"])
    for idx, s in enumerate(all_suppliers):
        if idx < 20:
            sg = random.choice(local_sg)
            ter = random.choice(local_territories)
        elif idx < 36:
            sg = random.choice(dom_sg)
            ter = random.choice(north_territories + south_territories)
        else:
            sg = "Import - Hardware & Machinery"
            ter = "Middle East"
        frappe.db.set_value("Supplier", s.name, {
            "supplier_group": sg,
            "payment_terms": random.choice(["Net 30 Days", "Net 60 Days", "Immediate Payment"])
        })
    print("✅ Suppliers redistributed")

    frappe.db.commit()
    print("\n🎉 Phase 1 Complete — All Master Data Ready")
