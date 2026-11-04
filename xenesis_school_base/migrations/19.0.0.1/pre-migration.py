# hr.employee.partner_id is required, but 17.0 never filled it (every employee had NULL), so the
# NOT NULL constraint could not be applied. Default it to the employee's work contact before the
# module update creates the constraint.


def migrate(cr, version):
    cr.execute(
        """
        UPDATE hr_employee
           SET partner_id = work_contact_id
         WHERE partner_id IS NULL AND work_contact_id IS NOT NULL
        """
    )
