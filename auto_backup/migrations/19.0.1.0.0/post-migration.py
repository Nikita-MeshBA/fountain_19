# The 17.0 module scheduled ``model.schedule_backup()`` through ``auto_backup.backup_scheduler``.
# 19.0 replaced it with ``ir_cron_backup_scheduler_0`` (``action_backup_all``); the old record
# was noupdate, so it survives the upgrade and fails every day. Remove it.


def migrate(cr, version):
    cr.execute(
        """
        SELECT c.id, c.ir_actions_server_id FROM ir_cron c
          JOIN ir_model_data d ON d.res_id = c.id AND d.model = 'ir.cron'
         WHERE d.module = 'auto_backup' AND d.name = 'backup_scheduler'
        """
    )
    for cron_id, action_id in cr.fetchall():
        cr.execute("DELETE FROM ir_cron WHERE id = %s", (cron_id,))
        cr.execute("DELETE FROM ir_act_server WHERE id = %s", (action_id,))
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = 'auto_backup'"
        " AND name IN ('backup_scheduler', 'backup_scheduler_ir_actions_server')"
    )
