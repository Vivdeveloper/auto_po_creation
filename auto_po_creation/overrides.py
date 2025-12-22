import frappe
import json

@frappe.whitelist()
def supplier_link_query(doctype, txt, searchfield, start, page_len, filters):
    if isinstance(filters, str):
        filters = json.loads(filters)

    item_code = filters.get("item_code")
    if not item_code:
        return []

    return frappe.db.sql("""
        SELECT DISTINCT s.name
        FROM `tabSupplier` s
        INNER JOIN `tabItem Supplier` isup
            ON isup.supplier = s.name
        WHERE
            isup.parent = %s
            AND s.name LIKE %s
        ORDER BY s.name
        LIMIT %s OFFSET %s
    """, (item_code, f"%{txt}%", page_len, start))
