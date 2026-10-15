# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import os
import tempfile

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestDownloadController(HttpCase):
    def setUp(self):
        super().setUp()
        self.folder = tempfile.mkdtemp(prefix="ab_dl_test_")
        self.filename = "2026_07_03_00_00_00.dump"
        self.file_content = b"FAKE-BACKUP-BYTES"
        with open(os.path.join(self.folder, self.filename), "wb") as fh:
            fh.write(self.file_content)
        self.rec = self.env["db.backup"].create(
            {
                "name": "Download Test",
                "method": "local",
                "folder": self.folder,
                "days_to_keep": 0,
                "download_enable": True,
                "download_user": "dluser",
                "download_password": "dlpass",
            }
        )
        self.token = self.rec.download_token

    def _auth(self, user, password):
        raw = base64.b64encode(f"{user}:{password}".encode()).decode()
        return {"Authorization": f"Basic {raw}"}

    def _path(self, token, filename=None):
        path = f"/auto_backup/download/{token}"
        if filename is not None:
            path += f"/{filename}"
        return path

    def _get(self, path, headers=None):
        # url_open carries the HttpCase test-cursor cookie so the request runs
        # inside the test transaction; allow_redirects off to read raw status.
        return self.url_open(path, headers=headers or {}, allow_redirects=False)

    def test_disabled_returns_404(self):
        self.rec.download_enable = False
        # commit so the test HTTP worker sees the change
        self.env.cr.flush()
        r = self._get(self._path(self.token), self._auth("dluser", "dlpass"))
        self.assertEqual(r.status_code, 404)

    def test_unknown_token_404(self):
        r = self._get(self._path("does-not-exist"), self._auth("dluser", "dlpass"))
        self.assertEqual(r.status_code, 404)

    def test_no_auth_header_401(self):
        r = self._get(self._path(self.token))
        self.assertEqual(r.status_code, 401)
        self.assertIn("WWW-Authenticate", r.headers)

    def test_wrong_password_401(self):
        r = self._get(self._path(self.token), self._auth("dluser", "WRONG"))
        self.assertEqual(r.status_code, 401)

    def test_index_lists_files(self):
        r = self._get(self._path(self.token), self._auth("dluser", "dlpass"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.filename, r.text)

    def test_download_file_ok(self):
        r = self._get(
            self._path(self.token, self.filename), self._auth("dluser", "dlpass")
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, self.file_content)

    def test_path_traversal_blocked(self):
        for evil in ["..%2f..%2fetc%2fpasswd", "%2e%2e", "sub%2ffile"]:
            r = self._get(
                self._path(self.token, evil), self._auth("dluser", "dlpass")
            )
            self.assertIn(r.status_code, (400, 404), f"{evil} -> {r.status_code}")
            self.assertNotIn(b"root:", r.content)

    def test_sftp_method_not_served(self):
        self.rec.method = "sftp"
        self.env.cr.flush()
        r = self._get(self._path(self.token), self._auth("dluser", "dlpass"))
        self.assertEqual(r.status_code, 404)
