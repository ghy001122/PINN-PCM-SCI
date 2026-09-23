"""Second and final zero-update CPU profile, with native Windows memory counters.

Run each arm in a fresh process. The first profile could not measure memory
because psutil is absent; no dependency installation or optimizer is needed.
"""
import argparse
import ctypes
from ctypes import wintypes
import time
import torch
from pinn_pcm_sci.phk_v23_phase_moments_run import (
    ROOT, ARMS, read, parent_model, full_pool, VisibleData, PhaseExperiment, save_json,
)


def memory():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
                'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
                'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    query = ctypes.WinDLL('psapi', use_last_error=True).GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    query.restype = wintypes.BOOL
    value = Counters();value.cb = ctypes.sizeof(value)
    if not query(kernel.GetCurrentProcess(), ctypes.byref(value), value.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return {name: getattr(value, name) for name in
            ('PeakWorkingSetSize', 'WorkingSetSize', 'PrivateUsage', 'PeakPagefileUsage')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm', choices=ARMS);a = p.parse_args()
    run = ROOT/'outputs/runs/20260923-relative-phase-moments'
    assert read(run/'profile.json')['passes_per_arm'] == 1
    out = run/f'profile-memory-{a.arm}.json'
    if out.exists():
        raise FileExistsError('Second profile already recorded; no third pass')
    cfg = read(run/'frozen-config.json');torch.set_num_threads(cfg['cpu_threads'])
    before = memory();_, parent = parent_model(cfg)
    exp = PhaseExperiment(cfg, parent['model_state_dict'], VisibleData(ROOT/cfg['sparse']), 'cpu', a.arm)
    start = time.perf_counter()
    value, parts = exp.objective(exp.obs.groups(), full_pool(cfg), read(run/'calibration.json'), .1, backward=True)
    elapsed = time.perf_counter()-start
    gradient = torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).reshape(-1) for p in exp.parameters])
    assert torch.isfinite(gradient).all()
    save_json(out, dict(arm=a.arm, pass_number=2, optimizer_updates=0, reference_read=False,
        objective=float(value), gradient_norm=float(torch.linalg.vector_norm(gradient)), components=parts,
        elapsed_seconds=elapsed, statistics=exp.statistics(), before=before, after=memory(),
        memory_unit='bytes', memory_scope='fresh process peak includes imports, parent, model and one full gradient'))
    print(out.name, flush=True)


if __name__ == '__main__':main()
