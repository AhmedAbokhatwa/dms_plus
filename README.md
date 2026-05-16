<div align="center">
  <img src="dms.png" alt="DMS Plus Logo" width="200">

# DMS Plus

**A full-featured ERPNext customization app built for Digital Myth Solutions**

Custom Frappe app — Quotation Workflows · Role-Based Permissions · Sales Reporting · Print Formats · Saudi Arabia ERPNext

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Frappe](https://img.shields.io/badge/Built%20on-Frappe%20Framework-00BCD4)](https://frappeframework.com)
[![ERPNext](https://img.shields.io/badge/ERPNext-Compatible-2490EF)](https://erpnext.com)

</div>

---

## Overview

**DMS Plus** is a custom Frappe ERPNext application developed for [Digital Myth Solutions (DMS)](https://dms-ksa.com) — a Saudi-based technology solutions provider. The app extends ERPNext with advanced sales workflows, role-based access control, quotation performance tracking, and Arabic-ready print formats.

Built on the Frappe Framework, DMS Plus integrates tightly with ERPNext's core Sales, CRM, Inventory, and Finance modules to automate business processes and enforce company-specific rules without modifying the ERPNext core.

---

## Features

### 1. Quotation Approval Workflow

A multi-stage approval workflow for ERPNext Quotations with conditional routing based on discount rate and order value.

**Workflow States:**

| State | Doc Status | Editable By |
|---|---|---|
| Draft | 0 | All |
| Pending Approval | 0 | Sales Manager |
| Rejected | 0 | Sales Manager |
| Approved | 1 | Sales Manager |
| Cancelled | 2 | All |
| Pending Director Approval | 0 | Sales Master Manager |
| Pending CEO Approval | 0 | CEO |

**Routing Logic:**

- Quotations with `avg_discount_rate <= 3` and `base_total <= 50,000 SR` → Auto-approved on submit
- Quotations exceeding thresholds → Routed to Sales Manager for approval
- High-value or high-discount quotes → Escalated to Director or CEO
- Junior Sales: quotes above 75,000 SR require Sales Manager approval
- Senior Sales: quotes above 150,000 SR require Sales Manager approval

### 2. Role-Based Permissions System

Granular, department-level permissions enforced across all ERPNext modules.

**Sales Roles:**

- **Junior Sales** — Create own quotations, max 5% discount, no Professional Services items
- **Senior Sales** — Max 10% discount, all item types, price list selection
- **Sales Coordinator** — Full customer assignment, reporting access, no discount approval
- **Sales Manager** — Full override, approval rights, all reports
- **Product Manager** — Full pricing control for their product category

**Other Roles:**

- **Warehouse Employee** — View quotes and orders, update stock, no financial edits
- **Technical Manager** — View all technical tasks, assign to Technical Team only
- **Technician** — View and update assigned tasks only
- **Accountant / Accounting Manager** — Invoice creation, payment recording, financial reports

### 3. Quotation Planning vs Actual Report

A pipeline performance report comparing planned sales targets against actual quotation and sales order results.

**Report Features:**

- Hierarchical view: Quotation Planning → Monthly Plan → Individual Quotations
- Automatic calculation of variance (SAR) and achievement percentage
- Status indicators: Planned / Partially Achieved / Achieved / Over Achieved
- Dynamic bar and line charts for monthly performance trends
- Filters: Month, Year, Product Manager, Territory
- Integrated with ERPNext Dashboard via `get_summary_data` and `get_chart_data` helpers

**Data Flow:**

1. Product Manager creates a **Quotation Planning** record with monthly targets
2. On Quotation submission → system auto-generates **Quotation Monthly Plan** records per item
3. On Sales Order submission → system updates actual amounts and recalculates status
4. Report pulls from all three doctypes in real time

### 4. Quotation Follow-Up Tracking

Track the status and follow-up history of open quotations. Helps sales teams manage pipeline and reduce lost opportunities.

### 5. Custom Print Formats

Arabic-ready print formats for:

- Sales Quotations
- Sales Orders
- Purchase Orders
- Sales Invoices

Formatted for Saudi Arabia business standards with company letterhead, VAT number, and CR number support. Compatible with DMS's Saudi VAT compliance setup.

### 6. Department-Based Data Isolation

Sales teams operate in isolated data scopes:

- **Team 1:** Sales Manager Amal → Coordinator Sara → Senior Ali → Junior Ahmed
- **Team 2:** Sales Manager Rania → Coordinator Samy → Senior Eslam → Junior Mohamed

Each team member sees only records within their hierarchy. Managers have cross-team visibility.

---

## Tech Stack

- **Backend:** Python, Frappe Framework, ERPNext
- **Frontend:** Vue.js, Frappe UI
- **Database:** MariaDB
- **Infrastructure:** Linux, NGINX, Supervisor
- **Region:** Saudi Arabia — VAT-compliant, Arabic RTL support

---

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/AhmedAbokhatwa/dms_plus --branch develop
bench --site <YOUR_SITE> install-app dms_plus
```

---

## Screenshots

> Coming soon — sales dashboard, quotation workflow, and report views.

---

## Contributing

This app uses `pre-commit` for code formatting and linting.

```bash
cd apps/dms_plus
pre-commit install
```

Tools configured: `ruff`, `eslint`, `prettier`, `pyupgrade`

---

## License

MIT — see [LICENSE](LICENSE)

---

*Custom ERPNext App · Frappe Framework · Saudi Arabia · Quotation Workflow · Role-Based Permissions · Sales Reporting · Arabic Print Formats*
