"""Restricted concept schema. This is not a mesh or gameplay validation."""
from myriadforge.core import FORMS
from myriadforge.gateway import GenerationError

CONCEPT_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'name': {'type': 'string'},
        'lore': {'type': 'string'},
        'safety_class': {'type': 'string', 'enum': ['nonfunctional_display']},
        'forms': {'type': 'array', 'minItems': 4, 'maxItems': 4, 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {
                'id': {'type': 'string', 'enum': sorted(FORMS)},
                'name': {'type': 'string'}, 'description': {'type': 'string'}},
            'required': ['id', 'name', 'description']}}},
    'required': ['name', 'lore', 'safety_class', 'forms']}


def validate_concept(value):
    def invalid():
        raise GenerationError('MODEL_INVALID_OUTPUT')

    def text(value, maximum):
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            invalid()

    if not isinstance(value, dict) or set(value) != set(CONCEPT_SCHEMA['required']):
        invalid()
    text(value['name'], 100)
    text(value['lore'], 3000)
    if value['safety_class'] != 'nonfunctional_display':
        invalid()
    forms = value['forms']
    if not isinstance(forms, list) or len(forms) != 4:
        invalid()
    ids = []
    for form in forms:
        if not isinstance(form, dict) or set(form) != {'id', 'name', 'description'}:
            invalid()
        text(form['id'], 32)
        text(form['name'], 100)
        text(form['description'], 1000)
        ids.append(form['id'])
    if set(ids) != FORMS:
        invalid()
    return value
