import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.lab_parser import parse_lab_text

text = """[진검]  현장검사[Heparinized WB, Artery]
　채혈: 2026-04-09 01:07  접수: 2026-04-09 05:39  보고: 2026-04-09 05:39  -
　검사명                               결과값       단위         참고치
　ABGA ,Ca++,electrolyte
　　pH                                 7.430                     7.35~7.45
　　PCO₂                              51.0  ▲     mmHg         35~45
　　PO₂                               53.0  ▼     mmHg         83~108
　　Na (ABGA)                          134.0  ▼    mmol/L       136~146
　　K (ABGA)                           5.50  ▲     mmol/L       3.5~5.1

[진검]  뇨[Urine, Random]
　채혈: 2026-03-17 08:22  접수: 2026-03-17 10:48  보고: 2026-03-17 11:08  -
　검사명                               결과값       단위         참고치
　(뇨)Routine U/A (10종)
　　(뇨) S.G                           1.024                     1.005~1.03
　　(뇨) Protein                       2+ (65~200mg/dl)             Negative
　　(뇨) Blood                         3+ (≥0.450mg/dl)             Negative
　(뇨) Urine Microscopy
　　(뇨) RBC                           100이상 cells/HPF             0~3 cells/HPF
　　(뇨) WBC                           1~3 cells/HPF             0~3 cells/HPF"""

rows, qual_rows, _, _ = parse_lab_text(text)
print("QUANTITATIVE:")
for r in rows:
    print(f"Name: {r.name}, Value: {r.value}, Unit: {r.unit}, Ref: {r.ref}")

print("\nQUALITATIVE:")
for r in qual_rows:
    print(f"Name: {r.item}, Value: {r.result}, Unit: {r.unit}, Ref: {r.ref}, Status: {r.status}")
