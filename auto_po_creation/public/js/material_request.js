// frappe.ui.form.on('Material Request', {
//     refresh(frm) {
//         if (frm.doc.__islocal || frm.doc.docstatus !== 1) return;

//         frm.add_custom_button(__('Auto Create PO'), () => {

//             // ----------------------------------------
//             // FETCH ITEMS WHICH ALREADY HAVE PO
//             // ----------------------------------------
//             frappe.call({
//                 method: 'auto_po_creation.api.get_po_status',
//                 args: { material_request: frm.doc.name },
//                 callback(r) {

//                     const po_items = r.message || [];
//                     let table_data = [];
//                     let missing_supplier = [];

//                     // ----------------------------------------
//                     // PREPARE TABLE DATA
//                     // ----------------------------------------
//                     frm.doc.items.forEach(row => {

//                         const supplier =
//                             row.supplier ||
//                             row.supplier_code ||
//                             row.default_supplier ||
//                             row.custom_supplier;

//                         if (!supplier) {
//                             missing_supplier.push(row.item_code);
//                             return;
//                         }

//                         const po_created = po_items.includes(row.item_code);

//                         table_data.push({
//                             po_created: po_created ? 1 : 0,
//                             _po_created: po_created,
//                             item_code: row.item_code,
//                             item_name: row.item_name,
//                             qty: row.qty,
//                             supplier: supplier
//                         });
//                     });

//                     if (missing_supplier.length) {
//                         frappe.msgprint({
//                             title: __('Supplier Missing'),
//                             indicator: 'red',
//                             message: `
//                                 Supplier not selected for:<br>
//                                 <b>${missing_supplier.join(', ')}</b>
//                             `
//                         });
//                         return;
//                     }

//                     // ----------------------------------------
//                     // POPUP DIALOG
//                     // ----------------------------------------
//                     const dialog = new frappe.ui.Dialog({
//                         title: __('Select Items for PO'),
//                         size: 'extra-large',
//                         fields: [
//                             {
//                                 fieldname: 'items',
//                                 fieldtype: 'Table',
//                                 label: 'Items',
//                                 cannot_add_rows: true,
//                                 in_place_edit: false,
//                                 fields: [
//                                     {
//                                         fieldname: 'po_created',
//                                         fieldtype: 'Check',
//                                         label: 'PO Created',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'item_code',
//                                         fieldtype: 'Data',
//                                         label: 'Item Code',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'item_name',
//                                         fieldtype: 'Data',
//                                         label: 'Item Name',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'qty',
//                                         fieldtype: 'Float',
//                                         label: 'Qty',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'supplier',
//                                         fieldtype: 'Link',
//                                         options: 'Supplier',
//                                         label: 'Supplier',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     }
//                                 ]
//                             }
//                         ],
//                         primary_action_label: __('Create PO'),
//                         primary_action() {

//                             // ----------------------------------------
//                             // GET SELECTED ROWS (DEFAULT CHECKBOX)
//                             // ----------------------------------------
//                             const selected_items = dialog.fields_dict.items.grid
//                                 .get_selected_children()
//                                 .filter(row => !row._po_created);

//                             if (!selected_items.length) {
//                                 frappe.msgprint(__('Please select items without existing PO.'));
//                                 return;
//                             }

//                             const payload = selected_items.map(row => ({
//                                 item_code: row.item_code,
//                                 qty: row.qty,
//                                 supplier: row.supplier
//                             }));

//                             frappe.call({
//                                 method: 'auto_po_creation.api.create_purchase_orders',
//                                 args: {
//                                     material_request: frm.doc.name,
//                                     items: JSON.stringify(payload)
//                                 },
//                                 callback(res) {
//                                     if (!res.message) return;

//                                     let msg = `<b>PO created for following items:</b><br><br>`;

//                                     res.message.created.forEach(po => {
//                                         msg += `
//                                             <b>PO:</b>
//                                             <a href="/app/purchase-order/${po.name}">
//                                                 ${po.name}
//                                             </a><br>
//                                             <b>Items:</b> ${po.items.join(', ')}<br><br>
//                                         `;
//                                     });

//                                     frappe.msgprint({
//                                         title: __('PO Creation Summary'),
//                                         indicator: 'green',
//                                         message: msg
//                                     });

//                                     dialog.hide();
//                                     frm.reload_doc();
//                                 }
//                             });
//                         }
//                     });

//                     // ----------------------------------------
//                     // LOAD DATA
//                     // ----------------------------------------
//                     dialog.fields_dict.items.df.data = table_data;
//                     dialog.fields_dict.items.grid.refresh();

