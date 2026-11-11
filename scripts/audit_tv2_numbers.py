"""Inventory every numeric token in docs/tv2/*.md and index JSON/CSV sources.

Source candidates are an index, NOT evidence that a claim is semantically true.
Use the accompanying manual review for context, units and proposed corrections.
Reads small reports only; never scans landing CSV data or runs Spark.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"\d+(?:[.,]\d+)*")


def normalized(token):
    # Vietnamese grouped integers versus decimal point/comma.
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token):
        return str(Decimal(token.replace('.', '')).normalize())
    try:
        return str(Decimal(token.replace(',', '.')).normalize())
    except InvalidOperation:
        return token


def numeric_keys(token):
    # 3.869 may be a decimal ratio OR a grouped integer: retain both candidates.
    keys = {normalized(token)}
    try:
        keys.add(str(Decimal(token.replace(',', '.')).normalize()))
    except InvalidOperation:
        pass
    return keys


def flatten(value, field=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten(child, f'{field}.{key}' if field else key)
    elif isinstance(value, list):
        yield field + '.length', len(value)
        for i, child in enumerate(value):
            yield from flatten(child, f'{field}[{i}]')
    elif not isinstance(value, bool) and value is not None:
        yield field, value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True, help='New output directory; never overwritten')
    args = parser.parse_args()
    out = Path(args.out_dir).resolve()
    if not out.is_relative_to(ROOT):
        parser.error('Output must be inside the repository')
    if out.exists():
        parser.error('Output exists; choose a new --out-dir')
    source_paths = sorted(set(
        list((ROOT / 'docs/evidence/tv2').rglob('*.json'))
        + list((ROOT / 'docs/evidence/tv2').rglob('*.csv'))
        + list((ROOT / 'data/real_sample3m_run01/reports').glob('*.json'))
        + list((ROOT / 'data/real_sample3m_run01/reports').glob('*.csv'))
    ))
    index = defaultdict(list)
    sources = []
    for path in source_paths:
        if path.name in {'number_inventory.csv', 'summary.json', 'source_index.json'}:
            continue  # Generated audit indexes are not experimental sources.
        rel = path.relative_to(ROOT).as_posix()
        sources.append({'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if path.suffix == '.json':
            values = flatten(json.loads(path.read_text(encoding='utf-8-sig')))
        else:
            with path.open(encoding='utf-8-sig', newline='') as handle:
                values = [(f'row[{i}].{k}', v) for i, row in enumerate(csv.DictReader(handle), 1)
                          for k, v in row.items() if v is not None]
        for field, value in values:
            string = str(value)
            # Index scalar numbers only, not numeric fragments of dates or UUIDs.
            if TOKEN.fullmatch(string):
                for key in numeric_keys(string):
                    index[key].append(f'{rel}#{field}={string}')
    inventory = []
    docs = []
    for path in sorted((ROOT / 'docs/tv2').glob('*.md')):
        rel = path.relative_to(ROOT).as_posix()
        docs.append({'path': rel, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        for line_num, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            for match in TOKEN.finditer(line):
                token = match.group()
                candidates = sorted(set(x for key in numeric_keys(token) for x in index.get(key, [])))
                inventory.append({'document': rel, 'line': line_num, 'column': match.start()+1,
                                  'token': token, 'candidate_count': len(candidates),
                                  'status': 'SOURCE_CANDIDATE_NOT_VERDICT' if candidates else 'CONTEXT_REVIEW',
                                  'source_candidates': ' | '.join(candidates[:8]), 'text': line})
    out.mkdir(parents=True)
    fields = ['document', 'line', 'column', 'token', 'candidate_count', 'status', 'source_candidates', 'text']
    with (out / 'number_inventory.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(inventory)
    summary = {'documents': docs, 'sources': sources, 'numeric_tokens': len(inventory),
               'tokens_per_document': dict(Counter(row['document'] for row in inventory)),
               'note': 'Every digit occurrence is inventoried, including headings, dates, IDs, code and paths. '
                       'Candidate matches do not verify meaning or units. Percentages are not converted to ratios. '
                       'See docs/evidence/tv2/audit_5b_review_20261111.md for contextual findings.'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out / 'source_index.json').write_text(json.dumps(dict(index), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('numeric_tokens', 'tokens_per_document')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
