#!/usr/bin/env python3
"""Validate the shareable experiment registry and aggregate arithmetic, without private data."""
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def inside(base, relative):
    path = (base / relative).resolve()
    require(path.is_relative_to(base.resolve()), 'Artifact escapes experiment directory')
    require(path.is_file(), 'Missing artifact: ' + str(relative))
    return path


def validate(root=ROOT):
    base = root / 'experiments'
    registry = read(base / 'index.json')
    seen = set()
    count = 0
    for entry in registry['experiments']:
        version = entry['experiment_version']
        require(re.fullmatch(r'b2[cb]-v\d+\.\d+\.\d+', version), 'Invalid experiment version')
        require(version not in seen, 'Duplicate experiment version: ' + version)
        seen.add(version)
        require(entry['manifest'] == version + '/experiment.json', 'Manifest path/version mismatch')
        require(entry['report'] == version + '/README.md', 'Report path/version mismatch')
        manifest = read(inside(base, entry['manifest']))
        experiment = base / version
        require(manifest['experiment_version'] == version, 'Manifest version mismatch')
        datetime.fromisoformat(manifest['executed_at'])
        require(entry['executed_at'] == manifest['executed_at'], 'Execution date mismatch')
        require(entry['scenario_count'] == manifest['suite']['task_count'], 'Scenario coverage mismatch')
        require(len(manifest['coverage']['task_ids']) == manifest['suite']['task_count'], 'Task coverage mismatch')
        require(entry['completed_runs'] == manifest['suite']['completed_runs'], 'Run coverage mismatch')
        require(manifest['sharing']['level'] == entry['sharing_level'], 'Sharing-level mismatch')
        require(manifest['sharing']['raw_data_in_git'] is False, 'Private raw data must stay outside Git')
        for relative in manifest['artifacts']:
            inside(experiment, relative)
        current = manifest['current_results']
        require(all(v in manifest['artifacts'] for v in current.values()), 'Current results missing from artifact list')
        metrics = read(inside(experiment, current['metrics']))
        quality = read(inside(experiment, current['quality']))
        cost = read(inside(experiment, current['cost']))
        raw = read(inside(experiment, current['raw_manifest']))
        for artifact in [metrics, quality, cost, raw]:
            require(artifact['experiment_version'] == version, 'Artifact experiment-version mismatch')
        require(raw['sharing_level'] == manifest['sharing']['level'], 'Raw sharing-level mismatch')
        require(raw['raw_data_uploaded'] is False, 'Raw data must remain withheld')
        for artifact in raw['artifacts']:
            require(artifact['access'] == 'withheld-private', 'Unexpected raw-data sharing')
            require(artifact['local_path'].startswith('.private/'), 'Raw locator must be a relative .private/ path')
            require('..' not in Path(artifact['local_path']).parts, 'Raw locator escapes .private/')
            require(re.fullmatch(r'[0-9a-f]{64}', artifact['sha256_bytes']), 'Invalid raw byte hash')
            require(artifact['bytes'] > 0, 'Empty raw artifact')
        runs = {r['run_id']: r for r in metrics['rows']}
        require(len(runs) == len(metrics['rows']) == manifest['suite']['completed_runs'], 'Duplicate/missing measured runs')
        require(set(runs) == {r['run_id'] for r in quality['rows']} == {r['run_id'] for r in cost['rows']}, 'Metrics/quality/cost run mismatch')
        require(len(quality['rows']) == len(runs) == len(cost['rows']), 'Duplicate quality/cost runs')
        for row in quality['rows']:
            require(row['model'] == runs[row['run_id']]['model'], 'Quality model mismatch')
            require(set(row['scores']) == {'coverage', 'prioritization', 'grounding'}, 'Missing rubric')
            for score in row['scores'].values():
                require(score is None or (type(score) in (int, float) and score in (0, 0.5, 1)), 'Invalid ordinal score')
            require(not (runs[row['run_id']]['state_verifier_status'] == 'unknown' and row['overall_verdict'] == 'pass'), 'Unknown required state cannot become pass')
        total = Decimal(0)
        for row in cost['rows']:
            measured = runs[row['run_id']]
            require(row['model'] == measured['model'], 'Cost model mismatch')
            require(row['total_input_tokens'] == measured['input_tokens_reported'], 'Cost input tokens mismatch')
            require(row['output_tokens'] == measured['output_tokens_reported'], 'Cost output tokens mismatch')
            require(row['cached_input_tokens'] == measured['cache_read_tokens_reported'], 'Cost cached tokens mismatch')
            require(row['uncached_input_tokens'] + row['cached_input_tokens'] == row['total_input_tokens'], 'Input decomposition mismatch')
            # This published v1 batch has no cache writes; never silently price future writes as zero.
            require(row['cache_write_tokens'] == 0, 'Cache writes require a new calculator revision')
            rate = row['usd_per_million']
            input_cost = Decimal(row['uncached_input_tokens']) * Decimal(rate['input']) / 1000000
            cached_cost = Decimal(row['cached_input_tokens']) * Decimal(rate['cache_read']) / 1000000 if row['cached_input_tokens'] else Decimal(0)
            output_cost = Decimal(row['output_tokens']) * Decimal(rate['output']) / 1000000
            require(input_cost == Decimal(row['uncached_input_cost_usd']), 'Input cost arithmetic mismatch')
            require(cached_cost == Decimal(row['cache_cost_usd']), 'Cached cost arithmetic mismatch')
            require(output_cost == Decimal(row['output_cost_usd']), 'Output cost arithmetic mismatch')
            value = input_cost + cached_cost + output_cost
            require(value == Decimal(row['total_reference_cost_usd']), 'Total cost mismatch')
            total += value
        require(total == Decimal(cost['batch_total_reference_cost_usd']), 'Batch cost mismatch')
        require(sum(Decimal(str(r['supervisor_seconds'])) for r in metrics['rows']) == Decimal(cost['batch_total_wall_seconds']), 'Batch time mismatch')
        count += 1
    return count


if __name__ == '__main__':
    print('Validated %d experiment(s); private evidence not required or inspected.' % validate())