//                     // ----------------------------------------
//                     // DISABLE SELECTION FOR CREATED PO
//                     // ----------------------------------------
//                     setTimeout(() => {
//                         dialog.fields_dict.items.grid.grid_rows.forEach(r => {
//                             if (r.doc._po_created) {
//                                 r.$checkbox.prop('disabled', true);
//                             }
//                         });
//                     }, 200);

//                     dialog.show();
//                 }
//             });
//         });
//     }
// });










// frappe.ui.form.on('Material Request', {
//     refresh(frm) {
//         // Only on submitted MR
//         if (frm.doc.__islocal || frm.doc.docstatus !== 1) return;

//         frm.add_custom_button(__('Auto Create PO'), () => {
//             frappe.call({
//                 method: 'auto_po_creation.api.get_po_status',
//                 args: { material_request: frm.doc.name },
//                 callback(r) {
//                     const po_items = r.message || [];
//                     const table_data = [];
//                     const missing_supplier = [];

//                     // Build table rows
//                     (frm.doc.items || []).forEach(row => {
//                         // Always pick custom supplier first
//                         const supplier =
//                             row.custom_supplier_ ||      // custom field on MR Item
//                             row.supplier ||
//                             row.supplier_code ||
//                             row.default_supplier;

//                         if (!supplier) {
//                             // Will trigger the “Supplier Missing” popup
//                             missing_supplier.push(row.item_code);
//                             return;
//                         }

//                         const po_created = po_items.includes(row.item_code);

//                         table_data.push({
//                             po_created: po_created ? 1 : 0,
//                             _po_created: po_created,
//                             item_code: row.item_code,
//                             item_name: row.item_name,
//                             qty: row.qty,
//                             supplier: supplier
//                         });
//                     });

//                     if (missing_supplier.length) {
//                         frappe.msgprint({
//                             title: __('Supplier Missing'),
//                             indicator: 'red',
//                             message: `
//                                 Supplier not selected for:<br>
//                                 <b>${missing_supplier.join(', ')}</b>
//                             `
//                         });
//                         return;
//                     }

//                     // Dialog with items
//                     const dialog = new frappe.ui.Dialog({
//                         title: __('Select Items for PO'),
//                         size: 'extra-large',
//                         fields: [
//                             {
//                                 fieldname: 'items',
//                                 fieldtype: 'Table',
//                                 label: 'Items',
//                                 cannot_add_rows: true,
//                                 in_place_edit: false,
//                                 fields: [
//                                     {
//                                         fieldname: 'po_created',
//                                         fieldtype: 'Check',
//                                         label: 'PO Created',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'item_code',
//                                         fieldtype: 'Data',
//                                         label: 'Item Code',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'item_name',
//                                         fieldtype: 'Data',
//                                         label: 'Item Name',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'qty',
//                                         fieldtype: 'Float',
//                                         label: 'Qty',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     },
//                                     {
//                                         fieldname: 'supplier',
//                                         fieldtype: 'Link',
//                                         options: 'Supplier',
//                                         label: 'Supplier',
//                                         in_list_view: 1,
//                                         read_only: 1
//                                     }
//                                 ]
//                             }
//                         ],
//                         primary_action_label: __('Create PO'),
//                         primary_action() {
//                             const selected_items = dialog.fields_dict.items.grid
//                                 .get_selected_children()
//                                 .filter(row => !row._po_created);

//                             if (!selected_items.length) {
//                                 frappe.msgprint(__('Please select items without existing PO.'));
//                                 return;
//                             }

//                             const payload = selected_items.map(row => ({
//                                 item_code: row.item_code,
//                                 qty: row.qty,
//                                 supplier: row.supplier
//                             }));

//                             frappe.call({
//                                 method: 'auto_po_creation.api.create_purchase_orders',
//                                 args: {
//                                     material_request: frm.doc.name,
//                                     items: JSON.stringify(payload)
//                                 },
//                                 callback(res) {
//                                     if (!res.message) return;

//                                     let msg = `<b>PO created for following items:</b><br><br>`;

//                                     (res.message.created || []).forEach(po => {
//                                         msg += `
//                                             <b>PO:</b>
//                                             <a href="/app/purchase-order/${po.name}">
//                                                 ${po.name}
//                                             </a><br>
//                                             <b>Items:</b> ${po.items.join(', ')}<br><br>
//                                         `;
//                                     });

