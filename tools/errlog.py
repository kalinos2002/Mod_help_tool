#!/usr/bin/env python3
"""Grupuje log kompilacji javac/Gradle w kolejkę napraw (zamiast 1500 linii błędów -> kilka kategorii).

Użycie:
  ./gradlew :common:compileJava --no-daemon > build.log 2>&1
  python tools/errlog.py build.log            # podsumowanie w konsoli
  python tools/errlog.py build.log --md out.md  # to samo do pliku, można wkleić do czatu

Kolejność plików = kolejność warstw (najpierw fundament, na końcu klient/JEI),
bo błędy w górnych warstwach często są tylko skutkiem błędów niżej.
"""
import re, sys, argparse
from collections import Counter, defaultdict

LAYERS = [
    ('1 fundament: platform/config/inv/data', ['/platform/', '/config/', '/inv/', '/data/', 'ModTags', 'ChickensConfig', 'ChickenSpawnConfig', 'Registrar', 'Chickens.java']),
    ('2 rejestracje: ModContent', ['ModContent']),
    ('3 bloki i block entity', ['/block/']),
    ('4 menu', ['/menu/']),
    ('5 encje', ['/entity/']),
    ('6 itemy i receptury', ['/item/', '/recipe/']),
    ('7 klient (renderery, ekrany)', ['/client/']),
    ('8 JEI', ['/jei/']),
    ('9 loadery', ['/fabric/', '/neoforge/']),
]
ERR = re.compile(r'^(?P<file>.+?\.java):(?P<line>\d+): error: (?P<msg>.*)$')


def layer_of(path):
    for name, keys in LAYERS:
        if any(k in path for k in keys):
            return name
    return '0 inne'


def parse(lines):
    errs, cur = [], None
    for ln in lines:
        ln = ln.replace('\\', '/')
        m = ERR.match(ln.strip('\r\n'))
        if m:
            cur = dict(m.groupdict(), symbol=None, location=None)
            errs.append(cur)
        elif cur:
            s = ln.strip()
            if s.startswith('symbol:'): cur['symbol'] = s.split(':', 1)[1].strip()
            elif s.startswith('location:'): cur['location'] = s.split(':', 1)[1].strip()
    return errs


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('log'); ap.add_argument('--md')
    a = ap.parse_args()
    raw = open(a.log, 'rb').read()
    if a.log.lower().endswith('.html'):   # raport Gradle: build/reports/problems/problems-report.html
        import json
        t = raw.decode('utf-8', errors='replace')
        i = t.index('// begin-report-data') + len('// begin-report-data'); j = t.index('// end-report-data')
        data = json.loads(t[i:j].strip().rstrip(');').rstrip())
        seen, blocks = set(), []
        for d in data.get('diagnostics', []):
            pd = d.get('problemDetails') or ''
            if 'error:' in pd and pd not in seen:
                seen.add(pd); blocks.append(pd)
        raw = '\n'.join(blocks).encode('utf-8')
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):   # PowerShell zapisuje UTF-16
        text_in = raw.decode('utf-16', errors='replace')
    else:
        text_in = raw.decode('utf-8', errors='replace')
    text_in = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text_in)  # kody ANSI
    errs = parse(text_in.splitlines())
    out = []
    P = out.append
    P(f'# Podsumowanie błędów kompilacji\n\nŁącznie: **{len(errs)}** błędów w {len({e["file"] for e in errs})} plikach\n')

    kinds = Counter()
    for e in errs:
        k = re.sub(r'package [\w.]+ does not exist', 'X does not exist (pakiet)', e['msg'])
        kinds[k] += 1
    P('## Rodzaje błędów')
    for k, n in kinds.most_common(12): P(f'- {n}× {k}')

    pk = Counter(e['msg'].split(' does not exist')[0].replace('package ', '')
                 for e in errs if 'does not exist' in e['msg'])
    if pk:
        P('\n## Brakujące pakiety (zwykle przeniesione klasy — użyj tools/check_imports.py)')
        for k, n in pk.most_common(25): P(f'- {n}× `{k}`')

    sy = Counter(e['symbol'] for e in errs if e['symbol'])
    if sy:
        P('\n## Najczęściej brakujące symbole')
        for k, n in sy.most_common(30): P(f'- {n}× `{k}`')

    ov = [e for e in errs if 'does not override' in e['msg']]
    if ov:
        P(f'\n## Zmienione sygnatury metod ({len(ov)}× „does not override")')
        c = Counter((e['file'].split('/')[-1]) for e in ov)
        for k, n in c.most_common(15): P(f'- {n}× {k}')

    P('\n## Kolejka napraw (warstwami)')
    by = defaultdict(Counter)
    for e in errs: by[layer_of(e['file'])][e['file'].split('/')[-1]] += 1
    for layer in sorted(by):
        P(f'\n### {layer} — {sum(by[layer].values())} błędów')
        for f, n in by[layer].most_common(): P(f'- {f}: {n}')

    text = '\n'.join(out)
    if a.md: open(a.md, 'w', encoding='utf-8').write(text); print('zapisano', a.md)
    else: print(text)

if __name__ == '__main__':
    main()
