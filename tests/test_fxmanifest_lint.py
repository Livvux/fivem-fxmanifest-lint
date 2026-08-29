import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fxmanifest_lint import RULESET_VERSION, tokenize_manifest, validate_text  # noqa: E402


class ManifestTokenizerTests(unittest.TestCase):
    def test_comments_call_syntax_and_plural_tables_are_tokenized(self):
        directives = tokenize_manifest(
            """-- fx_version 'adamant'
            fx_version('cerulean')
            games { 'gta5' }
            --[[ client_script 'ignored.lua' ]]
            client_scripts({ 'client/main.lua', "client/extra.lua" })
            data_file('HANDLING_FILE')('data/handling.meta')
            """
        )

        self.assertEqual(
            [(item.name, item.values, item.line, item.value_kind) for item in directives],
            [
                ('fx_version', ['cerulean'], 2, 'scalar'),
                ('games', ['gta5'], 3, 'table'),
                ('client_scripts', ['client/main.lua', 'client/extra.lua'], 5, 'table'),
                ('data_file', ['HANDLING_FILE', 'data/handling.meta'], 6, 'scalar'),
            ],
        )

    def test_malicious_lua_is_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'executed'
            text = f"fx_version 'cerulean'\ngame 'gta5'\nos.execute('touch {marker}')\n"
            findings = validate_text(text)
            self.assertFalse(marker.exists())
            self.assertFalse(any(item.rule_id == 'FXM900' for item in findings))


class ManifestValidationTests(unittest.TestCase):
    def rule_ids(self, text, **kwargs):
        return [item.rule_id for item in validate_text(text, **kwargs)]

    def test_valid_manifest_is_clean(self):
        text = """fx_version 'cerulean'
game 'gta5'
client_scripts { 'client/*.lua' }
server_script 'server.lua'
shared_script '@ox_lib/init.lua'
ui_page 'html/index.html'
files { 'html/index.html', 'html/app.js' }
dependency 'base-resource'
node_version '22'
"""
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'current-resource'
            (resource / 'client').mkdir(parents=True)
            (resource / 'html').mkdir()
            (resource.parent / 'base-resource').mkdir()
            (resource.parent / 'ox_lib').mkdir()
            (resource / 'client/main.lua').write_text('', encoding='utf-8')
            (resource / 'server.lua').write_text('', encoding='utf-8')
            (resource / 'html/index.html').write_text('', encoding='utf-8')
            (resource / 'html/app.js').write_text('', encoding='utf-8')
            (resource.parent / 'ox_lib/init.lua').write_text('', encoding='utf-8')
            self.assertEqual(validate_text(text, resource_dir=resource), [])

    def test_external_resource_file_reference_is_resolved_without_false_local_error(self):
        text = "fx_version 'cerulean'\ngame 'gta5'\nshared_script '@missing-lib/init.lua'\n"
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'resource'
            resource.mkdir()
            findings = validate_text(text, resource_dir=resource)
            self.assertEqual([item.rule_id for item in findings], ['FXM011'])

    def test_required_values_and_deprecations(self):
        self.assertEqual(self.rule_ids("description 'only metadata'"), ['FXM001', 'FXM003'])
        ids = self.rule_ids("fx_version 'future'\ngame 'minecraft'\nlua54 'yes'\nnode_version '20'\n")
        self.assertEqual(ids, ['FXM002', 'FXM004', 'FXM005', 'FXM006'])

    def test_shape_duplicates_nui_and_data_file(self):
        text = """fx_version 'cerulean'
fx_version 'cerulean'
game 'gta5'
client_scripts 'client.lua'
client_script { 'other.lua' }
ui_page 'html/index.html'
files { 'html/app.js', 'html/app.js' }
data_file 'HANDLING_FILE'
dependency 'base'
dependency 'base'
"""
        ids = self.rule_ids(text)
        self.assertIn('FXM007', ids)
        self.assertIn('FXM008', ids)
        self.assertIn('FXM012', ids)
        self.assertIn('FXM013', ids)
        self.assertIn('FXM015', ids)

    def test_files_globs_and_dependencies_are_resolved(self):
        text = """fx_version 'cerulean'
game 'gta5'
client_scripts { 'client/*.lua', 'missing.lua' }
files { 'html/**/*.js' }
dependency 'missing-base'
"""
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'resource'
            resource.mkdir()
            ids = self.rule_ids(text, resource_dir=resource)
            self.assertIn('FXM009', ids)
            self.assertIn('FXM010', ids)
            self.assertIn('FXM011', ids)

    def test_file_checks_do_not_escape_the_resource_directory(self):
        text = "fx_version 'cerulean'\ngame 'gta5'\nclient_script '../outside*.lua'\n"
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / 'resource'
            resource.mkdir()
            (resource.parent / 'outside.lua').write_text('', encoding='utf-8')
            self.assertEqual(self.rule_ids(text, resource_dir=resource), ['FXM010'])

    def test_size_limit_is_reported_without_parsing(self):
        text = "fx_version 'cerulean'\ngame 'gta5'\n" + ('x' * 65_536)
        findings = validate_text(text, max_bytes=65_536)
        self.assertEqual([item.rule_id for item in findings], ['FXM017'])

    def test_versioned_fixture_catalog(self):
        fixtures = json.loads((ROOT / 'fixtures-v2.0.0.json').read_text(encoding='utf-8'))
        self.assertEqual(fixtures['ruleset_version'], RULESET_VERSION)
        for case in fixtures['cases']:
            with self.subTest(case=case['name']):
                self.assertEqual(self.rule_ids(case['manifest']), case['rule_ids'])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / 'fxmanifest_lint.py'), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_version_and_json_contract(self):
        version = self.run_cli('--version')
        self.assertEqual(version.returncode, 0)
        self.assertEqual(version.stdout.strip(), f'fivem-fxmanifest-lint {RULESET_VERSION}')

        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory)
            (resource / 'fxmanifest.lua').write_text("fx_version 'cerulean'\ngame 'gta5'\n", encoding='utf-8')
            result = self.run_cli(str(resource), '--format', 'json')
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload['ruleset_version'], '2.0.0')
            self.assertEqual(payload['findings'], [])

    def test_exit_codes_and_fail_on_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory)
            manifest = resource / 'fxmanifest.lua'
            manifest.write_text("fx_version 'cerulean'\ngame 'gta5'\nlua54 'yes'\n", encoding='utf-8')
            self.assertEqual(self.run_cli(str(resource)).returncode, 0)
            self.assertEqual(self.run_cli(str(resource), '--fail-on-warnings').returncode, 1)
            manifest.write_text("game 'gta5'\n", encoding='utf-8')
            self.assertEqual(self.run_cli(str(resource)).returncode, 1)
            self.assertEqual(self.run_cli(str(resource / 'missing')).returncode, 2)


if __name__ == '__main__':
    unittest.main()
