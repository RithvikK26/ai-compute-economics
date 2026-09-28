import csv
import difflib
import hashlib
import importlib.metadata
import io
import json
import locale
import os
import platform
import socket
from decimal import Decimal, InvalidOperation
from pathlib import Path

from compute_economics.reporting import export_run, load_run

ROOT = Path.cwd()
OUT = Path(os.environ.get("DIAGNOSTIC_OUTPUT", "artifacts/diagnosis"))
OUT.mkdir(parents=True, exist_ok=True)

def deny_network(*args, **kwargs):
    raise AssertionError("Unexpected network")

socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network

def describe(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), crlf=raw.count(b"\r\n"), lone_lf=raw.count(b"\n")-raw.count(b"\r\n"), lone_cr=raw.count(b"\r")-raw.count(b"\r\n"), ends_crlf=raw.endswith(b"\r\n"), ends_lf=raw.endswith(b"\n"))

def compare(a, b):
    left, right = a.read_bytes(), b.read_bytes()
    al, bl = list(csv.reader(io.StringIO(left.decode(), newline=""))), list(csv.reader(io.StringIO(right.decode(), newline="")))
    differences, numbers = [], []
    for ri in range(max(len(al),len(bl))):
        aa = al[ri] if ri < len(al) else []
        bb = bl[ri] if ri < len(bl) else []
        for ci in range(max(len(aa),len(bb))):
            x = aa[ci] if ci < len(aa) else None
            y = bb[ci] if ci < len(bb) else None
            if x == y: continue
            d = dict(row_1based=ri+1,column_1based=ci+1,column=al[0][ci] if ci<len(al[0]) else None,key=aa[:3],expected=x,generated=y)
            differences.append(d)
            try:
                dx,dy=Decimal(x),Decimal(y)
                if dx!=dy: numbers.append(dict(d,delta=str(dy-dx)))
            except (InvalidOperation, TypeError): pass
    first = next((i for i,(x,y) in enumerate(zip(left,right)) if x!=y), min(len(left),len(right)) if len(left)!=len(right) else None)
    return dict(expected=describe(left),generated=describe(right),bytes_equal=left==right,normalized_newlines_equal=left.replace(b"\r\n",b"\n")==right.replace(b"\r\n",b"\n"),first_byte_difference=first,expected_hex_window=left[max(0,(first or 0)-30):(first or 0)+80].hex(),generated_hex_window=right[max(0,(first or 0)-30):(first or 0)+80].hex(),expected_rows=len(al),generated_rows=len(bl),columns_equal=al[0]==bl[0],row_keys_equal=[r[:3] for r in al]==[r[:3] for r in bl],parsed_cells_equal=al==bl,cell_difference_count=len(differences),numerical_difference_count=len(numbers),cell_differences=differences[:20],numerical_differences=numbers[:20],text_diff=list(difflib.unified_diff(left.decode().splitlines(),right.decode().splitlines(),fromfile="expected",tofile="generated"))[:100])

report = dict(environment=dict(python=platform.python_version(),system=platform.platform(),machine=platform.machine(),processor=platform.processor(),cpu_count=os.cpu_count(),locale=locale.setlocale(locale.LC_ALL,None),encoding=locale.getpreferredencoding(False),packages={n:importlib.metadata.version(n) for n in ["duckdb","pandas","numpy"]}),presets={})
for preset in ["stable_demand","demand_disappointment","delayed_capacity"]:
    run,_=load_run(ROOT/"scenarios"/(preset+".json"),ROOT/"data")
    generated=OUT/preset/"generated"
    export_run(run,generated)
    reference=ROOT/"examples" if preset=="stable_demand" else ROOT/"examples"/preset
    expected=OUT/preset/"expected"
    expected.mkdir(parents=True,exist_ok=True)
    comparisons={}
    for source in sorted(reference.glob("*.csv")):
        (expected/source.name).write_bytes(source.read_bytes())
        comparisons[source.name]=compare(source,generated/source.name)
    report["presets"][preset]=comparisons
    print(json.dumps(dict(preset=preset,annual=comparisons["annual_costs.csv"])),flush=True)
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report["environment"]),flush=True)
