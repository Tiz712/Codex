from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

import httpx

from myriadforge.api import create_app, PREFIX
from myriadforge.core import DomainError
from myriadforge.gateway import GenerationError, GenerationResult
from myriadforge.storage import Store


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'test.sqlite3'
        def unconfigured():
            raise GenerationError('MODEL_NOT_CONFIGURED')
        self.factory = unconfigured
        self.app = create_app(self.path, lambda: self.factory())
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://test')

    async def asyncTearDown(self):
        await self.client.aclose()
        self.tmp.cleanup()

    async def new_session(self):
        response = await self.client.post(PREFIX + '/sessions')
        self.assertEqual(response.status_code, 201)
        return response.json()

    async def test_complete_flow_and_recreation(self):
        session = await self.new_session()
        path = PREFIX + '/sessions/' + session['id']
        response = await self.client.post(path + '/transitions', json={'target_form': 'shield', 'expected_version': 0})
        self.assertEqual(response.json()['error']['code'], 'FORM_LOCKED')
        payload = {'recipe_id': 'guardian', 'request_id': 'one', 'expected_version': 0}
        response = await self.client.post(path + '/crafts', json=payload)
        self.assertEqual(response.json()['version'], 1)
        retry = await self.client.post(path + '/crafts', json=payload)
        self.assertEqual(retry.json(), response.json())
        for target, version in [('umbrella', 1), ('shield', 2)]:
            self.assertEqual((await self.client.post(path + '/transitions', json={
                'target_form': target, 'expected_version': version})).status_code, 200)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app(self.path)), base_url='http://test') as fresh:
            persisted = (await fresh.get(path)).json()
        self.assertEqual(persisted['current'], 'shield')
        self.assertEqual(persisted['inventory']['guardian_rune'], 0)

    async def test_conflict_and_rollback(self):
        session = await self.new_session()
        path = PREFIX + '/sessions/' + session['id']
        failed = await self.client.post(path + '/transitions', json={'target_form': 'umbrella', 'expected_version': 9})
        self.assertEqual(failed.json()['error']['code'], 'VERSION_CONFLICT')
        self.assertEqual((await self.client.get(path)).json(), session)

    async def test_missing_and_invalid_requests(self):
        self.assertEqual((await self.client.get(PREFIX + '/sessions/missing')).status_code, 404)
        session = await self.new_session()
        response = await self.client.post(PREFIX + '/sessions/' + session['id'] + '/transitions',
            json={'target_form': 'umbrella', 'expected_version': True, 'extra': 1})
        self.assertEqual(response.status_code, 422)

    async def test_no_key_is_explicit(self):
        response = await self.client.post(PREFIX + '/concepts', json={'brief': '星空机关展示道具'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error']['code'], 'MODEL_NOT_CONFIGURED')
        self.assertFalse(self.path.exists())

    async def test_concept_persistence_with_test_only_gateway(self):
        class FixtureGateway:
            async def generate_concept(self, brief):
                return GenerationResult(content={
                    'name': '测试装备', 'lore': '离线测试数据', 'safety_class': 'nonfunctional_display',
                    'forms': [{'id': key, 'name': key, 'description': '测试形态'} for key in
                              ['folded', 'umbrella', 'shield', 'staff']]},
                    provider='test_fixture', model='not-a-real-model', prompt_version='test')
        self.factory = FixtureGateway
        response = await self.client.post(PREFIX + '/concepts', json={'brief': '离线测试装备描述'})
        self.assertEqual(response.status_code, 201)
        value = response.json()
        persisted = (await self.client.get(PREFIX + '/concepts/' + value['id'])).json()
        self.assertEqual(persisted, value)
        self.assertEqual(value['validation_scope'], 'concept_schema_only')

    async def test_invalid_provider_output_not_saved(self):
        class InvalidGateway:
            async def generate_concept(self, brief):
                return GenerationResult({}, 'test', 'test', 'test')
        self.factory = InvalidGateway
        response = await self.client.post(PREFIX + '/concepts', json={'brief': '离线无效装备描述'})
        self.assertEqual(response.status_code, 502)
        self.assertFalse(self.path.exists())


class StorageTests(unittest.TestCase):
    def test_concurrent_version_check_allows_one_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'test.sqlite3')
            session = store.create_session()
            def attempt(_):
                try:
                    return store.mutate(session['id'], 0, target='umbrella')['version']
                except DomainError as error:
                    return str(error)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(attempt, range(2)))
            self.assertCountEqual(results, [1, 'VERSION_CONFLICT'])

    def test_reused_key_for_different_recipe_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'test.sqlite3')
            session = store.create_session()
            store.mutate(session['id'], 0, recipe='guardian', request_id='same')
            with self.assertRaisesRegex(DomainError, 'IDEMPOTENCY_CONFLICT'):
                store.mutate(session['id'], 0, recipe='arcane', request_id='same')
            self.assertEqual(store.get_session(session['id'])['version'], 1)