//                                     frappe.msgprint({
//                                         title: __('PO Creation Summary'),
//                                         indicator: 'green',
//                                         message: msg
//                                     });

//                                     dialog.hide();
//                                     frm.reload_doc();
//                                 }
//                             });
//                         }
//                     });

//                     // Load data
//                     dialog.fields_dict.items.df.data = table_data;
//                     dialog.fields_dict.items.grid.refresh();

//                     // Disable checkboxes for rows that already have PO
//                     setTimeout(() => {
//                         dialog.fields_dict.items.grid.grid_rows.forEach(r => {
//                             if (r.doc._po_created) {
//                                 r.$checkbox.prop('disabled', true);
//                                 r.$checkbox.prop('checked', false);
//                             }
//                         });
//                     }, 200);

//                     dialog.show();
//                 }
//             });
//         });
//     }
// });












function fetch_supplier_name_map(suppliers) {
    if (!suppliers.length) {
        return Promise.resolve({});
    }

    return frappe
        .call({
            method: 'auto_po_creation.api.get_supplier_name_map',
            args: { suppliers },
        })
        .then((r) => r.message || {});
}

function set_dialog_supplier_name(row, grid) {
    if (!row) return Promise.resolve();

    if (!row.supplier) {
        row.supplier_name = '';
        grid?.set_value('supplier_name', '', row);
        return Promise.resolve();
    }

    return frappe.db.get_value('Supplier', row.supplier, 'supplier_name').then((r) => {
        const supplier_name = r?.message?.supplier_name || '';
        row.supplier_name = supplier_name;
        grid?.set_value('supplier_name', supplier_name, row);
    });
}

function apply_supplier_names_to_table_data(table_data, name_map) {
    table_data.forEach((row) => {
        if (!row.supplier_name && row.supplier) {
            row.supplier_name = name_map[row.supplier] || '';
        }
    });
}

const MR_PO_CONFIG = {
    get_status_method: 'auto_po_creation.api.get_po_status',
    create_method: 'auto_po_creation.api.create_purchase_orders',
    dialog_title: __('Select Items for PO'),
    primary_label: __('Create PO'),
    created_label: __('PO Created'),
    empty_msg: __('Please select items without existing PO.'),
    freeze_msg: __('Creating Purchase Orders...'),
    summary_title: __('PO Creation Summary'),
    summary_heading: __('Purchase Orders Created:'),
    link_route: 'purchase-order',
    link_prefix: __('PO'),
};

const MR_SQ_CONFIG = {
    get_status_method: 'auto_po_creation.api.get_sq_status',
    create_method: 'auto_po_creation.api.create_supplier_quotations',
    dialog_title: __('Select Items for Supplier Quotation'),
    primary_label: __('Create Supplier Quotation'),
    created_label: __('Quotation Created'),
    empty_msg: __('Please select items without existing Supplier Quotation.'),
    freeze_msg: __('Creating Supplier Quotations...'),
    summary_title: __('Supplier Quotation Summary'),
    summary_heading: __('Supplier Quotations Created:'),
    link_route: 'supplier-quotation',
    link_prefix: __('Supplier Quotation'),
};

function get_mr_item_supplier(row) {
    return (
        row.custom_supplier_ ||
        row.supplier ||
        row.supplier_code ||
        row.default_supplier
    );
}

function open_mr_document_dialog(frm, config) {
    frappe.call({
        method: config.get_status_method,
        args: { material_request: frm.doc.name },
        callback(r) {
            const existing_items = r.message || [];
            const table_data = [];
            const missing_supplier = [];

            (frm.doc.items || []).forEach((row) => {
                const supplier = get_mr_item_supplier(row);

                if (!supplier) {
                    missing_supplier.push(row.item_code);
                    return;
                }

                const doc_created = existing_items.includes(row.item_code);

                table_data.push({
                    doc_created: doc_created ? 1 : 0,
                    _doc_created: doc_created,
                    item_code: row.item_code,
                    item_name: row.item_name,
                    qty: row.qty,
                    supplier: supplier,
                    supplier_name: row.custom_supplier_name || '',
                });
            });

            if (missing_supplier.length) {
                frappe.msgprint({
                    title: __('Supplier Missing'),
                    indicator: 'red',
                    message: `
                        Supplier not selected for:<br>
                        <b>${missing_supplier.join(', ')}</b>
                    `,
                });
                return;
            }

            const suppliers = [...new Set(table_data.map((row) => row.supplier))];

            fetch_supplier_name_map(suppliers).then((name_map) => {
                apply_supplier_names_to_table_data(table_data, name_map);
                show_mr_selection_dialog(frm, table_data, config);
            });
        },
    });
}

