"""Copy the frozen array metrics, without importing training/model modules."""
from pathlib import Path
import ast

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def function(file, names):
    source = (ROOT/'pinn_pcm_sci'/file).read_text(encoding='utf-8')
    tree = ast.parse(source)
    return '\n\n'.join(ast.get_source_segment(source, node) for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name in names)


def main():
    out = HERE/'portable'; out.mkdir(exist_ok=True)
    pieces = ['''"""Frozen NumPy-only metrics copied from the repository at paper revision.

No model loading, neural execution, linear solve, or private repository path.
The only adaptations inject serialized constants/grid and a NumPy waveform.
Scientific definitions retain the published LF11 semantics, including the
historical bottom-current comparison against the reference TOP current.
"""
from __future__ import annotations
from types import SimpleNamespace
from typing import Any
import numpy as np
''']
    pieces.append(function('phk_v23_lf11.py', {'axis_weights'}))
    pieces.append(function('phk_v22r_evaluator.py', {'_event_summary'}))
    pieces.append(function('phk_v23_lf11_readout.py', {'readout'}))
    m = function('phk_v23_lf11_evaluation.py', {'time_rms', 'field_rms', 'metrics', 'comparison'})
    m = m.replace('    from .phk_v22r_evaluator import _physical_contract\n', '')
    m = m.replace('ev = _physical_contract().payload["qualification_event"]', 'ev = config["qualification_event"]')
    m = m.replace('physics.waveform(tensor(time)).numpy()', 'physics.waveform(time)')
    pieces.append(m)
    pieces.append(function('phk_v23_lf11_followup_evaluate.py', {'add_power_metrics'}))
    pieces.append(function('phk_v23_lf11_joint_evaluate.py', {'functional_comparison'}))
    (out/'frozen_metrics.py').write_text('\n\n'.join(pieces)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
