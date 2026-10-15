# Copyright 2004-2009 Tiny SPRL (<http://tiny.be>).
# Copyright 2015 Agile Business Group <http://www.agilebg.com>
# Copyright 2016 Grupo ESOC Ingenieria de Servicios, S.L.U. - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
import secrets
import shutil
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta
from glob import iglob

import pysftp

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import UserError
from odoo.service import db

_logger = logging.getLogger(__name__)


class DbBackup(models.Model):
    _description = "Database Backup"
    _name = "db.backup"
    _inherit = "mail.thread"

    _name_unique = models.Constraint(
        "UNIQUE(name)",
        "Cannot duplicate a configuration.",
    )
    _days_to_keep_positive = models.Constraint(
        "CHECK(days_to_keep >= 0)",
        "I cannot remove backups from the future. Ask Doc for that.",
    )

    name = fields.Char(
        required=True,
        help="A label for this backup process.",
    )
    folder = fields.Char(
        default=lambda self: self._default_folder(),
        help="Absolute path for storing the backups",
        required=True,
    )
    days_to_keep = fields.Integer(
        required=True,
        default=0,
        help="Backups older than this will be deleted automatically. "
        "Set 0 to disable autodeletion.",
    )
    method = fields.Selection(
        [("local", "Local disk"), ("sftp", "Remote SFTP server")],
        default="local",
        help="Choose the storage method for this backup.",
    )
    sftp_host = fields.Char(
        "SFTP Server",
        help=(
            "The host name or IP address from your remote"
            " server. For example 192.168.0.1"
        ),
    )
    sftp_port = fields.Integer(
        "SFTP Port",
        default=22,
        help="The port on the FTP server that accepts SSH/SFTP calls.",
    )
    sftp_user = fields.Char(
        "Username in the SFTP Server",
        help=(
            "The username where the SFTP connection "
            "should be made with. This is the user on the external server."
        ),
    )
    sftp_password = fields.Char(
        "SFTP Password",
        help="The password for the SFTP connection. If you specify a private "
        "key file, then this is the password to decrypt it.",
    )
    # Non-stored input box: the real ``sftp_password`` is never sent to the
    # browser. Users click "Change Password" to reveal an empty box, type a new
    # value, and on save it is written into ``sftp_password``.
    sftp_password_input = fields.Char(
        string="New SFTP Password",
        store=False,
        help="Type a new SFTP password here; leave empty to keep the current "
        "one.",
    )
    sftp_password_edit = fields.Boolean(
        store=False,
        help="Reveals the password input when changing the SFTP password.",
    )
    sftp_password_set = fields.Boolean(
        string="Password is set",
        compute="_compute_sftp_password_set",
        help="Whether an SFTP password is currently stored.",
    )
    sftp_private_key = fields.Char(
        "Private key location",
        help="Path to the private key file. Only the Odoo user should have "
        "read permissions for that file.",
    )

    backup_format = fields.Selection(
        [
            ("zip", "zip (includes filestore)"),
            ("dump", "pg_dump custom format (without filestore)"),
        ],
        default="zip",
        help="Choose the format for this backup.",
    )

    email_notify = fields.Boolean(
        string="Auto e-mail on backup fail",
        help="If checked, an e-mail is sent to the address below whenever a "
        "backup fails.",
    )
    email_to_notify = fields.Char(
        string="Email to notify",
        help="E-mail address that receives a notification when a backup fails.",
    )

    download_enable = fields.Boolean(
        string="Enable public download",
        help="Serve this backup folder over HTTP so files can be downloaded "
        "with the link below, protected by the username and password. "
        "Local-disk backups only.",
    )
    download_token = fields.Char(
        string="Download token",
        default=lambda self: secrets.token_urlsafe(24),
        copy=False,
        readonly=True,
        help="Random, unguessable part of the download URL.",
    )
    download_user = fields.Char(
        string="Download username",
        help="Username required (HTTP Basic Auth) to download the backups.",
    )
    download_password = fields.Char(
        string="Download password",
        help="Password required (HTTP Basic Auth) to download the backups.",
    )
    download_url = fields.Char(
        string="Download URL",
        compute="_compute_download_url",
        help="Share this link to download the backups (requires the username "
        "and password above).",
    )

    last_backup_date = fields.Datetime(
        string="Last backup",
        readonly=True,
        help="When the most recent backup attempt ran (manual or scheduled).",
    )
    last_backup_status = fields.Selection(
        [("success", "Success"), ("failed", "Failed")],
        string="Last status",
        readonly=True,
        help="Outcome of the most recent backup attempt.",
    )
    last_backup_filename = fields.Char(
        string="Last file",
        readonly=True,
        help="File name of the most recent successful backup.",
    )
    last_backup_size = fields.Char(
        string="Last size",
        readonly=True,
        help="Size of the most recent successful backup.",
    )

    @staticmethod
    def _human_size(num_bytes):
        """Return a human-readable size string, e.g. '1.9 MB'."""
        if not num_bytes:
            return ""
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @api.depends("download_token", "download_enable", "method")
    def _compute_download_url(self):
        base = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("web.base.url", "")
            .rstrip("/")
        )
        for rec in self:
            if rec.download_enable and rec.method == "local" and rec.download_token:
                rec.download_url = f"{base}/auto_backup/download/{rec.download_token}"
            else:
                rec.download_url = False

    def action_reset_download_token(self):
        """Regenerate the token, invalidating any previously shared links."""
        for rec in self:
            rec.download_token = secrets.token_urlsafe(24)

    @api.depends("sftp_password")
    def _compute_sftp_password_set(self):
        for rec in self:
            rec.sftp_password_set = bool(rec.sftp_password)

    @staticmethod
    def _extract_sftp_password(vals):
        """Move a typed ``sftp_password_input`` into ``sftp_password``.

        The stored ``sftp_password`` is only written when the user actually
        typed a new value, so the real password is never overwritten by the
        (always-empty) input box.
        """
        if "sftp_password_input" in vals:
            new_password = vals.pop("sftp_password_input")
            if new_password:
                vals["sftp_password"] = new_password
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._extract_sftp_password(dict(v)) for v in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        return super().write(self._extract_sftp_password(dict(vals)))

    @api.model
    def _default_folder(self):
        """Default to ``backups`` folder inside current server datadir."""
        return os.path.join(tools.config["data_dir"], "backups", self.env.cr.dbname)

    @api.constrains("folder", "method")
    def _check_folder(self):
        """Do not use the filestore or you will backup your backups."""
        for record in self:
            if record.method == "local" and record.folder.startswith(
                tools.config.filestore(self.env.cr.dbname)
            ):
                raise exceptions.ValidationError(
                    self.env._(
                        "Do not save backups on your filestore, or you will "
                        "backup your backups too!"
                    )
                )

    def action_sftp_test_connection(self):
        """Check if the SFTP settings are correct."""
        try:
            # Just open and close the connection
            with self.sftp_connection():
                raise UserError(_("Connection Test Succeeded!"))
        except (
            pysftp.CredentialException,
            pysftp.ConnectionException,
            pysftp.SSHException,
        ) as exc:
            _logger.info("Connection Test Failed!", exc_info=True)
            raise UserError(self.env._("Connection Test Failed!")) from exc

    def action_backup(self):
        """Run selected backups."""
        backup = None
        successful = self.browse()

        # Start with local storage
        for rec in self.filtered(lambda r: r.method == "local"):
            filename = self.filename(
                datetime.now(), ext=rec.backup_format, db_name=self.env.cr.dbname
            )
            with rec.backup_log():
                # Directory must exist
                try:
                    os.makedirs(rec.folder, exist_ok=True)
                except OSError as exc:
                    _logger.exception(f"Action backup - OSError: {exc}")

                full_path = os.path.join(rec.folder, filename)
                with open(full_path, "wb") as destiny:
                    # Copy the cached backup
                    if backup:
                        with open(backup) as cached:
                            shutil.copyfileobj(cached, destiny)
                    # Generate new backup
                    else:
                        db.dump_db(
                            self.env.cr.dbname, destiny, backup_format=rec.backup_format
                        )
                        backup = backup or destiny.name
                rec._record_backup_file(filename, full_path)
                successful |= rec

        # Ensure a local backup exists if we are going to write it remotely
        sftp = self.filtered(lambda r: r.method == "sftp")
        if sftp:
            for rec in sftp:
                filename = self.filename(
                    datetime.now(), ext=rec.backup_format, db_name=self.env.cr.dbname
                )
                with rec.backup_log():
                    cached = db.dump_db(
                        self.env.cr.dbname, None, backup_format=rec.backup_format
                    )

                    with cached:
                        with rec.sftp_connection() as remote:
                            try:
                                remote.makedirs(rec.folder)
                            except pysftp.ConnectionException as exc:
                                _logger.exception(f"pysftp ConnectionException: {exc}")

                            # Copy cached backup to remote server. putfo enables
                            # paramiko write pipelining (many requests in flight),
                            # so throughput is bandwidth-bound instead of paying a
                            # network round-trip per 32 KB chunk; a plain
                            # open()+copyfileobj on a large dump over any latency
                            # is slow enough to exceed limit_time_real_cron and get
                            # the worker killed mid-transfer.
                            remote.putfo(
                                cached, os.path.join(rec.folder, filename)
                            )
                        rec._record_backup_file(filename, cached.name)
                        successful |= rec

        # Remove old files for successful backups
        successful.cleanup()

    @api.model
    def action_backup_all(self):
        """Run all scheduled backups."""
        return self.search([]).action_backup()

    def _record_backup_file(self, filename, path):
        """Store the file name and size of the last successful backup.

        Recording status must never break the backup itself: log and swallow.
        """
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        try:
            # sudo: cron/scheduled runs may execute with limited write rights.
            self.sudo().write(
                {
                    "last_backup_filename": filename,
                    "last_backup_size": self._human_size(size),
                }
            )
        except Exception:
            _logger.exception(f"Could not record last backup file: {self.name}")

    @contextmanager
    def backup_log(self):
        """Log a backup result."""
        try:
            _logger.info(f"Starting database backup: {self.name}")
            yield
        except Exception:
            _logger.exception(f"Database backup failed: {self.name}")
            self.sudo().write(
                {
                    "last_backup_date": fields.Datetime.now(),
                    "last_backup_status": "failed",
                }
            )
            escaped_tb = tools.html_escape(traceback.format_exc())
            self.message_post(  # pylint: disable=translation-required
                body=f"<p>{_('Database backup failed.')}</p><pre>{escaped_tb}</pre>",
                subtype_id=self.env.ref("auto_backup.mail_message_subtype_failure").id,
            )
            if self.email_notify and self.email_to_notify:
                self._send_failure_email(escaped_tb)
        else:
            _logger.info(f"Database backup succeeded: {self.name}")
            self.sudo().write(
                {
                    "last_backup_date": fields.Datetime.now(),
                    "last_backup_status": "success",
                }
            )
            self.message_post(body=_("Database backup succeeded."))

    def _send_failure_email(self, escaped_tb):
        """Send a failure-notification e-mail, if configured.

        Never let a mail error mask the original backup failure: log and swallow.
        """
        self.ensure_one()
        try:
            template = self.env.ref(
                "auto_backup.email_template_backup_failed", raise_if_not_found=False
            )
            if not template:
                _logger.warning("Backup failure e-mail template not found; skipping.")
                return
            template.with_context(backup_error=escaped_tb).send_mail(
                self.id, force_send=True
            )
        except Exception:
            _logger.exception(
                f"Could not send backup-failure notification e-mail: {self.name}"
            )

    def cleanup(self):
        """Clean up old backups."""
        now = datetime.now()
        db_name = self.env.cr.dbname
        for rec in self.filtered("days_to_keep"):
            with rec.cleanup_log():
                bu_format = rec.backup_format
                file_extension = "zip" if bu_format == "zip" else bu_format
                # Threshold filename in the SAME format as generated backups
                # (timestamp + _<db>.<ext>) so the leading-timestamp
                # lexicographic comparison stays valid.
                oldest = self.filename(
                    now - timedelta(days=rec.days_to_keep),
                    bu_format,
                    db_name=db_name,
                )
                suffix = f"_{db_name}.{file_extension}"

                if rec.method == "local":
                    for name in iglob(os.path.join(rec.folder, f"*{suffix}")):
                        if os.path.basename(name) < oldest:
                            os.unlink(name)

                elif rec.method == "sftp":
                    with rec.sftp_connection() as remote:
                        for name in remote.listdir(rec.folder):
                            if (
                                name.endswith(suffix)
                                and os.path.basename(name) < oldest
                            ):
                                remote.unlink(f"{rec.folder}/{name}")

    @contextmanager
    def cleanup_log(self):
        """Log a possible cleanup failure."""
        self.ensure_one()
        try:
            _logger.info(f"Starting cleanup process after database backup: {self.name}")
            yield
        except Exception:
            _logger.exception(f"Cleanup of old database backups failed: {self.name}")
            escaped_tb = tools.html_escape(traceback.format_exc())
            self.message_post(  # pylint: disable=translation-required
                body=(
                    f"<p>{_('Cleanup of old database backups failed.')}</p>"
                    f"<pre>{escaped_tb}</pre>"
                ),
                subtype_id=self.env.ref("auto_backup.failure").id,
            )
        else:
            _logger.info(f"Cleanup of old database backups succeeded: {self.name}")

    @staticmethod
    def filename(when, ext="zip", db_name=None):
        """Generate a file name for a backup.

        Format: ``<YYYY_MM_DD_HH_MM_SS>[_<db_name>].<ext>`` where ``ext`` is
        ``zip`` for the zip format and ``dump`` for the pg_dump format, e.g.
        ``2026_07_18_19_31_32_live_citam.zip``.

        :param datetime.datetime when:
            Use this datetime instead of :meth:`datetime.datetime.now`.
        :param str ext: Backup format, ``"zip"`` or ``"dump"``.
        :param str db_name: Database name to append to the file name.
        """
        file_ext = "zip" if ext == "zip" else ext
        suffix = f"_{db_name}" if db_name else ""
        return "{:%Y_%m_%d_%H_%M_%S}{suffix}.{ext}".format(
            when, suffix=suffix, ext=file_ext
        )

    def sftp_connection(self):
        """Return a new SFTP connection with found parameters."""
        self.ensure_one()
        # Disable pysftp host-key verification: the module connects to
        # user-configured backup servers whose host key is usually not present
        # in the Odoo user's known_hosts, which would otherwise raise
        # "No hostkey for host ... found." on the first connection.
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        params = {
            "host": self.sftp_host,
            "username": self.sftp_user,
            "port": self.sftp_port,
            "cnopts": cnopts,
        }
        _logger.debug(
            "Trying to connect to sftp://%(username)s@%(host)s:%(port)d",
            {
                "username": self.sftp_user,
                "host": self.sftp_host,
                "port": self.sftp_port,
            },
        )
        if self.sftp_private_key:
            params["private_key"] = self.sftp_private_key
            if self.sftp_password:
                params["private_key_pass"] = self.sftp_password
        else:
            params["password"] = self.sftp_password

        conn = pysftp.Connection(**params)
        # Bound each SFTP read/write on the channel so a stalled transfer raises
        # (and is caught/logged by backup_log) instead of hanging until the cron
        # worker hits limit_time_real_cron and is killed with no log at all.
        conn.timeout = 300
        return conn
