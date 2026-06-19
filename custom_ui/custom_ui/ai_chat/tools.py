import frappe

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

        elif name == "execute_document_method":
            doctype = args.get("doctype")
            docname = args.get("name")
            method = args.get("method")
            method_args = args.get("args") or {}
            
            doc = frappe.get_doc(doctype, docname)
            result = doc.run_method(method, **method_args)
            frappe.db.commit()
            return {"output": {"status": "Success", "method": method, "result": result}}

        elif name == "send_email":
            recipients = args.get("recipients")
            subject = args.get("subject")
            message = args.get("message")
            reference_doctype = args.get("reference_doctype")
            reference_name = args.get("reference_name")
            
            # Convert AI markdown to HTML so tables, bolds, etc render correctly in the email
            html_message = frappe.utils.md_to_html(message) if message else ""
            
            # frappe.sendmail natively handles queueing, creating Communication, and linking
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=html_message,
                reference_doctype=reference_doctype,
                reference_name=reference_name
            )
            frappe.db.commit()
            return {"output": {"status": "Success", "message": "Email has been sent and added to the Email Queue."}}

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