frappe.ui.form.on('Material Request', {
    refresh(frm) {
        if (frm.doc.__islocal || frm.doc.docstatus !== 1) return;

        if (frm.doc.material_request_type == "Purchase"){
            frm.add_custom_button(__('Auto Create PO'), () => {
                open_mr_document_dialog(frm, MR_PO_CONFIG);
            });
        }
    }
});

function show_mr_selection_dialog(frm, table_data, config) {
    const dialog = new frappe.ui.Dialog({
        title: config.dialog_title,
        size: 'extra-large',
        fields: [
            {
                fieldname: 'items',
                fieldtype: 'Table',
                label: 'Items',
                cannot_add_rows: true,
                cannot_delete_rows: true,
                in_place_edit: true,
                fields: [
                    {
                        fieldname: 'doc_created',
                        fieldtype: 'Check',
                        label: config.created_label,
                        in_list_view: 1,
                        read_only: 1
                    },
                    {
                        fieldname: 'item_code',
                        fieldtype: 'Data',
                        label: 'Item Code',
                        in_list_view: 1,
                        read_only: 1
                    },
                    {
                        fieldname: 'item_name',
                        fieldtype: 'Data',
                        label: 'Item Name',
                        in_list_view: 1,
                        read_only: 1
                    },
                    {
                        fieldname: 'qty',
                        fieldtype: 'Float',
                        label: 'Qty',
                        in_list_view: 1
                    },
                    {
                        fieldname: 'supplier',
                        fieldtype: 'Link',
                        options: 'Supplier',
                        label: 'Supplier Code',
                        in_list_view: 1
                    },
                    {
                        fieldname: 'supplier_name',
                        fieldtype: 'Data',
                        label: 'Supplier Name',
                        fetch_from: 'supplier.supplier_name',
                        in_list_view: 1,
                        read_only: 1
                    }
                ]
            }
        ],
        primary_action_label: config.primary_label,
        primary_action() {
            const selected_items = dialog.fields_dict.items.grid
                .get_selected_children()
                .filter((r) => !r._doc_created);

            if (!selected_items.length) {
                frappe.msgprint(config.empty_msg);
                return;
            }

            const payload = selected_items.map((r) => ({
                item_code: r.item_code,
                qty: r.qty,
                supplier: r.supplier
            }));

            frappe.call({
                method: config.create_method,
                args: {
                    material_request: frm.doc.name,
                    items: JSON.stringify(payload)
                },
                freeze: true,
                freeze_message: config.freeze_msg,
                callback(res) {
                    if (!res.message) return;

                    let msg = '';

                    if (res.message.created?.length) {
                        msg += `<b>${config.summary_heading}</b><br><br>`;
                        res.message.created.forEach((doc) => {
                            msg += `
                                <b>${config.link_prefix}:</b>
                                <a href="/app/${config.link_route}/${doc.name}" target="_blank">
                                    ${doc.name}
                                </a>
                                (${doc.supplier})<br>
                                <b>Items:</b> ${doc.items.join(', ')}<br><br>
                            `;
                        });
                    }

                    frappe.msgprint({
                        title: config.summary_title,
                        indicator: 'green',
                        message: msg
                    });

                    dialog.hide();
                    frm.reload_doc();
                }
            });
        },
        on_page_show() {
            const grid = dialog.fields_dict.items.grid;
            grid.df.data = table_data;
            grid.refresh();

            setTimeout(() => {
                grid.grid_rows.forEach((grid_row) => {
                    const supplier_name = grid_row.doc.supplier_name;
                    if (supplier_name) {
                        grid.set_value('supplier_name', supplier_name, grid_row.doc);
                    }
                });

                grid.grid_rows.forEach((r) => {
                    if (r.doc._doc_created && r.$checkbox) {
                        r.$checkbox.prop('disabled', true);
                        r.$row.addClass('text-muted');
                    }
                });
            }, 100);
        }
    });

    dialog.$wrapper.on(
        'change',
        'input[data-fieldname="supplier"]',
        function () {
            const $row = $(this).closest('.grid-row');
            if (!$row.length) return;

            const docname = $row.attr('data-name');
            const grid = dialog.fields_dict.items.grid;
            const row = grid.grid_rows_by_docname[docname]?.doc;
            if (!row) return;

            set_dialog_supplier_name(row, grid);
        }
    );

    dialog.show();
}
