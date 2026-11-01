"""Local-only API. Public deployment needs identity, quotas and access controls."""
from dataclasses import asdict
import os
import sqlite3

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from myriadforge.concept import validate_concept
from myriadforge.core import DomainError, FORMS, EDGES, RECIPES
from myriadforge.gateway import GenerationError
from myriadforge.openai_provider import configured_gateway
from myriadforge.storage import Store

PREFIX = '/api/v1/myriadforge'


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Brief(StrictRequest):
    brief: str = Field(min_length=5, max_length=6000)


class Transition(StrictRequest):
    target_form: str = Field(min_length=1, max_length=32)
    expected_version: int = Field(ge=0)


class Craft(StrictRequest):
    recipe_id: str = Field(min_length=1, max_length=100)
    request_id: str = Field(min_length=1, max_length=100)
    expected_version: int = Field(ge=0)


def create_app(db_path=None, gateway_factory=None):
    app = FastAPI(title='MyriadForge local API', version='0.2.0')
    # Lazy store creation allows importing the API without filesystem changes.
    def store():
        return Store(db_path or os.getenv('NEXUS_DB_PATH', 'nexus.sqlite3'))

    @app.exception_handler(DomainError)
    async def domain_error(request, error):
        code = str(error)
        status = 404 if code.endswith('_NOT_FOUND') else 409
        return JSONResponse(status_code=status, content={'error': {'code': code}})

    @app.exception_handler(GenerationError)
    async def model_error(request, error):
        status = 502
        if error.code in {'MODEL_NOT_CONFIGURED', 'PROVIDER_NOT_IMPLEMENTED'}:
            status = 503
        elif error.code == 'INVALID_BRIEF':
            status = 422
        return JSONResponse(status_code=status, content={'error': {'code': error.code}})

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request, error):
        return JSONResponse(status_code=503, content={'error': {'code': 'STORAGE_UNAVAILABLE'}})

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'mode': 'local_development'}

    @app.get(PREFIX + '/reference')
    async def reference():
        return {'id': 'astra-myriad-umbra', 'revision': 1, 'source': 'authored_reference_case',
                'forms': sorted(FORMS), 'transitions': sorted(EDGES),
                'recipes': {key: {'materials': materials, 'unlock': target}
                            for key, (materials, target) in RECIPES.items()},
                'model_status': 'not_implemented', 'print_status': 'not_tested'}

    @app.post(PREFIX + '/concepts', status_code=201)
    async def generate(request: Brief):
        gateway = (gateway_factory or configured_gateway)()
        result = await gateway.generate_concept(request.brief)
        # Enforce the shared contract even for a future provider implementation.
        validate_concept(result.content)
        return store().save_concept({'validation_scope': 'concept_schema_only', **asdict(result)})

    @app.get(PREFIX + '/concepts/{identifier}')
    async def get_concept(identifier: str):
        return store().get_concept(identifier)

    @app.post(PREFIX + '/sessions', status_code=201)
    async def create_session():
        return store().create_session()

    @app.get(PREFIX + '/sessions/{identifier}')
    async def get_session(identifier: str):
        return store().get_session(identifier)

    @app.post(PREFIX + '/sessions/{identifier}/transitions')
    async def transition(identifier: str, request: Transition):
        return store().mutate(identifier, request.expected_version, target=request.target_form)

    @app.post(PREFIX + '/sessions/{identifier}/crafts')
    async def craft(identifier: str, request: Craft):
        return store().mutate(identifier, request.expected_version,
                              recipe=request.recipe_id, request_id=request.request_id)

    return app


app = create_app()
