import logging
from frappe.desk.doctype.workspace.workspace import last_sequence_id
from frappe.desk.doctype.desktop_icon.desktop_icon import add_workspace_to_desktop
import frappe
from json import loads

WORKSPACE_NAME = "DMS"

WORKSPACE_DEF = {
	"app": "dms_plus",
	"charts": [],
	"content": "[{\"id\":\"Qm4MoEdeYQ\",\"type\":\"header\",\"data\":{\"text\":\"<span class=\\\"h4\\\">Welcome to the DMS workspace</span>\",\"col\":12}},{\"id\":\"qaJMEJvX-S\",\"type\":\"paragraph\",\"data\":{\"text\":\"Click on \\n\\t\\t\\t\\n\\t\\t\\t\\n\\t\\t to edit\",\"col\":12}},{\"id\":\"5IPUbQcD6W\",\"type\":\"card\",\"data\":{\"card_name\":\"Reports\",\"col\":4}}]",
	"custom_blocks": [],
	"docstatus": 0,
	"doctype": "Workspace",
	"hide_custom": 0,
	"icon": "alarm-clock-minus",
	"idx": 0,
	"indicator_color": "green",
	"is_hidden": 0,
	"label": "DMS",
	"link_type": "DocType",
	"links": [
		{
		"hidden": 0,
		"is_query_report": 0,
		"label": "Reports",
		"link_count": 1,
		"link_type": "DocType",
		"onboard": 0,
		"type": "Card Break"
		},
		{
		"hidden": 0,
		"is_query_report": 1,
		"label": "Quotation Follow-up",
		"link_count": 0,
		"link_to": "Quotation Follow-up",
		"link_type": "Report",
		"onboard": 0,
		"type": "Link"
		}
		],
		"module": "dms_plus",
		"name": "DMS",
		"number_cards": [],
		"owner": "Administrator",
		"parent_page": "",
		"public": 1,
		"quick_lists": [],
		"roles": [],
		"sequence_id": 29.0,
		"shortcuts": [],
		"title": "DMS",
		"type": "Workspace"
}


def execute():
	"""Reinstall DMS Plus workspace."""
	logger = frappe.logger("dms_workspace")
	logger.setLevel(logging.DEBUG)

	_remove_workspace(logger)
	_install_workspace(logger)


def _remove_workspace(logger):
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		logger.debug(f"Workspace '{WORKSPACE_NAME}' does not exist, skipping removal")
		return

	try:
		frappe.delete_doc("Workspace", WORKSPACE_NAME, force=True, ignore_permissions=True)
		logger.info(f"Removed workspace: {WORKSPACE_NAME}")
	except Exception:
		frappe.log_error(
			title=f"Failed to Remove Workspace: {WORKSPACE_NAME}",
			message=frappe.get_traceback(),
		)


def _install_workspace(logger):
	try:
		doc = frappe.get_doc(WORKSPACE_DEF)
		doc.sequence_id = last_sequence_id(doc) + 1
		doc.insert(ignore_permissions=True)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		logger.info(f"Installed workspace: {WORKSPACE_NAME}")
		add_workspace_to_desktop(doc.name)
	except Exception:
		frappe.log_error(
			title=f"Failed to Install Workspace: {WORKSPACE_NAME}",
			message=frappe.get_traceback(),
		)
