"""Spielwerk-Beispiel in Python: Pfeiltasten ohne Ticks oder Fremdbibliotheken.

Die Spielregeln sehen nur einfache Textzeilen, nicht HTML oder CSS.
"""
import sys

x, y = 100, 120
print('CREATE kugel farbkugel', flush=True)
print(f'MOVE kugel {x} {y}', flush=True)
print('SHOW kugel', flush=True)
for line in sys.stdin:
    words = line.strip().split()
    if len(words) != 2 or words[0] != 'KEYDOWN':
        continue
    key = words[1]
    if key == 'ArrowLeft':
        x -= 10
    elif key == 'ArrowRight':
        x += 10
    elif key == 'ArrowUp':
        y -= 10
    elif key == 'ArrowDown':
        y += 10
    else:
        continue
    x = max(0, min(280, x))
    y = max(0, min(200, y))
    print(f'MOVE kugel {x} {y}', flush=True)
