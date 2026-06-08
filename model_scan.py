#!/usr/bin/env python3
"""Quick scan for model references, faster version."""
import os, re, sys

base = '.'
MODELS = sys.argv[1:] if len(sys.argv) > 1 else [
    'AgentMemory', 'TokenBlacklist', 'UploadChunk', 'UploadTask', 'NodeExecution',
]

# Collect all relevant source files
all_files = []
for root, dirs, files in os.walk(base):
    # Skip problematic dirs
    parts = root.replace(os.sep, '/').split('/')
    skip = False
    for p in parts:
        if p.startswith('.') or p in ('__pycache__', 'node_modules', '.codegraph', '__pycache__'):
            skip = True
            break
    if skip:
        continue
    for f in files:
        if f.endswith(('.py', '.ts', '.tsx')):
            all_files.append(os.path.join(root, f))

for model in MODELS:
    refs = []
    for fp in all_files:
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            continue
        if re.search(r'\b' + re.escape(model) + r'\b', content):
            rel = os.path.relpath(fp, base)
            # Filter out model definition files and __init__ re-exports
            if rel.endswith(f'{model.lower()}.py') or rel.endswith(f'{model.lower()}.ts'):
                continue
            # Filter __init__.py where the model is just re-exported
            if rel.endswith('__init__.py'):
                # Check if it's an actual import
                if f'from shared.models' not in content and f'import {model}' not in content:
                    continue
                # Skip pure re-export __init__.py files
                if model in content and 'from' in content:
                    continue
            refs.append(rel)
    
    if refs:
        print(f'{model}:')
        for r in refs[:10]:
            print(f'  {r}')
        if len(refs) > 10:
            print(f'  ... and {len(refs)-10} more')
        print()
    else:
        print(f'{model}: NO references\n')
