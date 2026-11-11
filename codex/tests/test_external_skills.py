import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from install_external_skills import install, source_folder


class WorkPackInstallTests(unittest.TestCase):
    def setUp(self):
        # All fixture repositories resolve offline to their current default-branch head.
        self.resolver = patch('install_external_skills.resolve_source', side_effect=lambda source: {
            'tag': None, 'commit': subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True).strip()})
        self.resolve = self.resolver.start()
        self.addCleanup(self.resolver.stop)

    def test_release_commit_wins_over_branch_and_stale_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            (source/'SKILL.md').write_text('stable')
            subprocess.run(['git','init','-q',str(source)],check=True)
            def commit(message):
                subprocess.run(['git','-C',str(source),'add','.'],check=True)
                subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                                '-c','user.email=fixture@example.invalid','commit','-qm',message],check=True)
                return subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
            stable = commit('stable')
            (source/'SKILL.md').write_text('unreleased')
            newer = commit('unreleased')
            self.resolve.side_effect = None
            self.resolve.return_value = {'tag':'v1.0.0','commit':stable}
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills':{'alpha':{'sourceUrl':str(source),'skillPath':'SKILL.md'}}}))
            kwargs = dict(catalog=catalog,home=root/'home',state=root/'state')
            install(['alpha'],**kwargs)
            target = root/'home/.agents/skills/alpha'
            self.assertEqual((target/'SKILL.md').read_text(),'stable')
            lockfile = root/'state/external-skills.lock.json'
            self.assertEqual(json.loads(lockfile.read_text())['alpha']['tag'],'v1.0.0')
            self.resolve.return_value = {'tag':'v2.0.0','commit':newer}
            install(['alpha'],refresh=True,**kwargs)
            self.assertEqual((target/'SKILL.md').read_text(),'unreleased')
            self.assertEqual(json.loads(lockfile.read_text())['alpha']['commit'],newer)
            # A missing copy uses the latest release even when its old receipt survives.
            import shutil
            shutil.rmtree(target)
            install(['alpha'],**kwargs)
            self.assertEqual((target/'SKILL.md').read_text(),'unreleased')

    def test_installs_grouped_source_and_preserves_later_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            subprocess.run(['git','init','-q',str(source)], check=True)
            entries = {}
            for name in ('alpha','beta'):
                folder = source/'skills'/name
                folder.mkdir(parents=True)
                (folder/'SKILL.md').write_text(f'---\nname: {name}\ndescription: fixture\n---\n')
                entries[name] = {'sourceUrl': str(source), 'skillPath': f'skills/{name}/SKILL.md'}
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','fixture'], check=True)
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': entries}))
            home, state = root/'home', root/'state'
            first = install(list(entries), catalog=catalog, home=home, state=state)
            self.assertEqual(first, {'alpha':'installed','beta':'installed'})
            self.assertFalse((home/'.agents/skills/alpha/.git').exists())
            self.assertEqual(set(json.loads((state/'external-skills.lock.json').read_text())), set(entries))
            (home/'.agents/skills/alpha/SKILL.md').write_text('user edit')
            second = install(list(entries), catalog=catalog, home=home, state=state)
            self.assertEqual(second, {'alpha':'existing_preserved','beta':'already_installed'})
            self.assertEqual((home/'.agents/skills/alpha/SKILL.md').read_text(), 'user edit')
            (source/'skills/beta/SKILL.md').write_text('new upstream beta')
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','update'], check=True)
            refreshed = install(list(entries), catalog=catalog, home=home, state=state, refresh=True)
            self.assertEqual(refreshed['alpha'], 'modified_copy_preserved')
            self.assertTrue(refreshed['beta'].startswith('updated; backup='))
            self.assertEqual((home/'.agents/skills/beta/SKILL.md').read_text(), 'new upstream beta')
            self.assertTrue((Path(refreshed['beta'].split('=',1)[1])/'SKILL.md').is_file())

    def test_replace_existing_keeps_local_additions_and_updates_description_only_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            subprocess.run(['git','init','-q',str(source)], check=True)
            entries = {}
            for name in ('alpha','beta'):
                folder = source/'skills'/name
                folder.mkdir(parents=True)
                (folder/'SKILL.md').write_text(f'---\nname: {name}\ndescription: fixture\n---\nbody\n')
                entries[name] = {'sourceUrl': str(source), 'skillPath': f'skills/{name}/SKILL.md'}
            def commit(message):
                subprocess.run(['git','-C',str(source),'add','.'], check=True)
                subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                                '-c','user.email=fixture@example.invalid','commit','-qm',message], check=True)
            commit('fixture')
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': entries}))
            home, state = root/'home', root/'state'
            install(list(entries), catalog=catalog, home=home, state=state)
            skills = home/'.agents/skills'
            # beta: curated description only; alpha: a local lesson and a local reference file.
            (skills/'beta/SKILL.md').write_text('---\nname: beta\ndescription: "curated"\n---\nbody\n')
            (skills/'alpha/SKILL.md').write_text('---\nname: alpha\ndescription: fixture\n---\nbody\nlocal lesson\n')
            (skills/'alpha/references').mkdir()
            (skills/'alpha/references/local.md').write_text('local')
            for name in entries:
                (source/'skills'/name/'SKILL.md').write_text(f'---\nname: {name}\ndescription: fixture\n---\nnew body\n')
            commit('update')
            result = install(list(entries), catalog=catalog, home=home, state=state, refresh=True, replace_existing=True)
            self.assertEqual(result['alpha'], 'modified_copy_preserved')
            self.assertIn('local lesson', (skills/'alpha/SKILL.md').read_text())
            self.assertTrue((skills/'alpha/references/local.md').is_file())
            self.assertTrue(result['beta'].startswith('updated; backup='))
            self.assertIn('new body', (skills/'beta/SKILL.md').read_text())

    def test_other_skill_folder_gets_its_own_copy_and_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            folder = source/'skills/alpha'
            folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text('---\nname: alpha\ndescription: fixture\n---\n')
            subprocess.run(['git','init','-q',str(source)], check=True)
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','fixture'], check=True)
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': {'alpha': {'sourceUrl': str(source), 'skillPath': 'skills/alpha/SKILL.md'}}}))
            home, state, claude = root/'home', root/'state', root/'home/.claude/skills'
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state), {'alpha': 'installed'})
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, skills_dir=claude), {'alpha': 'installed'})
            self.assertTrue((claude/'alpha/SKILL.md').is_file())
            self.assertEqual(len(list(state.glob('external-skills*.lock.json'))), 2)
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, skills_dir=claude), {'alpha': 'already_installed'})

    def test_refresh_protects_untracked_and_non_skill_user_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            folder = source/'skills/alpha'
            folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text('version one')
            (folder/'notes.md').write_text('reference one')
            subprocess.run(['git','init','-q',str(source)], check=True)
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','first'], check=True)
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': {'alpha': {'sourceUrl': str(source), 'skillPath': 'skills/alpha/SKILL.md'}}}))
            home, state = root/'home', root/'state'
            install(['alpha'], catalog=catalog, home=home, state=state)
            target = home/'.agents/skills/alpha'
            (target/'notes.md').write_text('user change')
            (folder/'notes.md').write_text('reference two')
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','second'], check=True)
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, refresh=True),
                             {'alpha':'modified_copy_preserved'})
            self.assertEqual((target/'notes.md').read_text(), 'user change')
            (state/'external-skills.lock.json').unlink()
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, refresh=True),
                             {'alpha':'untracked_copy_preserved'})
            with self.assertRaisesRegex(RuntimeError, 'requires --refresh'):
                install(['alpha'], catalog=catalog, home=home, state=state, replace_existing=True)
            replaced = install(['alpha'], catalog=catalog, home=home, state=state,
                               refresh=True, replace_existing=True)
            backup = Path(replaced['alpha'].split('=', 1)[1])
            self.assertEqual((backup/'notes.md').read_text(), 'user change')
            self.assertEqual((target/'notes.md').read_text(), 'reference two')
            self.assertEqual(json.loads((backup.parent/'receipt.json').read_text())['skill'], 'alpha')
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, refresh=True),
                             {'alpha':'up_to_date'})

    def test_refresh_can_migrate_a_verified_copy_to_new_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = []
            for index in (1, 2):
                repo = root/f'source-{index}'
                folder = repo/'skills/alpha'
                folder.mkdir(parents=True)
                (folder/'SKILL.md').write_text(f'version {index}')
                subprocess.run(['git','init','-q',str(repo)], check=True)
                subprocess.run(['git','-C',str(repo),'add','.'], check=True)
                subprocess.run(['git','-C',str(repo),'-c','user.name=Fixture',
                                '-c','user.email=fixture@example.invalid','commit','-qm','source'], check=True)
                sources.append(repo)
            catalog = root/'catalog.json'
            home, state = root/'home', root/'state'
            def write_catalog(repo):
                catalog.write_text(json.dumps({'skills': {'alpha': {'sourceUrl': str(repo),
                                                                  'skillPath': 'skills/alpha/SKILL.md'}}}))
            write_catalog(sources[0])
            install(['alpha'], catalog=catalog, home=home, state=state)
            write_catalog(sources[1])
            result = install(['alpha'], catalog=catalog, home=home, state=state, refresh=True)
            self.assertTrue(result['alpha'].startswith('updated; backup='))
            self.assertEqual((home/'.agents/skills/alpha/SKILL.md').read_text(), 'version 2')
            self.assertEqual(json.loads((state/'external-skills.lock.json').read_text())['alpha']['source'], str(sources[1]))

    def test_root_skill_does_not_copy_git_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            source.mkdir()
            (source/'SKILL.md').write_text('root skill')
            subprocess.run(['git','init','-q',str(source)], check=True)
            subprocess.run(['git','-C',str(source),'add','.'], check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','root'], check=True)
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': {'alpha': {'sourceUrl': str(source), 'skillPath': 'SKILL.md'}}}))
            home, state = root/'home', root/'state'
            install(['alpha'], catalog=catalog, home=home, state=state)
            target = home/'.agents/skills/alpha'
            self.assertFalse((target/'.git').exists())
            self.assertEqual(install(['alpha'], catalog=catalog, home=home, state=state, refresh=True),
                             {'alpha':'up_to_date'})

    def test_source_with_lfs_media_installs_without_git_lfs(self):
        # A source repository may keep media in Git LFS. The checkout keeps LFS pointer
        # files, so a machine whose Git config names a missing git-lfs program still installs.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gitconfig = root/'gitconfig'
            gitconfig.write_text('')
            with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': str(gitconfig), 'GIT_CONFIG_NOSYSTEM': '1'}):
                source = root/'source'
                folder = source/'skills/alpha'
                folder.mkdir(parents=True)
                (folder/'SKILL.md').write_text('---\nname: alpha\ndescription: fixture\n---\n')
                (source/'media').mkdir()
                (source/'media/clip.mp4').write_text('media bytes')
                (source/'.gitattributes').write_text('media/** filter=lfs diff=lfs merge=lfs -text\n')
                subprocess.run(['git','init','-q',str(source)], check=True)
                subprocess.run(['git','-C',str(source),'add','.'], check=True)
                subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                                '-c','user.email=fixture@example.invalid','commit','-qm','fixture'], check=True)
                gitconfig.write_text('[filter "lfs"]\n\tprocess = missing-git-lfs filter-process\n'
                                     '\tsmudge = missing-git-lfs smudge -- %f\n\trequired = true\n')
                catalog = root/'catalog.json'
                catalog.write_text(json.dumps({'skills': {'alpha': {'sourceUrl': str(source),
                                                                  'skillPath': 'skills/alpha/SKILL.md'}}}))
                self.assertEqual(install(['alpha'], catalog=catalog, home=root/'home', state=root/'state'),
                                 {'alpha': 'installed'})

    def test_skill_dropped_in_latest_release_keeps_installed_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'source'
            (source/'skills/kept').mkdir(parents=True)
            (source/'skills/kept/SKILL.md').write_text('kept')
            subprocess.run(['git','init','-q',str(source)],check=True)
            subprocess.run(['git','-C',str(source),'add','.'],check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Fixture',
                            '-c','user.email=fixture@example.invalid','commit','-qm','init'],check=True)
            installed = root/'home/.agents/skills/gone'
            installed.mkdir(parents=True)
            (installed/'SKILL.md').write_text('local copy')
            catalog = root/'catalog.json'
            catalog.write_text(json.dumps({'skills': {
                'gone': {'sourceUrl': str(source), 'skillPath': 'skills/gone/SKILL.md'},
                'kept': {'sourceUrl': str(source), 'skillPath': 'skills/kept/SKILL.md'}}}))
            result = install(['gone','kept'], catalog=catalog, home=root/'home', state=root/'state',
                             refresh=True, replace_existing=True, skills_dir=root/'home/.agents/skills')
            self.assertEqual(result, {'gone': 'missing_upstream_preserved', 'kept': 'installed'})
            self.assertEqual((installed/'SKILL.md').read_text(), 'local copy')

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                source_folder(Path(directory), '../SKILL.md')


if __name__ == '__main__':
    unittest.main()
