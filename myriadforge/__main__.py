"""Explicit live-generation CLI. Environment variables are never printed."""
import argparse
import asyncio
from dataclasses import asdict
import json
from pathlib import Path
import sys

from myriadforge.gateway import GenerationError
from myriadforge.openai_provider import configured_gateway


def main():
    parser = argparse.ArgumentParser(description='Generate a validated equipment concept using a paid API')
    parser.add_argument('--brief-file', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        # Exclusive output creation prevents accidental loss of an existing design.
        if args.output.exists():
            print('OUTPUT_ALREADY_EXISTS', file=sys.stderr)
            return 1
        gateway = configured_gateway()
        brief = args.brief_file.read_text(encoding='utf-8')
        result = asyncio.run(gateway.generate_concept(brief))
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump({'validation_scope': 'concept_schema_only', **asdict(result)},
                      stream, ensure_ascii=False, indent=2)
        print('Concept saved; 3D and physical print validation have not run.')
        return 0
    except GenerationError as error:
        print(error.code, file=sys.stderr)
        return 1
    except OSError:
        print('FILE_OPERATION_FAILED', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
