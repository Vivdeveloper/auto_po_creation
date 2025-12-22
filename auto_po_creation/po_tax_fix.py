import frappe

def apply_purchase_taxes(doc, method):
    """
    Force load taxes from Purchase Taxes and Charges Template
    Fixes GST not loading for In-State / Out-State
    """

    if not doc.taxes_and_charges:
        return

    # Load tax template
    template = frappe.get_doc(
        "Purchase Taxes and Charges Template",
        doc.taxes_and_charges
    )

    if not template.taxes:
        frappe.throw(
            f"Tax Template {doc.taxes_and_charges} has no tax rows"
        )

    # Clear existing taxes
    doc.set("taxes", [])

    # Copy ALL mandatory fields
    for t in template.taxes:
        doc.append("taxes", {
            "charge_type": t.charge_type,
            "account_head": t.account_head,
            "rate": t.rate,

            # 🔥 MANDATORY FIELDS (FIX)
            "category": t.category,
            "add_deduct_tax": t.add_deduct_tax,

            # Optional but good practice
            "description": t.description,
            "cost_center": t.cost_center,
            "included_in_print_rate": t.included_in_print_rate,
            "included_in_paid_amount": t.included_in_paid_amount
        })

    # Force recalculation
    doc.calculate_taxes_and_totals()
