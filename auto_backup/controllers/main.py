# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import binascii
import hmac
import mimetypes
import os
from datetime import datetime
from zlib import adler32

import werkzeug.exceptions
from markupsafe import escape

from odoo import http
from odoo.http import Stream, request

_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Database Auto-Backup — {config}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: #f4f5f7; color: #1f2937;
  }}
  .wrap {{ max-width: 860px; margin: 0 auto; padding: 32px 20px; }}
  header {{
    display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
  }}
  .logo {{
    width: 42px; height: 42px; border-radius: 10px; flex: none;
    background: linear-gradient(135deg, #714B67, #a56b8f);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 22px;
  }}
  h1 {{ font-size: 20px; margin: 0; }}
  .brand {{ color: #714B67; font-weight: 700; }}
  .sub {{ color: #6b7280; font-size: 13px; margin: 2px 0 24px; }}
  .card {{
    background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,.04);
  }}
  .card-head {{
    padding: 14px 18px; border-bottom: 1px solid #eef0f2;
    font-weight: 600; display: flex; justify-content: space-between; align-items: center;
  }}
  .count {{ color: #6b7280; font-weight: 400; font-size: 13px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 12px 18px; font-size: 14px; }}
  thead th {{ color: #6b7280; font-weight: 600; font-size: 12px;
    text-transform: uppercase; letter-spacing: .03em; border-bottom: 1px solid #eef0f2; }}
  tbody tr:not(:last-child) td {{ border-bottom: 1px solid #f3f4f6; }}
  td.name {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; word-break: break-all; }}
  td.size, td.date {{ color: #6b7280; white-space: nowrap; }}
  td.dl {{ text-align: right; }}
  .btn {{
    display: inline-block; padding: 6px 14px; border-radius: 8px;
    background: #714B67; color: #fff; text-decoration: none; font-size: 13px; font-weight: 600;
  }}
  .btn:hover {{ background: #5d3d55; }}
  .empty {{ padding: 32px 18px; color: #6b7280; text-align: center; }}
  footer {{ text-align: center; color: #9ca3af; font-size: 12px; margin-top: 20px; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #111418; color: #e5e7eb; }}
    .card {{ background: #1b1f24; border-color: #2a2f36; }}
    .card-head {{ border-color: #2a2f36; }}
    thead th {{ border-color: #2a2f36; }}
    tbody tr:not(:last-child) td {{ border-color: #23282e; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="logo">&#128190;</div>
      <div>
        <h1><span class="brand">Database Auto-Backup</span></h1>
      </div>
    </header>
    <div class="sub">Backups for configuration: <strong>{config}</strong></div>
    <div class="card">
      <div class="card-head">
        <span>Backup files</span>
        <span class="count">{count} file(s)</span>
      </div>
      {table}
    </div>
    <footer>Database Auto-Backup · secure download</footer>
  </div>
</body>
</html>"""


def _unauthorized():
    """Return a 401 that makes the browser show the Basic Auth prompt."""
    return request.make_response(
        "Authentication required.",
        status=401,
        headers=[
            ("WWW-Authenticate", 'Basic realm="Auto Backup"'),
            ("Content-Type", "text/plain; charset=utf-8"),
        ],
    )


class AutoBackupDownload(http.Controller):
    """Serve a backup config's local folder over HTTP with Basic Auth.

    Access is gated by:
      * an unguessable per-config ``download_token`` in the URL,
      * a per-config ``download_enable`` flag,
      * HTTP Basic Auth against ``download_user`` / ``download_password``.
    Only ``method == 'local'`` configs are served.
    """

    def _authenticate(self, token):
        """Return the enabled db.backup record for ``token`` or raise NotFound.

        On a bad/missing Basic Auth header, returns None to signal that a 401
        must be sent (caller distinguishes via the sentinel).
        """
        rec = (
            request.env["db.backup"]
            .sudo()
            .search([("download_token", "=", token)], limit=1)
        )
        # Reveal nothing about disabled / non-local / unknown configs.
        if not token or not rec or not rec.download_enable or rec.method != "local":
            raise werkzeug.exceptions.NotFound()

        header = request.httprequest.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return None
        try:
            raw = base64.b64decode(header[6:].strip()).decode("utf-8")
            user, _, password = raw.partition(":")
        except (binascii.Error, UnicodeDecodeError):
            return None

        expected_user = rec.download_user or ""
        expected_password = rec.download_password or ""
        # Credentials must be configured, and matched in constant time.
        user_ok = hmac.compare_digest(user, expected_user)
        password_ok = hmac.compare_digest(password, expected_password)
        if not (expected_user and expected_password and user_ok and password_ok):
            return None
        return rec

    @staticmethod
    def _safe_full_path(rec, filename):
        """Return an absolute path inside rec.folder, or None if unsafe."""
        if (
            not filename
            or "/" in filename
            or "\\" in filename
            or ".." in filename
            or "\x00" in filename
        ):
            return None
        base = os.path.realpath(rec.folder)
        full = os.path.realpath(os.path.join(base, filename))
        # Must stay within the configured folder and be a real file.
        if os.path.commonpath([full, base]) != base or not os.path.isfile(full):
            return None
        return full

    @http.route(
        "/auto_backup/download/<string:token>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
        sitemap=False,
    )
    def index(self, token, **kwargs):
        rec = self._authenticate(token)
        if rec is None:
            return _unauthorized()

        files = []
        try:
            for name in sorted(os.listdir(rec.folder), reverse=True):
                path = os.path.join(rec.folder, name)
                if os.path.isfile(path):
                    stat = os.stat(path)
                    files.append((name, stat.st_size, stat.st_mtime))
        except OSError:
            pass

        body = self._render_index(token, rec, files)
        return request.make_response(
            body, headers=[("Content-Type", "text/html; charset=utf-8")]
        )

    @staticmethod
    def _human_size(num_bytes):
        size = float(num_bytes or 0)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _render_index(self, token, rec, files):
        """Render the branded download listing page."""
        if files:
            rows = "".join(
                "<tr>"
                "<td class='name'>{name}</td>"
                "<td class='size'>{size}</td>"
                "<td class='date'>{date}</td>"
                "<td class='dl'><a class='btn' "
                "href='/auto_backup/download/{token}/{name}'>Download</a></td>"
                "</tr>".format(
                    name=escape(name),
                    size=escape(self._human_size(size)),
                    date=escape(datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")),
                    token=escape(token),
                )
                for name, size, mtime in files
            )
            table = (
                "<table><thead><tr><th>File</th><th>Size</th>"
                "<th>Date</th><th></th></tr></thead>"
                "<tbody>{rows}</tbody></table>".format(rows=rows)
            )
        else:
            table = "<p class='empty'>No backup files available yet.</p>"

        return _INDEX_TEMPLATE.format(
            config=escape(rec.name or ""),
            count=len(files),
            table=table,
        )

    @http.route(
        "/auto_backup/download/<string:token>/<string:filename>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
        sitemap=False,
    )
    def download(self, token, filename, **kwargs):
        rec = self._authenticate(token)
        if rec is None:
            return _unauthorized()

        full = self._safe_full_path(rec, filename)
        if not full:
            raise werkzeug.exceptions.NotFound()

        stat = os.stat(full)
        # Build a Stream manually: Stream.from_path would restrict the path to
        # Odoo addon/data dirs, but a backup folder can live anywhere.
        stream = Stream(
            type="path",
            path=full,
            mimetype=mimetypes.guess_type(full)[0] or "application/octet-stream",
            download_name=os.path.basename(full),
            etag=f"{int(stat.st_mtime)}-{stat.st_size}-{adler32(full.encode())}",
            last_modified=stat.st_mtime,
            size=stat.st_size,
        )
        return stream.get_response(as_attachment=True)
