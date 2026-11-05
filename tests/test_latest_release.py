"""Offline coverage for the shared stable-release resolver."""

import contextlib
import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from scripts import latest_release as helper


@patch.dict('os.environ', {}, clear=True)
class LatestReleaseTests(unittest.TestCase):
    def response(self, url='', payload=None):
        response = MagicMock()
        response.geturl.return_value = url
        response.read.return_value = json.dumps(payload).encode()
        response.__enter__.return_value = response
        return response

    def redirect(self, location, code=302):
        return urllib.error.HTTPError('url', code, 'Found', {'Location': location}, None)

    @patch.object(helper, '_open_public')
    def test_public_redirect_decodes_tag(self, request):
        request.side_effect = self.redirect('https://github.com/acme/tool/releases/tag/release%2F1.0')
        self.assertEqual(helper.latest_release('acme/tool'), 'release/1.0')
        self.assertEqual(request.call_args.args[0].full_url,
                         'https://github.com/acme/tool/releases/latest')
        self.assertFalse(request.call_args.args[0].has_header('Authorization'))
        self.assertFalse(request.call_args.args[0].has_header('Accept'))

    @patch.object(helper, '_open_public')
    def test_public_redirect_to_releases_means_no_release(self, request):
        request.side_effect = self.redirect('https://github.com/acme/tool/releases')
        self.assertIsNone(helper.latest_release('acme/tool'))

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'})
    @patch.object(helper.urllib.request, 'urlopen')
    def test_authenticated_api(self, request):
        request.return_value = self.response(payload={'tag_name': 'v1', 'prerelease': False})
        self.assertEqual(helper.latest_release('acme/tool'), 'v1')
        self.assertEqual(request.call_args.args[0].get_header('Authorization'), 'Bearer test-token')
        self.assertIn('api.github.com/repos/', request.call_args.args[0].full_url)

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'test-token'})
    @patch.object(helper.urllib.request, 'urlopen')
    def test_api_rejects_prerelease_and_draft(self, request):
        for flag in ('prerelease', 'draft'):
            with self.subTest(flag=flag):
                request.return_value = self.response(payload={'tag_name': 'v2', flag: True})
                with self.assertRaises(ValueError):
                    helper.latest_release('acme/tool')

    @patch.object(helper, '_open_public')
    def test_no_release_and_network_errors(self, request):
        for code in (404, 403, 500):
            with self.subTest(code=code):
                request.side_effect = urllib.error.HTTPError('url', code, 'error', {}, None)
                if code == 404:
                    self.assertIsNone(helper.latest_release('acme/tool'))
                else:
                    with self.assertRaises(urllib.error.HTTPError):
                        helper.latest_release('acme/tool')

    @patch.object(helper, '_open_public')
    def test_unexpected_redirect(self, request):
        request.side_effect = self.redirect('https://github.com/acme/tool/wiki')
        with self.assertRaises(ValueError):
            helper.latest_release('acme/tool')

    @patch.object(helper, '_open_public')
    def test_invalid_identifier_stays_offline(self, request):
        for repo in ('https://github.com/acme/tool', 'acme/tool/extra', '../tool?x=1'):
            with self.assertRaises(ValueError):
                helper.latest_release(repo)
        request.assert_not_called()

    @patch.object(helper.subprocess, 'run')
    def test_lightweight_and_annotated_tags(self, run):
        direct, peeled = 'a' * 40, 'b' * 40
        run.return_value.stdout = f'{direct}\trefs/tags/v1\n'
        self.assertEqual(helper.tag_commit('acme/tool', 'v1'), direct)
        run.return_value.stdout += f'{peeled}\trefs/tags/v1^{{}}\n'
        self.assertEqual(helper.tag_commit('acme/tool', 'v1'), peeled)
        self.assertEqual(run.call_args.args[0][-2:], ['refs/tags/v1', 'refs/tags/v1^{}'])
        run.return_value.stdout = ''
        with self.assertRaises(ValueError):
            helper.tag_commit('acme/tool', 'v1')

    @patch.object(helper, 'tag_commit', return_value='a' * 40)
    @patch.object(helper, 'latest_release', return_value='v1')
    def test_cli_contract(self, latest, commit):
        for flags, expected in (([], 'v1'), (['--commit'], 'v1 ' + 'a' * 40)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(helper.main(['acme/tool', *flags]), 0)
            self.assertEqual(output.getvalue().strip(), expected)
        with contextlib.redirect_stdout(output := io.StringIO()):
            self.assertEqual(helper.main(['acme/tool', '--commit', '--json']), 0)
        self.assertEqual(json.loads(output.getvalue()),
                         {'repo': 'acme/tool', 'tag': 'v1', 'commit': 'a' * 40, 'status': 'ok'})
        latest.return_value = None
        commit.reset_mock()
        with contextlib.redirect_stdout(output := io.StringIO()):
            self.assertEqual(helper.main(['acme/tool', '--commit']), 0)
        self.assertEqual(output.getvalue().strip(), 'no_release')
        commit.assert_not_called()
        with contextlib.redirect_stdout(output := io.StringIO()):
            helper.main(['acme/tool', '--json'])
        self.assertEqual(json.loads(output.getvalue())['status'], 'no_release')

    @patch.object(helper, 'latest_release', side_effect=urllib.error.URLError('offline'))
    def test_cli_failure(self, latest):
        with contextlib.redirect_stderr(error := io.StringIO()):
            self.assertEqual(helper.main(['acme/tool']), 1)
        self.assertIn('offline', error.getvalue())


if __name__ == '__main__':
    unittest.main()
