"""Cell-overlap restriction and report-only threshold diagnostics.

No neural model or PDE solve is used here. Thresholding and restriction are
deliberately compared instead of being treated as interchangeable operations.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse


def overlap_axis(source_count: int, target_count: int) -> sparse.csr_matrix:
    source = np.linspace(0., 1., source_count + 1)
    target = np.linspace(0., 1., target_count + 1)
    overlap = np.maximum(0., np.minimum(target[1:, None], source[None, 1:]) -
                         np.maximum(target[:-1, None], source[None, :-1]))
    return sparse.csr_matrix(overlap / np.diff(target)[:, None])


@dataclass
class CellRestriction:
    source_nx: int
    source_nz: int
    target_nx: int = 160
    target_nz: int = 80

    def __post_init__(self):
        self.operator = sparse.kron(overlap_axis(self.source_nz, self.target_nz),
                                    overlap_axis(self.source_nx, self.target_nx), format="csr")
        if np.any(self.operator.data < 0):
            raise ValueError("restriction must be nonnegative")
        np.testing.assert_allclose(np.asarray(self.operator.sum(axis=1)).ravel(), 1., atol=2e-14, rtol=0)
        expected_column_mass = (self.target_nx*self.target_nz)/(self.source_nx*self.source_nz)
        np.testing.assert_allclose(np.asarray(self.operator.sum(axis=0)).ravel(),
                                   expected_column_mass, atol=3e-14, rtol=0)

    def __call__(self, values: np.ndarray, chunk: int = 32) -> np.ndarray:
        if values.ndim != 2 or values.shape[1] != self.source_nx*self.source_nz:
            raise ValueError("expected time by z-major cells")
        out = np.empty((len(values), self.target_nx*self.target_nz), dtype=np.float64)
        for start in range(0, len(values), chunk):
            stop = min(start + chunk, len(values))
            out[start:stop] = (self.operator @ values[start:stop].T).T
        return out


def threshold_diagnostic(predicted_phase, restricted_phase, restricted_active,
                         times, windows, threshold=.5):
    predicted = predicted_phase >= threshold
    coarse = restricted_phase >= threshold
    fraction = restricted_active
    if np.any(fraction < -2e-14) or np.any(fraction > 1 + 2e-14):
        raise ValueError("restricted indicator outside [0,1]")
    coarse_difference = np.mean(predicted != coarse, axis=1)
    native_difference = np.mean(np.where(predicted, 1-fraction, fraction), axis=1)
    disagreement = np.mean(np.abs(fraction-coarse), axis=1)
    average = lambda value: float(np.trapezoid(value, times)/(times[-1]-times[0]))
    primary, alternative, bound = map(average, (coarse_difference, native_difference, disagreement))
    if abs(primary-alternative) > bound + 2e-14:
        raise AssertionError("threshold/restriction discrepancy bound failed")
    edges = np.concatenate(([times[0]], .5*(times[:-1]+times[1:]), [times[-1]]))
    weights = np.diff(edges)/(times[-1]-times[0])
    cycles = []
    for i, (lo, hi) in enumerate(windows[::2], 1):
        selected = (times >= lo) & (times <= hi)
        measure = weights[selected, None] / predicted.shape[1]
        pa, ca, fa = predicted[selected], coarse[selected], fraction[selected]
        mass_coarse = float(np.sum(measure*ca))
        mass_native = float(np.sum(measure*fa))
        tp_coarse = float(np.sum(measure*(pa & ca)))
        tp_native = float(np.sum(measure*pa*fa))
        pred_mass = float(np.sum(measure*pa))
        cycles.append(dict(cycle=i, reference_mass_primary=mass_coarse,
            reference_mass_indicator_restriction=mass_native,
            overlap_primary=tp_coarse, overlap_indicator_restriction=tp_native,
            predicted_mass=pred_mass, recall_primary=tp_coarse/max(mass_coarse,1e-12),
            recall_indicator_restriction=tp_native/max(mass_native,1e-12),
            precision_indicator_restriction=tp_native/max(pred_mass,1e-12),
            mass_ratio_indicator_restriction=pred_mass/max(mass_native,1e-12)))
    return dict(S_primary=primary, S_indicator_restriction=alternative,
        S_absolute_difference=abs(primary-alternative), S_difference_bound=bound,
        cycles=cycles, role="report-only mapping sensitivity; not a replacement gate")


def focused_checks():
    rng = np.random.default_rng(90217)
    # Nontrivial 3:2 spatial ratio matches the proposed reference experiment.
    mapping = CellRestriction(12, 6, 8, 4)
    fields = rng.uniform(0, 1, (7, 72))
    mapped = mapping(fields, chunk=3)
    np.testing.assert_allclose(mapping(np.ones_like(fields)), 1., rtol=0, atol=2e-14)
    np.testing.assert_allclose(mapped.mean(axis=1), fields.mean(axis=1), rtol=0, atol=2e-14)
    np.testing.assert_allclose(CellRestriction(12, 6, 12, 6)(fields), fields, rtol=0, atol=2e-14)
    times = np.linspace(0, 2.5, 7)
    diag = threshold_diagnostic(rng.uniform(0,1,mapped.shape), mapped,
        mapping((fields>=.5).astype(float)), times, [[0,.35],[.35,1.25],[1.25,1.6],[1.6,2.5]])
    full = CellRestriction(240,120)
    return dict(status="PASS", identity=True, constant_preservation=True,
        integral_preservation=True, threshold_difference_bound=True,
        production_shape=list(full.operator.shape), production_nonzeros=full.operator.nnz,
        synthetic_S_difference=diag["S_absolute_difference"],
        synthetic_bound=diag["S_difference_bound"], new_pde_solves=0,
        new_checkpoint_evaluations=0)
