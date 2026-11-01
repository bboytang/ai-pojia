"""Contract tests with a host API double, not a live AstrBot/model."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from astrbot_policy import AUTHORIZATION, PROMPT, SKILL, apply_policy
from tools.package_astrbot import FILES, build

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def test_preserves_persona_and_loads_workflow(self):
        result = apply_policy("原有人格")
        self.assertEqual(result, "原有人格\n\n" + PROMPT + "\n\n" + SKILL + "\n\n" + AUTHORIZATION)
        self.assertEqual(apply_policy(result), result)
        self.assertTrue(apply_policy("").startswith(PROMPT))
        self.assertNotIn("name: ai-pojia", SKILL)

    def test_authorization_toggle(self):
        result = apply_policy("", False)
        self.assertIn(PROMPT, result)
        self.assertIn(SKILL, result)
        self.assertNotIn(AUTHORIZATION, result)
        self.assertEqual(apply_policy(result, True), result + "\n\n" + AUTHORIZATION)

    def test_original_texts_unchanged(self):
        import hashlib
        for name, digest in (
            ("prompts/ai-pojia.md", "c1b2fa4dec77b6626f757aee99b1f39e0e3f2727418772d9141027e7e4260b58"),
            ("skills/ai-pojia/SKILL.md", "031269d4706297bc443f265199872bd895dcb1e0b5a215dedc94f100bad3f2b8"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_package_is_complete_reproducible_and_importable(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = build(Path(tmp))
            before = archive.read_bytes()
            self.assertEqual(build(Path(tmp)).read_bytes(), before)
            with zipfile.ZipFile(archive) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertEqual(set(bundle.namelist()), {"astrbot_plugin_ai_pojia/" + f for f in FILES})
                bundle.extractall(tmp)
            policy = Path(tmp) / 'astrbot_plugin_ai_pojia/astrbot_policy.py'
            spec = importlib.util.spec_from_file_location('unpacked_policy', policy)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.apply_policy(''), apply_policy(''))
            self.assertTrue(archive.with_suffix('.zip.sha256').is_file())


class HookTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_system_prompt_changes_and_config_is_live(self):
        modules = {name: ModuleType(name) for name in (
            'astrbot', 'astrbot.api', 'astrbot.api.event', 'astrbot.api.provider', 'astrbot.api.star')}
        modules['astrbot.api'].AstrBotConfig = dict
        modules['astrbot.api.event'].AstrMessageEvent = object
        priorities = []
        def on_llm_request(**kwargs):
            priorities.append(kwargs['priority'])
            return lambda method: method
        modules['astrbot.api.event'].filter = SimpleNamespace(on_llm_request=on_llm_request)
        modules['astrbot.api.provider'].ProviderRequest = object
        class Star:
            def __init__(self, context):
                pass
        modules['astrbot.api.star'].Star = Star
        package = ModuleType('test_plugin')
        package.__path__ = [str(ROOT)]
        modules['test_plugin'] = package
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('test_plugin.main', ROOT / 'main.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        self.assertEqual(priorities, [-100000])
        config = {key: val['default'] for key, val in json.loads((ROOT / '_conf_schema.json').read_text()).items()}
        self.assertEqual(config, {'enabled': True, 'authorized_execution': True})
        plugin = module.AiPojiaPlugin(None, config)
        contexts = [{'role': 'user', 'content': 'hello'}]
        req = SimpleNamespace(system_prompt='persona', contexts=contexts, prompt='hello', model='original', func_tool=None)
        await plugin.on_request(object(), req)
        await plugin.on_request(object(), req)
        self.assertEqual(req.system_prompt, apply_policy('persona'))
        self.assertEqual(req.contexts, [{'role': 'user', 'content': 'hello'}])
        self.assertIs(req.contexts, contexts)
        self.assertEqual((req.prompt, req.model, req.func_tool), ('hello', 'original', None))
        for value in (False, 'false', 1):
            config['enabled'] = value
            req.system_prompt = 'persona'
            await plugin.on_request(object(), req)
            self.assertEqual(req.system_prompt, 'persona')
        config.update(enabled=True, authorized_execution=False)
        req.system_prompt = None
        await plugin.on_request(object(), req)
        self.assertEqual(req.system_prompt, apply_policy('', False))
