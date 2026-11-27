"""Summarise Altium's DRC text report (hardware/Project Outputs/Design Rule Check - DebugBoard.drc).

Prints the violation count per rule, then every violation that is not an un-routed net.
Usage: python tools/drc_summary.py
"""
import os, re
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hardware', 'Project Outputs', 'Design Rule Check - DebugBoard.drc')
rule, rows, detail = None, [], {}
for line in open(p, encoding='latin-1'):
    line = line.strip()
    if line.startswith(('Date', 'Time', 'ERROR', 'Violations Detected')): print(line)
    m = re.match(r'Processing Rule : (.*)', line)
    if m: rule = m.group(1); detail[rule] = []; continue
    m = re.match(r'Rule Violations :(\d+)', line)
    if m and rule: rows.append((int(m.group(1)), rule)); rule = None; continue
    if rule and line: detail[rule].append(re.sub(r'\([-0-9.]+mil,[-0-9.]+mil\)', '', line))
for n, r in rows:
    if n: print(f'{n:5}  {r[:110]}')
print('total', sum(n for n, r in rows), ' rules with no violations:', sum(1 for n, r in rows if not n))
for r, lines in detail.items():
    if lines and not r.startswith('Un-Routed'):
        print('\n' + r[:110])
        for l in lines[:60]: print('   ', l.replace('Violation between ', '')[:230])
