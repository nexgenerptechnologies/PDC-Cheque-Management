app_name = "pdc_cheque_management"
app_title = "PDC Cheque Management"
app_publisher = "Antigravity"
app_description = "Advanced PDC Management and Automated Bank Reconciliation"
app_email = "support@antigravity.ai"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/pdc_cheque_management/css/pdc_style.css"

# DocType Events
# ---------------
# doc_events = {
#     "PDC Cheque": {
#         "validate": "pdc_management.pdc.doctype.pdc_cheque.pdc_cheque.validate"
#     }
# }

required_apps = ["frappe >=15.0.0 <16.0.0", "erpnext >=15.0.0 <16.0.0"]

