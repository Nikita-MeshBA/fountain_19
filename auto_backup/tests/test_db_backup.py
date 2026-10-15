# Copyright 2015 Agile Business Group <http://www.agilebg.com>
# Copyright 2015 Alessio Gerace <alesiso.gerace@agilebg.com>
# Copyright 2016 Grupo ESOC Ingenieria de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import PropertyMock, patch

import pysftp

from odoo import tools
from odoo.exceptions import UserError
from odoo.tests import common

_logger = logging.getLogger(__name__)


model = "odoo.addons.auto_backup.models.db_backup"
class_name = f"{model}.DbBackup"


class TestConnectionException(pysftp.ConnectionException):
    def __init__(self):
        super().__init__("test", "test")


class TestDbBackup(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["db.backup"]

    @contextmanager
    def mock_assets(self):
        """It provides mocked core assets"""
        self.path_join_val = "/this/is/a/path"
        with patch(f"{model}.db") as db:
            with patch(f"{model}.os") as os:
                with patch(f"{model}.shutil") as shutil:
                    os.path.join.return_value = self.path_join_val
                    yield {
                        "db": db,
                        "os": os,
                        "shutil": shutil,
                    }

    @contextmanager
    def patch_filtered_sftp(self, record):
        """It patches filtered record and provides a mock"""
        with patch(f"{class_name}.filtered") as filtered:
            filtered.side_effect = [], [record]
            with patch(f"{class_name}.backup_log"):
                with patch(f"{class_name}.sftp_connection"):
                    yield filtered

    def new_record(self, method="sftp"):
        # ``name`` is a plain, required, user-provided label.
        vals = {"name": "Têst backup", "method": method, "days_to_keep": 1}
        if method == "sftp":
            vals.update(
                {
                    "sftp_host": "test_host",
                    "sftp_port": "222",
                    "sftp_user": "tuser",
                    "sftp_password": "password",
                    "folder": "/folder/",
                }
            )
        self.vals = vals
        return self.Model.create(vals)

    def test_name_is_manual(self):
        """The name is the plain value the user provided (no auto-fill)"""
        rec_id = self.new_record()
        self.assertEqual(rec_id.name, "Têst backup")
        # editing the folder must not change the name
        rec_id.write({"folder": "/some/other/path/"})
        self.assertEqual(rec_id.name, "Têst backup")

    def test_name_is_required(self):
        """Creating a backup without a name is rejected"""
        from psycopg2 import IntegrityError

        from odoo.tools import mute_logger

        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Model.create({"method": "local", "days_to_keep": 1})

    def test_check_folder(self):
        """It should not allow recursive backups"""
        rec_id = self.new_record("local")
        with self.assertRaises(UserError):
            rec_id.write(
                {
                    "folder": (
                        f"{tools.config.filestore(self.env.cr.dbname)}" "/another/path"
                    ),
                }
            )

    @patch(f"{model}._")
    def test_action_sftp_test_connection_success(self, _):
        """It should raise connection succeeded warning"""
        with patch(f"{class_name}.sftp_connection", new_callable=PropertyMock):
            rec_id = self.new_record()
            with self.assertRaises(UserError):
                rec_id.action_sftp_test_connection()
        _.assert_called_once_with("Connection Test Succeeded!")

    @patch(f"{model}._")
    def _test_action_sftp_test_connection_fail(self, _):
        """It should raise connection fail warning"""
        with patch(f"{class_name}.sftp_connection", new_callable=PropertyMock) as conn:
            rec_id = self.new_record()
            conn().side_effect = TestConnectionException
            with self.assertRaises(UserError):
                rec_id.action_sftp_test_connection()
            _.assert_called_once_with("Connection Test Failed!")

    def test_action_backup_local(self):
        """It should backup local database"""
        rec_id = self.new_record("local")
        db_name = self.env.cr.dbname
        filename = rec_id.filename(datetime.now(), db_name=db_name)
        rec_id.action_backup()
        generated_backup = [f for f in os.listdir(rec_id.folder) if f >= filename]
        self.assertEqual(1, len(generated_backup))
        # file name embeds the database name
        self.assertTrue(all(db_name in f for f in os.listdir(rec_id.folder)))

    def test_filename_contains_db_name(self):
        """The generated file name embeds the database name and .zip ext"""
        res = self.Model.filename(datetime.now(), ext="zip", db_name="live_citam")
        self.assertTrue(res.endswith("_live_citam.zip"))
        res = self.Model.filename(datetime.now(), ext="dump", db_name="live_citam")
        self.assertTrue(res.endswith("_live_citam.dump"))

    def test_last_backup_status_success(self):
        """A successful backup records date/status/file/size"""
        rec = self.new_record("local")
        rec.action_backup()
        self.assertEqual(rec.last_backup_status, "success")
        self.assertTrue(rec.last_backup_date)
        self.assertTrue(rec.last_backup_filename.endswith(".zip"))
        self.assertIn(self.env.cr.dbname, rec.last_backup_filename)
        self.assertTrue(rec.last_backup_size)

    def test_last_backup_status_failed(self):
        """A failed backup records status=failed and a date"""
        rec = self.new_record("local")
        with rec.backup_log():
            raise RuntimeError("boom")
        self.assertEqual(rec.last_backup_status, "failed")
        self.assertTrue(rec.last_backup_date)

    def test_human_size(self):
        """_human_size formats bytes to a readable string"""
        self.assertEqual(self.Model._human_size(0), "")
        self.assertEqual(self.Model._human_size(512), "512 B")
        self.assertEqual(self.Model._human_size(1536), "1.5 KB")
        self.assertTrue(self.Model._human_size(5 * 1024 * 1024).endswith("MB"))

    def test_action_backup_local_cleanup(self):
        """Backup local database and cleanup old databases"""
        rec_id = self.new_record("local")
        db_name = self.env.cr.dbname
        old_date = datetime.now() - timedelta(days=3)
        filename = rec_id.filename(old_date, db_name=db_name)
        with patch(f"{model}.datetime") as mock_date:
            mock_date.now.return_value = old_date
            rec_id.action_backup()
        generated_backup = [f for f in os.listdir(rec_id.folder) if f >= filename]
        self.assertEqual(2, len(generated_backup))

        filename = rec_id.filename(datetime.now(), db_name=db_name)
        rec_id.action_backup()
        generated_backup = [f for f in os.listdir(rec_id.folder) if f >= filename]
        self.assertEqual(1, len(generated_backup))

    def _test_action_backup_sftp_mkdirs(self):
        """It should create remote dirs"""
        rec_id = self.new_record()
        with self.mock_assets():
            with self.patch_filtered_sftp(rec_id):
                with patch(f"{class_name}.cleanup", new_callable=PropertyMock):
                    conn = rec_id.sftp_connection().__enter__()
                    rec_id.action_backup()
                    conn.makedirs.assert_called_once_with(rec_id.folder)

    def _test_action_backup_sftp_mkdirs_conn_exception(self):
        """It should guard from ConnectionException on remote.mkdirs"""
        rec_id = self.new_record()
        with self.mock_assets():
            with self.patch_filtered_sftp(rec_id):
                with patch(f"{class_name}.cleanup", new_callable=PropertyMock):
                    conn = rec_id.sftp_connection().__enter__()
                    conn.makedirs.side_effect = TestConnectionException
                    rec_id.action_backup()
                    # No error was raised, test pass
                    self.assertTrue(True)

    def test_action_backup_sftp_remote_open(self):
        """It should open remote file w/ proper args"""
        rec_id = self.new_record()
        with self.mock_assets() as assets:
            with self.patch_filtered_sftp(rec_id):
                with patch(f"{class_name}.cleanup", new_callable=PropertyMock):
                    conn = rec_id.sftp_connection().__enter__()
                    rec_id.action_backup()
                    conn.open.assert_called_once_with(assets["os"].path.join(), "wb")

    def test_action_backup_sftp_uses_large_buffer(self):
        """Large-DB hardening: SFTP upload copies with the big buffer"""
        from odoo.addons.auto_backup.models.db_backup import SFTP_COPY_BUFFER

        rec_id = self.new_record()
        with self.mock_assets() as assets:
            with self.patch_filtered_sftp(rec_id):
                with patch(f"{class_name}.cleanup", new_callable=PropertyMock):
                    rec_id.sftp_connection().__enter__()
                    rec_id.action_backup()
                    # last positional arg to copyfileobj is the buffer size
                    _, args, _kwargs = assets["shutil"].copyfileobj.mock_calls[-1]
                    self.assertEqual(args[-1], SFTP_COPY_BUFFER)

    def test_action_backup_all_search(self):
        """It should search all records"""
        rec_id = self.new_record()
        with patch(f"{class_name}.search", new_callable=PropertyMock):
            rec_id.action_backup_all()
            rec_id.search.assert_called_once_with([])

    def test_action_backup_all_return(self):
        """It should return result of backup operation"""
        rec_id = self.new_record()
        with patch(f"{class_name}.search", new_callable=PropertyMock):
            res = rec_id.action_backup_all()
            self.assertEqual(rec_id.search().action_backup(), res)

    @patch(f"{model}.pysftp")
    def test_sftp_connection_init_passwd(self, pysftp):
        """It should initiate SFTP connection w/ proper args and pass"""
        rec_id = self.new_record()
        rec_id.sftp_connection()
        pysftp.Connection.assert_called_once_with(
            host=rec_id.sftp_host,
            username=rec_id.sftp_user,
            port=rec_id.sftp_port,
            cnopts=pysftp.CnOpts.return_value,
            password=rec_id.sftp_password,
        )
        # host-key verification disabled
        self.assertIsNone(pysftp.CnOpts.return_value.hostkeys)

    @patch(f"{model}.pysftp")
    def test_sftp_connection_init_key(self, pysftp):
        """It should initiate SFTP connection w/ proper args and key"""
        rec_id = self.new_record()
        rec_id.write({"sftp_private_key": "pkey", "sftp_password": "pkeypass"})
        rec_id.sftp_connection()
        pysftp.Connection.assert_called_once_with(
            host=rec_id.sftp_host,
            username=rec_id.sftp_user,
            port=rec_id.sftp_port,
            cnopts=pysftp.CnOpts.return_value,
            private_key=rec_id.sftp_private_key,
            private_key_pass=rec_id.sftp_password,
        )

    @patch(f"{model}.pysftp")
    def test_sftp_connection_return(self, pysftp):
        """It should return new sftp connection"""
        rec_id = self.new_record()
        res = rec_id.sftp_connection()
        self.assertEqual(
            pysftp.Connection(),
            res,
        )

    @patch(f"{model}.pysftp")
    def test_sftp_connection_sets_timeout_keepalive(self, pysftp):
        """Large-DB hardening: connection gets a timeout and keepalive"""
        from odoo.addons.auto_backup.models.db_backup import (
            SFTP_KEEPALIVE,
            SFTP_TIMEOUT,
        )

        rec_id = self.new_record()
        conn = pysftp.Connection.return_value
        rec_id.sftp_connection()
        self.assertEqual(conn.timeout, SFTP_TIMEOUT)
        conn._transport.set_keepalive.assert_called_once_with(SFTP_KEEPALIVE)

    def test_sftp_password_input_sets_password(self):
        """Typing a new password via the input box updates the stored one"""
        rec = self.new_record()  # sftp, password 'password'
        rec.write({"sftp_password_input": "newsecret"})
        self.assertEqual(rec.sftp_password, "newsecret")
        self.assertTrue(rec.sftp_password_set)

    def test_sftp_password_input_empty_keeps_password(self):
        """An empty input box must not wipe the stored password"""
        rec = self.new_record()
        rec.write({"sftp_password_input": False})
        self.assertEqual(rec.sftp_password, "password")
        rec.write({"sftp_password_input": ""})
        self.assertEqual(rec.sftp_password, "password")

    def test_sftp_password_edit_toggle_not_persisted(self):
        """The edit toggle is transient (non-stored) and never written to DB"""
        rec = self.new_record()
        self.assertFalse(rec.sftp_password_edit)
        rec.sftp_password_edit = True
        self.assertTrue(rec.sftp_password_edit)
        # reload from DB: transient flag is not persisted
        rec.invalidate_recordset(["sftp_password_edit"])
        self.assertFalse(rec.sftp_password_edit)

    def test_filename_default(self):
        """It should not error and should return a .zip file str"""
        now = datetime.now()
        res = self.Model.filename(now)
        self.assertTrue(res.endswith(".zip"))

    def test_filename_zip(self):
        """It should return a .zip filename"""
        now = datetime.now()
        res = self.Model.filename(now, ext="zip")
        self.assertTrue(res.endswith(".zip"))

    def test_filename_dump(self):
        """It should return a .dump filename"""
        now = datetime.now()
        res = self.Model.filename(now, ext="dump")
        self.assertTrue(res.endswith(".dump"))

    def _fail_in_backup_log(self, rec):
        """Run a failing block through backup_log to exercise the failure path."""
        with rec.backup_log():
            raise RuntimeError("boom")

    def test_failure_email_sent_when_enabled(self):
        """It should send a failure e-mail when notify is on and address set"""
        rec = self.new_record("local")
        rec.write({"email_notify": True, "email_to_notify": "ops@example.com"})
        with patch(f"{class_name}._send_failure_email") as send:
            self._fail_in_backup_log(rec)
            send.assert_called_once()

    def test_failure_email_not_sent_when_disabled(self):
        """It should not send a failure e-mail when notify is off"""
        rec = self.new_record("local")
        rec.write({"email_notify": False, "email_to_notify": "ops@example.com"})
        with patch(f"{class_name}._send_failure_email") as send:
            self._fail_in_backup_log(rec)
            send.assert_not_called()

    def test_failure_email_not_sent_when_no_address(self):
        """It should not send (and not crash) when notify on but address blank"""
        rec = self.new_record("local")
        rec.write({"email_notify": True, "email_to_notify": False})
        with patch(f"{class_name}._send_failure_email") as send:
            self._fail_in_backup_log(rec)
            send.assert_not_called()

    def test_success_does_not_send_email(self):
        """It should not send a failure e-mail on a successful backup"""
        rec = self.new_record("local")
        rec.write({"email_notify": True, "email_to_notify": "ops@example.com"})
        with patch(f"{class_name}._send_failure_email") as send:
            with rec.backup_log():
                pass  # no exception -> success branch
            send.assert_not_called()

    def test_send_failure_email_uses_template(self):
        """_send_failure_email renders the template with the traceback context"""
        rec = self.new_record("local")
        rec.write({"email_notify": True, "email_to_notify": "ops@example.com"})
        template = self.env.ref("auto_backup.email_template_backup_failed")
        with patch.object(type(template), "send_mail") as send_mail:
            rec._send_failure_email("escaped-traceback")
            send_mail.assert_called_once()
            # res_id is the record, force_send requested
            args, kwargs = send_mail.call_args
            self.assertEqual(args[0], rec.id)
            self.assertTrue(kwargs.get("force_send"))

    def test_send_failure_email_swallows_errors(self):
        """A mail error must not propagate out of _send_failure_email"""
        rec = self.new_record("local")
        rec.write({"email_notify": True, "email_to_notify": "ops@example.com"})
        template = self.env.ref("auto_backup.email_template_backup_failed")
        with patch.object(
            type(template), "send_mail", side_effect=RuntimeError("smtp down")
        ):
            # Should not raise
            rec._send_failure_email("escaped-traceback")
