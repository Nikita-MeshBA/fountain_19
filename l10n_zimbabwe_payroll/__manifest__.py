{
    "name": "l10n Zimbabwe Payroll",
    "summary": "l10n Zimbabwe Payroll",
    "category": "Payroll",
    "sequence": 3,
    "version": "19.0.0.0.0",
    "license": "LGPL-3",
    "author": "Sybyl",
    # "depends": ["hr", "hr_contract", "hr_payroll_community"],
    "depends": ["hr", "hr_payroll_community"],

    "data": [
        "security/ir.model.access.csv",
        "data/hr_payroll_data.xml",
        "views/hr_employee.xml",
        "views/hr_contract_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
