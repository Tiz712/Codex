import asyncio
from copy import deepcopy
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from myriadforge.gateway import GenerationError
from myriadforge.openai_provider import OpenAIGateway, configured_gateway, post_response


def concept():
    return {'name': '星穹千机伞', 'lore': '星图守望者的展示道具。',
            'safety_class': 'nonfunctional_display',
            'forms': [{'id': key, 'name': key, 'description': '非功能性展示形态'}
                      for key in ['folded', 'umbrella', 'shield', 'staff']]}


def response(value=None):
    return {'status': 'completed', 'model': 'test-model', 'usage': {'input_tokens': 10},
            'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps(value or concept())}]}]}


class GatewayTests(unittest.TestCase):
    def run_generation(self, result):
        async def transport(key, payload):
            return result
        return asyncio.run(OpenAIGateway('test-key', 'test-model', transport).generate_concept('生成星空展示装备'))

    def test_success_and_request_contract(self):
        async def transport(key, payload):
            self.assertEqual(key, 'test-key')
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('tools', payload)
            self.assertEqual(payload['max_output_tokens'], 2400)
            return response()
        result = asyncio.run(OpenAIGateway('test-key', 'test-model', transport).generate_concept('生成星空展示装备'))
        self.assertEqual(result.provider, 'openai')
        self.assertEqual(result.usage['input_tokens'], 10)
        self.assertEqual(len(result.input_sha256), 64)

    def test_duplicate_forms_rejected(self):
        value = concept()
        value['forms'][0] = deepcopy(value['forms'][1])
        with self.assertRaisesRegex(GenerationError, 'MODEL_INVALID_OUTPUT'):
            self.run_generation(response(value))

    def test_unexpected_fields_and_wrong_types(self):
        for field, value in [('model_status', 'verified'), ('forms', {}), ('name', 42)]:
            invalid = concept()
            invalid[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(GenerationError, 'MODEL_INVALID_OUTPUT'):
                self.run_generation(response(invalid))

    def test_incomplete(self):
        with self.assertRaisesRegex(GenerationError, 'MODEL_INCOMPLETE'):
            self.run_generation({'status': 'incomplete'})

    def test_refusal(self):
        with self.assertRaisesRegex(GenerationError, 'MODEL_REFUSAL'):
            self.run_generation({'status': 'completed', 'output': [{'type': 'message',
                'content': [{'type': 'refusal', 'refusal': 'Cannot comply'}]}]})

    def test_malformed_json(self):
        value = response()
        value['output'][0]['content'][0]['text'] = 'not json'
        with self.assertRaisesRegex(GenerationError, 'MODEL_INVALID_OUTPUT'):
            self.run_generation(value)

    def test_empty_output(self):
        with self.assertRaisesRegex(GenerationError, 'MODEL_INVALID_OUTPUT'):
            self.run_generation({'status': 'completed', 'output': []})

    def test_config_missing(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'openai', 'OPENAI_API_KEY': '', 'OPENAI_MODEL': ''}):
            with self.assertRaisesRegex(GenerationError, 'MODEL_NOT_CONFIGURED'):
                configured_gateway()

    def test_provider_not_implemented(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'unknown'}):
            with self.assertRaisesRegex(GenerationError, 'PROVIDER_NOT_IMPLEMENTED'):
                configured_gateway()

    def test_invalid_brief_never_calls_transport(self):
        async def transport(key, payload):
            self.fail('Transport should not run')
        with self.assertRaisesRegex(GenerationError, 'INVALID_BRIEF'):
            asyncio.run(OpenAIGateway('test', 'test', transport).generate_concept(' '))

    def test_http_errors_are_sanitized(self):
        for status, code in [(401, 'MODEL_AUTH_FAILED'), (403, 'MODEL_ACCESS_DENIED'),
                             (429, 'MODEL_RATE_LIMIT'), (500, 'MODEL_REQUEST_FAILED')]:
            with self.subTest(status=status), patch('myriadforge.openai_provider.build_opener') as opener:
                opener.return_value.open.side_effect = HTTPError('https://example.test', status, 'private', {}, None)
                with self.assertRaisesRegex(GenerationError, code):
                    post_response('secret', {})

    def test_timeout_and_unreachable(self):
        for error, code in [(TimeoutError(), 'MODEL_TIMEOUT'), (URLError('private'), 'MODEL_UNREACHABLE')]:
            with self.subTest(code=code), patch('myriadforge.openai_provider.build_opener') as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaisesRegex(GenerationError, code):
                    post_response('secret', {})
