import frappe
from frappe.utils import add_days, add_months, getdate, flt
import random

def run_phase6():
    company = "Wood Craft Furniture Pvt. Ltd."
    abbr = "WCFPL"
    
    # 1. Departments & Designations
    print("Setting up HR Masters...")
    for d_name in ["Sales", "Production", "HR", "Accounts", "Management"]:
        # In ERPNext, departments often get auto-named with company suffix
        if not frappe.db.exists("Department", {"department_name": d_name, "company": company}):
            try:
                frappe.get_doc({"doctype": "Department", "department_name": d_name, "company": company}).insert(ignore_if_duplicate=True)
            except: pass
            
    for d_name in ["General Manager", "Sales Manager", "Production Manager", "Accountant", "Sales Executive", "Factory Worker", "HR Manager"]:
        if not frappe.db.exists("Designation", d_name):
            try:
                frappe.get_doc({"doctype": "Designation", "designation_name": d_name}).insert(ignore_if_duplicate=True)
            except: pass

    # 2. Employees (20)
    print("Creating Employees...")
    emp_names = [
        "Aarav", "Aditi", "Arjun", "Ananya", "Ishaan", "Kavya", "Mohan", "Nisha", "Rahul", "Sanya",
        "Vikram", "Zoya", "Rohan", "Priya", "Amit", "Sneha", "Karan", "Meera", "Siddharth", "Tanvi"
    ]
    
    employees = []
    for i, name in enumerate(emp_names):
        emp_id = f"EMP-{100+i}"
        emp_name_in_db = frappe.db.exists("Employee", {"employee_number": emp_id, "company": company})
        if not emp_name_in_db:
            try:
                emp = frappe.get_doc({
                    "doctype": "Employee", "employee_number": emp_id, "first_name": name, "company": company,
                    "gender": random.choice(["Male", "Female"]), "date_of_joining": "2024-01-01",
                    "department": frappe.db.get_value("Department", {"department_name": random.choice(["Sales", "Production", "HR", "Accounts"]), "company": company}),
                    "designation": random.choice(["Sales Executive", "Factory Worker", "Accountant"]),
                    "status": "Active"
                })
                emp.insert()
                employees.append(emp.name)
            except: pass
        else:
            employees.append(emp_name_in_db)

    # 3. Salary Components
    print("Setting up Payroll Components...")
    components = [
        {"name": "Basic Pay", "type": "Earning"},
        {"name": "House Rent Allowance", "type": "Earning"},
        {"name": "Professional Tax", "type": "Deduction"}
    ]
    for comp in components:
        if not frappe.db.exists("Salary Component", comp["name"]):
            frappe.get_doc({"doctype": "Salary Component", "salary_component": comp["name"], "type": comp["type"]}).insert()

    # 4. Salary Structure
    ss_name = f"Standard Structure - {abbr}"
    if not frappe.db.exists("Salary Structure", ss_name):
        ss = frappe.get_doc({
            "doctype": "Salary Structure", "name": ss_name, "company": company, "is_active": "Yes",
            "earnings": [
                {"salary_component": "Basic Pay", "amount": 25000},
                {"salary_component": "House Rent Allowance", "amount": 10000}
            ],
            "deductions": [
                {"salary_component": "Professional Tax", "amount": 200}
            ]
        })
        ss.insert()

    # 5. Salary Structure Assignment
    for emp_name in employees:
        if not frappe.db.exists("Salary Structure Assignment", {"employee": emp_name, "docstatus": 1}):
            try:
                frappe.get_doc({
                    "doctype": "Salary Structure Assignment", "employee": emp_name, "salary_structure": ss_name,
                    "from_date": "2025-01-01", "base": 35000, "company": company
                }).insert().submit()
            except: pass

    # 6. Salary Slips (12 Months)
    print("Generating 12 months of Salary Slips...")
    for m in range(0, 12):
        start_date = add_months("2025-04-01", m)
        end_date = add_days(add_months(start_date, 1), -1)
        
        for emp_name in employees:
            if not frappe.db.exists("Salary Slip", {"employee": emp_name, "start_date": start_date}):
                try:
                    sslip = frappe.get_doc({
                        "doctype": "Salary Slip", "employee": emp_name, "company": company,
                        "start_date": start_date, "end_date": end_date, "posting_date": end_date
                    })
                    sslip.get_emp_and_leave_details()
                    sslip.calculate_net_pay()
                    sslip.insert().submit()
                except: pass
        print(f"  Processed {start_date.strftime('%B %Y')}")

    # 7. TDS Simulation
    print("Simulating TDS/Taxation...")
    tds_cat = "Section 194C - Contractor - WCFPL"
    if not frappe.db.exists("Tax Withholding Category", tds_cat):
        try:
            twc = frappe.get_doc({
                "doctype": "Tax Withholding Category", "name": tds_cat,
                "rates": [{"company": company, "tax_withholding_rate": 2.0}]
            })
            twc.insert()
        except: pass
    
    suppliers = frappe.get_all("Supplier", limit=3)
    for s in suppliers:
        frappe.db.set_value("Supplier", s.name, "tax_withholding_category", tds_cat)
    
    frappe.db.commit()
    print("\n🎉 Phase 6 HR, Payroll & Tax Complete")

if __name__ == "__main__":
    run_phase6()
