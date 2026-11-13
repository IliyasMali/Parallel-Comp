#!/usr/bin/env python3
"""Reproducible parallel-computing lab: tasks 0-4 with raw logs and a Markdown report.

Run quick validation: python parallel_lab.py --profile pilot --id 230103344
Run prescribed sizes: python parallel_lab.py --profile full --id 230103344

IMPORTANT: the pilot intentionally reduces compute sizes and repetitions. The full
profile is computationally expensive. Both run on the CURRENT machine, not on a
student's remote laptop. A completed instructor-compliant run must occur locally,
offline, and independently, as the PDF explicitly requires.
"""
from __future__ import annotations

import argparse
import array
import datetime
import math
import multiprocessing as mp
from multiprocessing import shared_memory
import os
from pathlib import Path
import platform
import sys
import time
import subprocess
import json
import traceback

from harness import emit_verify_tag, run_benchmark, summarize_ms

M64 = 0xFFFFFFFFFFFFFFFF
MULT = 6364136223846793005
TILES = [4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
CHUNKS = [1, 4, 16, 64, 256, 1024]


class Printer:
    """Mirror telemetry to the console and a durable log file immediately."""
    def __init__(self, log_file=None, prior_lines=None):
        self.lines = list(prior_lines or [])
        self.log_file = Path(log_file) if log_file else None
        if self.log_file is not None:
            self.log_file.write_text('\n'.join(self.lines) + ('\n' if self.lines else ''),
                                     encoding='utf-8')

    def __call__(self, msg=""):
        s = str(msg)
        print(s, flush=True)
        self.lines.append(s)
        if self.log_file is not None:
            with self.log_file.open('a', encoding='utf-8') as f:
                f.write(s + '\n')


def read_sysfs(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, ValueError):
        return "unavailable"


def mac_sysctl(key):
    """Return a sysctl value, or None if this macOS key is not exposed."""
    try:
        result = subprocess.run(['sysctl', '-n', key], capture_output=True,
                                text=True, timeout=3, check=False)
        return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def first_positive_sysctl(*keys):
    for key in keys:
        value = mac_sysctl(key)
        try:
            number = int(value) if value is not None else 0
        except (TypeError, ValueError):
            continue
        if number > 0:
            return number
    return None


def pretty_bytes(value):
    if value is None:
        return 'unavailable'
    if value >= 1024 * 1024:
        return f'{value / (1024 * 1024):g} MiB'
    if value >= 1024:
        return f'{value / 1024:g} KiB'
    return f'{value} B'


def hardware():
    """Identify the CPU and cache topology without third-party packages."""
    logical = mp.cpu_count()
    if sys.platform == 'darwin':
        physical = first_positive_sysctl('hw.physicalcpu') or logical
        logical = first_positive_sysctl('hw.logicalcpu') or logical
        brand = mac_sysctl('machdep.cpu.brand_string')
        if not brand:
            if platform.machine() == 'arm64':
                brand = 'Apple Silicon (model: ' + (mac_sysctl('hw.model') or 'unknown') + ')'
            else:
                brand = platform.processor() or platform.machine()
        l1 = first_positive_sysctl('hw.l1dcachesize', 'hw.perflevel0.l1dcachesize')
        l2 = first_positive_sysctl('hw.l2cachesize', 'hw.perflevel0.l2cachesize')
        l3 = first_positive_sysctl('hw.l3cachesize')
        pcores = first_positive_sysctl('hw.perflevel0.physicalcpu')
        ecores = first_positive_sysctl('hw.perflevel1.physicalcpu')
        return {
            'cpu': brand,
            'physical': physical,
            'logical': logical,
            'line': first_positive_sysctl('hw.cachelinesize') or 'unavailable',
            'l1d': pretty_bytes(l1),
            'l2': pretty_bytes(l2),
            'l3': pretty_bytes(l3),
            'performance_cores': pcores if pcores is not None else 'unavailable',
            'efficiency_cores': ecores if ecores is not None else 'unavailable',
            'threads_core': f'{logical / physical:.2f}' if physical else 'unavailable',
            'python_os': f'{platform.python_version()} / {platform.system()} {platform.release()}',
            'affinity': 'not exposed by macOS',
        }
    model = 'unknown'
    try:
        for line in Path('/proc/cpuinfo').read_text().splitlines():
            if line.startswith('model name'):
                model = line.split(':', 1)[1].strip()
                break
    except OSError:
        model = platform.processor() or 'unknown'
    # Linux's os.cpu_count() is logical CPUs, not necessarily physical cores.
    physical = logical
    try:
        topology = Path('/sys/devices/system/cpu/cpu0/topology/thread_siblings_list').read_text().strip()
        # This does not prove the physical-core count inside a VM; report an estimate.
        if ',' in topology:
            sibling_count = len(topology.split(','))
        elif '-' in topology:
            a, b = topology.split('-', 1)
            sibling_count = int(b) - int(a) + 1
        else:
            sibling_count = 1
        physical = max(1, logical // sibling_count)
    except (OSError, ValueError):
        pass
    return {
        'cpu': model, 'physical': physical, 'logical': logical,
        'line': read_sysfs('/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size'),
        'l1d': read_sysfs('/sys/devices/system/cpu/cpu0/cache/index0/size'),
        'l2': read_sysfs('/sys/devices/system/cpu/cpu0/cache/index2/size'),
        'l3': read_sysfs('/sys/devices/system/cpu/cpu0/cache/index3/size'),
        'performance_cores': 'not applicable', 'efficiency_cores': 'not applicable',
        'threads_core': round(logical / physical, 3) if physical else 'unavailable',
        'python_os': f'{platform.python_version()} / {platform.system()} {platform.release()}',
        'affinity': len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else logical,
    }


def harmonic_counts(p):
    counts = [1]
    k = 2
    while k < p:
        counts.append(k)
        k *= 2
    if p > 1 and p not in counts:
        counts.append(p)
    return counts


def table(headers, rows):
    def f(x):
        return str(x).replace('|', '\\|').replace('\n', ' ')
    return ('| ' + ' | '.join(map(f, headers)) + ' |\n' +
            '| ' + ' | '.join(['---'] * len(headers)) + ' |\n' +
            ''.join('| ' + ' | '.join(map(f, row)) + ' |\n' for row in rows))


def q(x, dp=4):
    return f'{x:.{dp}f}' if isinstance(x, (int, float)) else str(x)


def phase0(student_id, log, md):
    log('--- PHASE0: clock calibration ---')
    hw = hardware()
    reads = 2_000_000
    t0 = time.perf_counter_ns()
    for _ in range(reads):
        time.perf_counter_ns()
    t1 = time.perf_counter_ns()
    latency = (t1 - t0) / reads
    tag = emit_verify_tag('PHASE0', student_id, latency, hw['physical'])
    for k, v in hw.items():
        log(f'PHASE0 {k}={v}')
    log(f'PHASE0 clock_reads={reads} total_ns={t1-t0} average_latency_ns={latency:.4f}')
    log(tag)
    md.extend(['## Phase 0. Hardware and timing calibration', '',
       table(['Hardware parameter','Observed value','Hardware parameter','Observed value'], [
           ['CPU model', hw['cpu'], 'L1d (per visible core)', hw['l1d']],
           ['Physical cores (OS-reported)', hw['physical'], 'L2 (OS-reported)', hw['l2']],
           ['Logical CPUs (Plog)', hw['logical'], 'L3', hw['l3']],
           ['Cache line (bytes)', hw['line'], 'Python / OS', hw['python_os']],
           ['Performance cores (if exposed)', hw['performance_cores'], 'Efficiency cores (if exposed)', hw['efficiency_cores']],
       ]),
       f'Two-million-read mean `time.perf_counter_ns()` call latency: **{latency:.4f} ns** (includes loop and dispatch overhead).',
       f'`{tag}`', ''])
    return hw, tag


# ---------- Phase 1 ----------
def fs_worker(shm_name: str, slot_idx: int, iterations: int) -> None:
    shm = shared_memory.SharedMemory(name=shm_name)
    # Use the actual shared-buffer capacity; do not assume <= 16 workers.
    arr = ( __import__('ctypes').c_uint64 * (shm.size // 8) ).from_buffer(shm.buf)
    acc = arr[slot_idx]
    for i in range(iterations):
        acc = (acc * MULT + (i | 1)) & M64
        arr[slot_idx] = acc
    del arr
    shm.close()


def fs_trial(ctx, p, stride, total_steps):
    capacity = max(4096, ((p - 1) * stride + 1) * 8)
    s = shared_memory.SharedMemory(create=True, size=capacity)
    try:
        parts = [total_steps // p + (1 if t < total_steps % p else 0) for t in range(p)]
        jobs = [ctx.Process(target=fs_worker, args=(s.name, t*stride, parts[t])) for t in range(p)]
        for job in jobs:
            job.start()
        for job in jobs:
            job.join()
        errors = [job.exitcode for job in jobs if job.exitcode != 0]
        if errors:
            raise RuntimeError(f'fs worker exit failures: {errors}')
    finally:
        s.close()
        s.unlink()


def phase1(student_id, ctx, pphys, plog, profile, log, md):
    log('--- PHASE1: false sharing ---')
    steps = 24_000_000 if profile == 'full' else 120_000
    warm, timed = (2, 7) if profile == 'full' else (1, 3)
    md.extend(['## Phase 1. False sharing and Karp–Flatt', '',
       f'Measured workload: **M={steps:,}** total read/modify/write steps per trial; '
       f'**{warm}** warm-up and **{timed}** timed repetitions. Each worker owns a distinct 64-bit word; '
       'no race exists in the arithmetic output.', ''])
    stride_rows = []
    stride_stats = {}
    for stride in [1,2,4,8,16,32]:
        stats = run_benchmark(lambda:fs_trial(ctx, pphys, stride, steps), warm, timed)
        stride_stats[stride] = stats
        throughput = steps / (stats.median_ms * 1000)
        stride_rows.append([stride, stride*8, q(stats.median_ms, 3), q(stats.iqr_ms, 3), q(throughput, 3)])
        log(f'PHASE1 stride={stride} p={pphys} M={steps} min_ms={stats.min_ms:.4f} median_ms={stats.median_ms:.4f} iqr_ms={stats.iqr_ms:.4f} max_ms={stats.max_ms:.4f} throughput_Mops={throughput:.4f}')
    md.extend(['### Table 1A. Stride sensitivity (p = visible CPU count)', '',
        table(['Stride (words)', 'Separation (bytes)', 'Median (ms)', 'IQR (ms)', 'Mops/s'], stride_rows), ''])
    scaling_stats = {}
    rows = []
    for stride in [1,16]:
        bench_by_p = {}
        for p in harmonic_counts(plog):
            if p == pphys and stride in stride_stats:
                stats = stride_stats[stride]
            else:
                stats = run_benchmark(lambda p=p, stride=stride:fs_trial(ctx,p,stride,steps), warm, timed)
            bench_by_p[p] = stats.median_ms
        scaling_stats[stride] = bench_by_p
        t1 = bench_by_p[1]
        for p, tp in bench_by_p.items():
            sp = t1/tp
            ep = sp / p
            kf = ((1/sp)-(1/p))/(1-(1/p)) if p >= 2 else None
            rows.append([stride,p,q(tp,3),q(sp,3),q(ep,3),q(kf,4) if kf is not None else 'n/a'])
            log(f'PHASE1 scale stride={stride} p={p} T_ms={tp:.4f} S={sp:.5f} E={ep:.5f} e={kf if kf is not None else "n/a"}')
    md.extend(['### Table 1B. Process scaling and Karp–Flatt serial fraction', '',
         table(['Stride','p','Median (ms)','Speedup S','Efficiency E','Karp–Flatt e'],rows), ''])
    near = stride_stats[1].median_ms
    separated = stride_stats[16].median_ms
    ratio = near/separated
    deltas = [(s, (stride_stats[prev].median_ms - stride_stats[s].median_ms)/stride_stats[prev].median_ms*100)
              for prev,s in zip([1,2,4,8,16], [2,4,8,16,32])]
    boundary = max(deltas, key=lambda x: x[1]); fsp = scaling_stats[1]; iso = scaling_stats[16]
    md.extend([
        f'**Observation.** At p={pphys}, median time for adjacent words is {near:.3f} ms and '
        f'for 128-byte separation is {separated:.3f} ms (ratio {ratio:.3f}×). '
        f'The largest adjacent tested reduction occurs at stride {boundary[0]} '
        f'({boundary[0]*8} bytes): {boundary[1]:.2f}%. '
        'A single noisy minimum is not definitive evidence of the hardware line size.',
        f'The OS-reported cache-line width is {hardware()["line"]} bytes. Stores to '
        'different words inside one cache line can trigger ownership transfers. '
        'The observed Karp–Flatt fraction also includes scheduling/startup costs and is not '
        'a pure serial-code fraction; a smooth rather than sharp stride trend does not '
        'prove a specific coherence-line boundary.',
        'The formula used is `e(p) = (1/S_p - 1/p)/(1 - 1/p)` for p >= 2. '
        'A growing value with increasing p indicates costs absent from ideal linear scaling, '
        'including coherence invalidations, scheduler overhead, interpreter work and CPU contention.',
    ])
    tag = emit_verify_tag('PHASE1', student_id, near, separated)
    log(tag)
    md.extend([f'`{tag}`', ''])
    return tag


# ---------- Phase 2 ----------
def stage_a(n):
    accumulator = 0.0
    for i in range(max(1, int(.05*n))):
        x = (i % 10007 + 1) / 10009
        for j in range(6):
            y = x + j * 0.00013
            accumulator += math.sin(y) + math.sqrt(y)
    return accumulator


def stage_b_partition(args):
    start, stop = args
    accumulator = 0.0
    for i in range(start, stop):
        x = (i % 8191 + 1) / 8192
        for _ in range(35):
            x = (x*1.000000011 + 0.00000011) + 0.0004*math.sin(x)
        accumulator += x
    return accumulator


def partition(n, p):
    return [(t*n//p, (t+1)*n//p) for t in range(p)]


def pipeline_trial(pool, n, p):
    t0 = time.perf_counter_ns()
    sa = stage_a(n)
    t1 = time.perf_counter_ns()
    part = pool.map(stage_b_partition, partition(n,p), chunksize=1)
    t2 = time.perf_counter_ns()
    return ((t2-t0)/1e6, (t1-t0)/1e6, sa + sum(part))


def sample_pipeline(pool, n, p, warm, timed):
    for _ in range(warm):
        pipeline_trial(pool, n, p)
    timings = [pipeline_trial(pool,n,p) for _ in range(timed)]
    total_stats = summarize_ms([x[0] for x in timings]); serial_stats = summarize_ms([x[1] for x in timings])
    return total_stats, serial_stats, timings[-1][2]


def phase2(student_id, ctx, pphys, plog, profile, log, md, hw=None):
    log('--- PHASE2: strong/weak scaling ---')
    nstrong = 1_600_000 if profile == 'full' else 15_000
    n0 = 250_000 if profile == 'full' else 5_000
    warm, timed = (2,7) if profile == 'full' else (1,3)
    md.extend(['## Phase 2. Strong vs weak scaling', '',
       f'Strong scaling: fixed N={nstrong:,}; weak scaling: N0={n0:,} per process. '
       f'{warm} warm-up / {timed} timed trials; the pool is instantiated outside the timer. '
       'Stage A executes six sin + six sqrt calls per item on the first 5% of items; '
       'Stage B executes 35 deterministic multiply-add/trig iterations per item.', ''])
    strong, weak, sr, wr = {}, {}, [], []
    for p in range(1, plog+1):
        with ctx.Pool(processes=p) as pool:
            s, a, check = sample_pipeline(pool, nstrong, p, warm, timed)
            w, aw, check_w = sample_pipeline(pool, p*n0, p, warm, timed)
        strong[p] = (s.median_ms, a.median_ms)
        weak[p] = (w.median_ms, aw.median_ms)
        log(f'PHASE2 p={p} strong_N={nstrong} T_ms={s.median_ms:.4f} serial_ms={a.median_ms:.4f} total_checksum={check:.9f} weak_N={p*n0} T_ms={w.median_ms:.4f} serial_ms={aw.median_ms:.4f} weak_checksum={check_w:.9f}')
    ts1 = strong[1][0]
    tw1 = weak[1][0]
    for p in range(1, plog+1):
        ts, sa = strong[p]; tw, wa = weak[p]
        ss = ts1/ts
        es = ss/p
        ew = tw1/tw
        alpha = wa/tw
        sg = p-alpha*(p-1)
        sr.append([p, nstrong, q(ts,3), q(ss,3),q(es,3),q(sa,3)])
        wr.append([p,p*n0,q(tw,3),q(ew,3),q(alpha,4),q(sg,3)])
    md.extend(['### Table 2A. Strong scaling', '',
        table(['p','N','T (ms)','Speedup','Efficiency','Serial A (ms)'],sr), '',
        '### Table 2B. Weak scaling', '',
        table(['p','N(p)','T (ms)','Efficiency','alpha','Gustafson S'],wr), ''])
    serial_fraction = strong[1][1]/strong[1][0]
    amdahl_max = 1/serial_fraction
    amdahl_plog = 1/(serial_fraction + (1-serial_fraction)/plog)
    obs = ts1/strong[plog][0]
    gust = plog - (weak[plog][1]/weak[plog][0])*(plog-1)
    margin = []
    for p in range(2, plog+1):
        margin.append((p,ts1/strong[p][0]-ts1/strong[p-1][0]))
    marginal_text = '; '.join(f'p {p-1}->{p}: {d:+.3f}' for p,d in margin)
    # Quantify the marginal speedup change at the architectural transition
    # when the OS exposes a meaningful P/E boundary or SMT transition.
    p_cores = hw.get('performance_cores') if hw else None
    transition = None
    boundary_label = ''
    if isinstance(p_cores, int) and 2 <= p_cores < plog:
        transition = p_cores
        boundary_label = 'OS-reported performance-core count'
    elif 2 <= pphys < plog:
        transition = pphys
        boundary_label = 'physical-core to additional logical-thread boundary'
    if transition is not None:
        older = (ts1 / strong[transition][0]) - (ts1 / strong[transition-1][0])
        newer = (ts1 / strong[transition+1][0]) - (ts1 / strong[transition][0])
        change = ((older - newer) / abs(older) * 100) if older else None
        if change is not None:
            transition_text = (
                f'At the {boundary_label} (p={transition} -> {transition+1}), '
                f'marginal speedup changes from {older:+.5f} to {newer:+.5f}; '
                f'percentage change relative to the preceding increment is '
                f'{change:+.2f}% (positive means a drop). '
                'Scheduling does not guarantee the process is pinned to a particular core class.'
            )
        else:
            transition_text = 'Cannot calculate a percentage change: preceding marginal speedup was zero.'
    else:
        transition_text = (
            f'No distinct SMT physical-to-logical transition is observable: '
            f'physical={pphys}, logical={plog}. '
            'The operating system did not report a usable performance-core boundary '
            'within the measured range; marginal increments above can still be examined.'
        )
    md.extend([
        f'**Amdahl analysis:** measured serial fraction `s = T_A(1)/T_strong(1)` '
        f'= {serial_fraction:.5f}; theoretical S_inf = {amdahl_max:.3f}, '
        f'S_Amdahl({plog}) = {amdahl_plog:.3f}; observed S_strong({plog}) = {obs:.3f}.',
        f'**Marginal strong speedup** for each added process: {marginal_text}.',
        '**Boundary analysis:** ' + transition_text,
        f'The operating system reports {pphys} physical and {plog} logical cores. '
        'On Apple Silicon, performance/efficiency clusters can cause inflections '
        'without SMT. A change in marginal speedup alone cannot establish which '
        'core class or resource is responsible.',
        'Gustafson scaling assumes a fixed serial fraction while parallel work '
        'grows with p. Here Stage A also grows with N(p), so empirical alpha(p) '
        'can rise, reducing scaled speedup.',
    ])
    tag = emit_verify_tag('PHASE2',student_id,obs,gust)
    log(tag)
    md.extend([f'`{tag}`',''])
    return tag


# ---------- Phase 3 ----------
def copy_worker(args):
    aname,bname,lo,hi = args
    a = shared_memory.SharedMemory(name=aname)
    b = shared_memory.SharedMemory(name=bname)
    av=a.buf; bv=b.buf
    av[lo:hi] = bv[lo:hi]
    del av,bv
    a.close(); b.close()
    return hi-lo


def fp_worker(iterations):
    # 16 independently updated scalars, 2 floating-point operations per update.
    x0,x1,x2,x3 = 1.,1.01,1.02,1.03
    x4,x5,x6,x7 = 1.04,1.05,1.06,1.07
    x8,x9,x10,x11 = 1.08,1.09,1.10,1.11
    x12,x13,x14,x15 = 1.12,1.13,1.14,1.15
    a,b = 0.999999999, 0.000000001
    t0=time.perf_counter_ns()
    for _ in range(iterations):
        x0=x0*a+b; x1=x1*a+b; x2=x2*a+b; x3=x3*a+b
        x4=x4*a+b; x5=x5*a+b; x6=x6*a+b; x7=x7*a+b
        x8=x8*a+b; x9=x9*a+b; x10=x10*a+b; x11=x11*a+b
        x12=x12*a+b; x13=x13*a+b; x14=x14*a+b; x15=x15*a+b
    elapsed=(time.perf_counter_ns()-t0)/1e9
    checksum = (x0+x1+x2+x3+x4+x5+x6+x7+
                x8+x9+x10+x11+x12+x13+x14+x15)
    return elapsed,checksum


def gemm_worker(args):
    a_name,b_name,c_name,n,lo,hi,variant,bs=args
    sa=shared_memory.SharedMemory(name=a_name)
    sb=shared_memory.SharedMemory(name=b_name)
    sc=shared_memory.SharedMemory(name=c_name)
    A=sa.buf.cast('d'); B=sb.buf.cast('d'); C=sc.buf.cast('d')
    if variant=='naive':
        for i in range(lo,hi):
            irow=i*n
            for j in range(n):
                acc=0.0
                for k in range(n):
                    acc += A[irow+k]*B[k*n+j]
                C[irow+j]=acc
    elif variant=='reordered':
        for i in range(lo,hi):
            irow=i*n
            for k in range(n):
                aik=A[irow+k]
                brow=k*n
                for j in range(n):
                    C[irow+j] += aik*B[brow+j]
    elif variant=='blocked':
        for ii in range(lo,hi,bs):
            iend=min(ii+bs,hi)
            for jj in range(0,n,bs):
                jend=min(jj+bs,n)
                for kk in range(0,n,bs):
                    kend=min(kk+bs,n)
                    for i in range(ii,iend):
                        irow=i*n
                        for k in range(kk,kend):
                            aik=A[irow+k]
                            brow=k*n
                            for j in range(jj,jend):
                                C[irow+j] += aik*B[brow+j]
    else:
        raise ValueError(variant)
    del A,B,C
    sa.close(); sb.close(); sc.close()
    return (hi-lo)


def mem_alloc(size):
    return shared_memory.SharedMemory(create=True, size=size)


def fill_shm(shm, value, nbytes):
    """Fill exactly nbytes using bounded memory and explicit, equal-size slices.

    This avoids whole-buffer memoryview assignment mismatches seen on some
    macOS/Python SharedMemory versions and avoids a 96-MB temporary bytes object.
    """
    if nbytes > len(shm.buf):
        raise ValueError(f'Allocated buffer has {len(shm.buf)} B, expected {nbytes} B')
    blocksize = 1 << 20
    chunk = bytes([value]) * blocksize
    for start in range(0, nbytes, blocksize):
        stop = min(start + blocksize, nbytes)
        shm.buf[start:stop] = chunk[:stop - start]


def phase3(student_id, ctx, pphys, profile, hw, log, md, bwbytes=96_000_000):
    log('--- PHASE3: roofline & GEMM ---')
    warm,timed=(2,7) if profile=='full' else (1,3)
    a=mem_alloc(bwbytes); b=mem_alloc(bwbytes)
    try:
        # SharedMemory buffers are initially zero-initialized.
        # Fill only the source, with bounded and correctly sized slice writes.
        fill_shm(b, 0x55, bwbytes)
        partitions=[(a.name,b.name, t*bwbytes//pphys,(t+1)*bwbytes//pphys) for t in range(pphys)]
        with ctx.Pool(processes=pphys) as pool:
            bwstats=run_benchmark(lambda:pool.map(copy_worker,partitions,chunksize=1),warm,timed)
    finally:
        a.close();b.close();a.unlink();b.unlink()
    bw_s=bwstats.median_ms/1000
    bw_gb_s=(2*bwbytes)/(bw_s*1e9)
    log(f'PHASE3 bw_bytes_per_buffer={bwbytes} p={pphys} median_ms={bwstats.median_ms:.4f} iqr_ms={bwstats.iqr_ms:.4f} nominal_bw_GBps={bw_gb_s:.6f}')
    flops_per_worker = 80_000_000 if profile=='full' else 1_000_000
    iters=flops_per_worker//(16*2)
    with ctx.Pool(processes=pphys) as pool:
        for _ in range(warm):
            pool.map(fp_worker, [iters]*pphys, chunksize=1)
        fptimes=[]; fpsum=[]
        for _ in range(timed):
            completed = pool.map(fp_worker,[iters]*pphys,chunksize=1)
            fptimes.append(max(x[0] for x in completed))
            fpsum.append(sum(x[1] for x in completed))
    fpstats=summarize_ms([x*1000 for x in fptimes])
    totalflops=iters*16*2*pphys
    peak=totalflops/(fpstats.median_ms/1000)/1e9
    ridge=peak/bw_gb_s
    log(f'PHASE3 fp_iters_worker={iters} flops_total={totalflops} median_worker_ms={fpstats.median_ms:.4f} iqr_ms={fpstats.iqr_ms:.4f} checksum={fpsum[-1]:.12f} compute_GFLOPs={peak:.6f} ridge_FLOPs_per_byte={ridge:.6f}')
    md.extend(['## Phase 3. Empirical Roofline and GEMM optimization', '',
        '### 3A. Copy bandwidth and scalar arithmetic ceiling', '',
        table(['Metric','Observed'],[
            ['Copy source/destination buffers',f'2 × {bwbytes:,} bytes'],
            ['Median parallel memory-copy elapsed',f'{bwstats.median_ms:.3f} ms'],
            ['Nominal sustained copy bandwidth',f'{bw_gb_s:.6f} GB/s'],
            ['Scalar operations per worker',f'{flops_per_worker:,} (16 unrolled lanes)'],
            ['Median slowest-worker compute time',f'{fpstats.median_ms:.3f} ms'],
            ['Python multiply-add throughput',f'{peak:.6f} GFLOP/s'],
            ['Ridge point I*=P/BW',f'{ridge:.6f} FLOP/byte'],
        ]), '',
        'The Python `x*x+b` expression is **not guaranteed to compile to a true fused hardware FMA**. '
        'The copy measurement includes Python process-pool dispatch; these numbers are empirical '
        'application-level ceilings, not hardware peak FLOP/s or a direct DRAM-only counter reading. '
        f'The OS reports L3 = {hw["l3"]}. The 192-MB combined A/B footprint might '
        'not exceed a shared last-level/system cache on this machine. This benchmark '
        'does not isolate physical DRAM traffic; do not treat memcpy throughput '
        'as a hardware-counter measurement.', '',
        '### 3B. GEMM variants and the full 10-point tile sweep', ''])
    n=384 if profile=='full' else 64
    n2=n*n; size=n2*8
    sa=mem_alloc(size); sb=mem_alloc(size); sc=mem_alloc(size)
    records=[]; reference=None; max_errors={}
    try:
        av=sa.buf.cast('d'); bv=sb.buf.cast('d')
        for i in range(n):
            base=i*n
            for j in range(n):
                av[base+j]=((i*17+j*13)%101)/101.0-0.5
                bv[base+j]=((i*23+j*11)%97)/97.0-0.5
        del av,bv
        part=[(t*n//pphys, (t+1)*n//pphys) for t in range(pphys)]
        with ctx.Pool(processes=pphys) as pool:
            for variant,bs in [('naive',None),('reordered',None)]+[('blocked',z) for z in TILES]:
                jobs=[(sa.name,sb.name,sc.name,n,lo,hi,variant,bs) for lo,hi in part]
                def once():
                    fill_shm(sc, 0, size)
                    t0=time.perf_counter_ns()
                    pool.map(gemm_worker,jobs,chunksize=1)
                    t1=time.perf_counter_ns()
                    return (t1-t0)/1e6
                for _ in range(warm):
                    once()
                samples=[once() for _ in range(timed)]
                stats=summarize_ms(samples)
                gflops=2*n**3/(stats.median_ms*1e6)
                outview=sc.buf.cast('d')
                arrcopy=list(outview)
                del outview
                if variant=='reordered':
                    reference=arrcopy
                if reference is not None and variant=='blocked':
                    err=max(abs(x-y) for x,y in zip(reference,arrcopy))
                    max_errors[bs]=err
                records.append({'name':variant,'bs':bs,'ms':stats.median_ms,'iqr':stats.iqr_ms,'gflops':gflops})
                log(f'PHASE3 gemm_variant={variant} BS={bs} N={n} p={pphys} median_ms={stats.median_ms:.4f} iqr_ms={stats.iqr_ms:.4f} GFLOPs={gflops:.8f} max_abs_err_vs_v2={max_errors.get(bs,"n/a")}')
    finally:
        sa.close();sb.close();sc.close()
        sa.unlink();sb.unlink();sc.unlink()
    naive,reordered=records[:2]
    candidates=records[2:]
    best=max(candidates,key=lambda r:r['gflops'])
    all_pass = all(x<1e-9 for x in max_errors.values())
    gemm_rows=[]
    for r in records:
        bs=r['bs']
        w=(3*bs*bs*8) if bs is not None else 'n/a'
        nominal_intensity=(bs/12) if bs is not None else (0.125 if r['name']=='naive' else 'n/a')
        gemm_rows.append([r['name'],str(bs) if bs is not None else '—',q(r['ms'],3),q(r['iqr'],3),q(r['gflops'],5),w,q(nominal_intensity,4) if isinstance(nominal_intensity,float) else nominal_intensity])
    md.extend([f'GEMM dimension **N={n}**; all runs use p={pphys} processes and shared double buffers. '
       f'Each benchmark uses {warm} warm-up and {timed} timed trials. Throughput = `2N^3/(seconds*1e9)`.', '',
       table(['Variant','BS','Median (ms)','IQR (ms)','GFLOP/s','Tile working set (B)','Intensity (F/B)'],gemm_rows), '',
       f'Maximum absolute difference between each tiled result and reordered GEMM: '
       f'**{max(max_errors.values()):.3g}**; all ten pass `<1e-9`: **{all_pass}**.',
       f'Fastest measured tile: **BS*={best["bs"]}**, median {best["ms"]:.3f} ms, '
       f'{best["gflops"]:.6f} GFLOP/s; nominal Wtile = '
       f'{3*best["bs"]**2*8:,} bytes, nominal I = {best["bs"]/12:.4f} FLOP/byte.',
       f'The visible L1d and L2 sizes were {hw["l1d"]} and {hw["l2"]}. '
       'A tile fitting L1d avoids capacity misses, but loop overhead and interpreter dispatch '
       'may favor a larger tile. Effective tiled locality also depends on simultaneous tiles, '
       'partition edges and the interpreter; Wtile is a simplified capacity model.', '',
       '### 3C. Roofline mapping', ''])
    roof_rows=[]
    for name,r,intensity in [('Naive',naive,.125),('Reordered',reordered,.125),('Tiled BS*',best,min(best['bs'],n)/12)]:
        roof=min(peak,bw_gb_s*intensity)
        eff=100*r['gflops']/roof if roof else 0
        roof_rows.append([name,q(intensity,4),q(roof,6),q(r['gflops'],6),q(eff,2)+'%'])
    md.extend([table(['Variant','Modeled intensity (F/B)','P_roof (GFLOP/s)','Achieved (GFLOP/s)','Achieved / roof'],roof_rows), '',
       'The naive operational-intensity approximation is 0.125 FLOP/byte, and tile '
       'intensity BS/12. Reordered GEMM may reuse streamed B/C differently, '
       'so naive intensity is only a rough lower-bound proxy for this variant. '
       'Efficiencies above 100% imply the simplistic roofline/measurement pairing '
       'is not physically calibrated; do not interpret them as exceeding silicon limits.', ''])
    tag=emit_verify_tag('PHASE3',student_id,naive['gflops'],best['gflops'])
    log(tag);md.extend([f'`{tag}`',''])
    return tag


# ---------- Phase 4 ----------
def skew_item(i):
    k = 1 + (i*i)//3600
    x=(i%1000+1)/1001.0
    for j in range(k):
        x=0.5*(math.sin(x) + .01*math.cos(x) + math.sqrt(x*x+1))
    return x


def schedule_worker(t,p,n,strategy,chunk,counter,times,checks):
    start=time.perf_counter_ns()
    checksum=0.0
    if strategy=='block':
        for i in range(t*n//p, (t+1)*n//p):
            checksum+=skew_item(i)
    elif strategy=='cyclic':
        for i in range(t,n,p):
            checksum+=skew_item(i)
    elif strategy=='dynamic':
        while True:
            with counter.get_lock():
                lo=counter.value
                counter.value += chunk
            if lo>=n:
                break
            for i in range(lo,min(lo+chunk,n)):
                checksum+=skew_item(i)
    else:
        raise ValueError(strategy)
    times[t]=(time.perf_counter_ns()-start)/1e6
    checks[t]=checksum


def schedule_trial(ctx,p,n,strategy,chunk):
    counter=ctx.Value('i',0)
    times=ctx.Array('d',p)
    checks=ctx.Array('d',p)
    jobs=[ctx.Process(target=schedule_worker,args=(t,p,n,strategy,chunk,counter,times,checks)) for t in range(p)]
    t0=time.perf_counter_ns()
    for job in jobs:
        job.start()
    for job in jobs:
        job.join()
    wall=(time.perf_counter_ns()-t0)/1e6
    if any(job.exitcode!=0 for job in jobs):
        raise RuntimeError(f'scheduler worker failure {[x.exitcode for x in jobs]}')
    worker=list(times); checksum=sum(checks)
    imbalance=max(worker)/(sum(worker)/p) if sum(worker)>0 else float('nan')
    return wall,imbalance,checksum,worker


def phase4(student_id, ctx, pphys, profile, log, md):
    log('--- PHASE4: skewed scheduling ---')
    n=12000 if profile=='full' else 1200
    warm,timed=(2,7) if profile=='full' else (1,3)
    rows=[]; results={}
    for strategy,chunk in [('block',None),('cyclic',None)]+[('dynamic',c) for c in CHUNKS]:
        for _ in range(warm):
            schedule_trial(ctx,pphys,n,strategy,chunk)
        records=[schedule_trial(ctx,pphys,n,strategy,chunk) for _ in range(timed)]
        best_record=sorted(records,key=lambda r:r[0])[timed//2]
        walls=summarize_ms([r[0] for r in records])
        imbalances=summarize_ms([r[1] for r in records])
        key=(strategy,chunk)
        results[key]=(walls.median_ms,imbalances.median_ms)
        rows.append([strategy,str(chunk) if chunk is not None else '—',q(walls.median_ms,3),q(walls.iqr_ms,3),q(imbalances.median_ms,3)])
        log(f'PHASE4 strategy={strategy} C={chunk} p={pphys} N={n} wall_median_ms={walls.median_ms:.4f} wall_iqr_ms={walls.iqr_ms:.4f} lambda_median={imbalances.median_ms:.4f} checksum_median_run={best_record[2]:.9f} worker_times_median_run={[round(z,4) for z in best_record[3]]}')
    optimum=min(CHUNKS,key=lambda c: results[('dynamic',c)][0])
    static=results[('block',None)][0]
    best=results[('dynamic',optimum)][0]
    gain=static/best
    md.extend(['## Phase 4. Skewed workload and scheduling', '',
       f'Outer items N={n:,}, with `K(i)=1+floor((i/60)^2)` trig/sqrt iterations. '
       f'Processes p={pphys}, {warm} warm-ups / {timed} timed repetitions. '
       'Wall-clock includes process launch/join; each worker separately reports active time. '
       'The imbalance factor is `max(t_worker) / mean(t_worker)`.', '',
       table(['Strategy','Chunk C','Wall median (ms)','Wall IQR (ms)','Lambda median'],rows), '',
       f'**Fastest measured dynamic chunk**: C*={optimum}; wall {best:.3f} ms vs '
       f'{static:.3f} ms for contiguous blocks, speed ratio {gain:.3f}×. '
       'The optimum is workload-size- and machine-specific.',
       'Contiguous assignment puts later, more expensive indices on the last worker; '
       'round-robin distributes heavy indices. Dynamic scheduling responds to worker '
       'finish times at the cost of locked-counter transactions. C=1 minimizes end-of-run '
       'granularity but incurs the most lock/cache-line contention; C=1024 has few '
       'counter operations but can leave one worker a costly tail chunk.', '',
    ])
    tag=emit_verify_tag('PHASE4',student_id,static,best)
    log(tag);md.extend([f'`{tag}`',''])
    return tag


def build_report(md, tags, log, root, complete, *, error=None, include_source=True):
    """Build a complete or clearly marked partial report."""
    body = list(md)
    if not complete:
        body.extend(['', '## Execution status: INCOMPLETE', '',
                     '**Not a final submission.** This is a checkpoint containing only '
                     'successfully finished phases. Use START_RESUME_FULL.command '
                     'or `python3 parallel_lab.py --profile full --resume` if this was '
                     'a full run, after addressing the error.', ''])
        if error:
            body.extend(['**Last error:**', '', '```text', str(error), '```', ''])
    body.extend(['## Verification hashes', '', '```text', *tags, '```', '',
                 '## Raw console telemetry', '', '```text', *log.lines, '```', ''])
    if include_source:
        body.extend(['## Complete Python 3 implementation', '',
                     'The self-contained worker functions, timing, verification, '
                     'cache and process routines are included verbatim below.', ''])
        for filename in ['harness.py', 'parallel_lab.py']:
            source = (root / filename).read_text(encoding='utf-8')
            body.extend([f'### `{filename}`', '', '```python', source, '```', ''])
    return '\n'.join(body) + '\n'


def atomic_text(path, data):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(data, encoding='utf-8')
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser(description='Offline parallel-computing lab for ID 230103344')
    ap.add_argument('--id', type=int, default=230103344,
                    help='Student ID; preset for this package')
    ap.add_argument('--profile', choices=['pilot', 'full'], default='pilot')
    ap.add_argument('--out', default=None,
                    help='Optional output Markdown file (default: ID+profile-specific name)')
    ap.add_argument('--resume', action='store_true',
                    help='Continue a checkpointed run; only completed phases are skipped')
    ap.add_argument('--workers', type=int, default=None,
                    help='Diagnostics only: cap process count and scaling sweep')
    ap.add_argument('--bandwidth-mb', type=int, default=96,
                    help='MB per shared buffer; 96 MB required by lab')
    args = ap.parse_args()
    if args.id <= 0:
        ap.error('Student ID must be positive')
    if args.workers is not None and args.workers < 1:
        ap.error('--workers must be positive')
    if args.bandwidth_mb < 1:
        ap.error('--bandwidth-mb must be positive')
    root = Path(__file__).resolve().parent
    # Always write beside the downloaded script, even if Finder opens it from
    # an unexpected working directory. Never overwrite a full report with pilot.
    suffix = '' if args.profile == 'full' else '_PILOT'
    path = Path(args.out).expanduser().resolve() if args.out else root / f'lab_report_{args.id}{suffix}.md'
    log_path = root / f'run_{args.id}_{args.profile}.log'
    checkpoint = root / f'.checkpoint_{args.id}_{args.profile}.json'
    hw = hardware()
    physical = min(hw['physical'], args.workers) if args.workers else hw['physical']
    logical = min(hw['logical'], args.workers) if args.workers else hw['logical']
    machine_key = f'{platform.platform()} | {hw["cpu"]} | {hw["physical"]} | {hw["logical"]}'
    settings = dict(id=args.id, profile=args.profile, workers=args.workers,
                    bandwidth_mb=args.bandwidth_mb, machine=machine_key,
                    python=sys.version.split()[0])
    start = time.perf_counter()
    if args.resume:
        if not checkpoint.exists():
            ap.error(f'Checkpoint not found: {checkpoint}. Start without --resume first.')
        state = json.loads(checkpoint.read_text(encoding='utf-8'))
        if state['settings'] != settings:
            ap.error('Saved checkpoint belongs to a different ID, profile, Python, '
                     'hardware, or options. Run with exactly the original settings.')
        md = state['markdown']
        tags = state['tags']
        completed = set(state['completed'])
        log = Printer(log_path, prior_lines=state['logs'])
        log(f'LAB RESUME checkpoint={checkpoint.name} completed={sorted(completed)}')
    else:
        if checkpoint.exists():
            # Preserve previous work rather than silently overwriting it.
            ap.error(f'A prior run checkpoint exists: {checkpoint.name}. '
                     'Use --resume to continue, or manually rename/delete that '
                     'checkpoint if you intentionally want to start over.')
        md = [
            '# Performance Evaluation and Optimization in Parallel Computing', '',
            f'**Student ID:** {args.id}  ',
            f'**Execution profile:** {args.profile.upper()}  ',
            f'**Date (UTC):** {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}  ',
            f'**Measured machine:** {platform.platform()}; CPU: {hw["cpu"]}  ',
            '', '## Provenance and assignment protocol', '',
            'All measurements in this report were obtained on the computer that '
            'executed this script, not inferred from another laptop. The code '
            'and explanatory notes were AI-assisted; the assignment itself '
            'requires independent offline work without AI and at least 120 minutes. '
            'Running the program does not in itself establish compliance with '
            'those academic requirements.', '',
            ('**PILOT / DIAGNOSTIC ONLY:** This quick run uses smaller kernels '
             'and fewer repeats and is not the full required experiment. '
             'The pilot report has `_PILOT` in its filename to prevent accidental '
             'submission.' if args.profile == 'pilot' else
             '**FULL WORKLOAD PROFILE:** Prescribed kernel sizes and 2+7 '
             'benchmark repetitions are used. This does not independently '
             'verify 120 minutes of individual work.'), '',
            'Required settings from the source PDF: Phase 1 M=24,000,000; '
            'Phase 2 strong N=1,600,000 and weak N0=250,000; Phase 3 '
            'two 96-MB copy buffers, 80,000,000 operations per worker, '
            'GEMM N=384; Phase 4 N=12,000. '
            'All ten block sizes and all six dynamic chunks are tested.', ''
        ]
        tags = []
        completed = set()
        log = Printer(log_path)
        log(f'LAB student_id={args.id} profile={args.profile} '
            f'date_utc={datetime.datetime.now(datetime.timezone.utc).isoformat()}')
        log(f'LAB execution_platform={platform.platform()} cpu={hw["cpu"]} '
            f'visible_cpus={hw["logical"]}')
        log(f'LAB test_workers={physical} scaling_max={logical} '
            f'bandwidth_bytes_per_buffer={args.bandwidth_mb*1_000_000}')
        if args.workers is not None or args.bandwidth_mb != 96:
            md.extend(['**DIAGNOSTIC OVERRIDES:** --workers and/or --bandwidth-mb '
                       'deviates from assigned values. Not an acceptable full run.', ''])

    def save_checkpoint():
        state = {'settings': settings, 'markdown': md, 'tags': tags,
                 'logs': log.lines, 'completed': sorted(completed)}
        log(f'LAB checkpoint_saved phases={sorted(completed)} path={path.name}')
        state['logs'] = log.lines
        atomic_text(checkpoint, json.dumps(state, ensure_ascii=False, indent=2))
        atomic_text(path, build_report(md, tags, log, root, complete=False))

    steps = [
        (0, lambda: phase0(args.id, log, md)),
        (1, lambda: phase1(args.id, ctx, physical, logical, args.profile, log, md)),
        (2, lambda: phase2(args.id, ctx, physical, logical, args.profile, log, md, hw)),
        (3, lambda: phase3(args.id, ctx, physical, args.profile, hw, log, md,
                          args.bandwidth_mb*1_000_000)),
        (4, lambda: phase4(args.id, ctx, physical, args.profile, log, md)),
    ]
    ctx = mp.get_context('spawn' if sys.platform in ('darwin', 'win32') else 'fork')
    # On macOS this deliberately uses spawn: all target functions are top-level.
    try:
        for idx, run_phase in steps:
            if idx in completed:
                continue
            log(f'LAB START phase={idx}')
            outcome = run_phase()
            if idx == 0:
                measured_hw, tag = outcome
                # Verify that cached hardware and phase measurements agree.
                if measured_hw['physical'] != hw['physical'] or measured_hw['logical'] != hw['logical']:
                    log('LAB WARNING: OS-reported CPU count changed during initialization')
            else:
                tag = outcome
            tags.append(tag)
            completed.add(idx)
            save_checkpoint()
    except KeyboardInterrupt:
        log('LAB INTERRUPTED by user. Checkpoint and raw log preserved.')
        atomic_text(path, build_report(md, tags, log, root, complete=False,
                                       error='KeyboardInterrupt'))
        return 130
    except BaseException as exc:
        message = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        log('LAB ERROR: ' + message)
        atomic_text(path, build_report(md, tags, log, root, complete=False, error=message))
        return 1
    elapsed = time.perf_counter() - start
    log(f'LAB elapsed_seconds={elapsed:.3f}')
    log(f'LAB finished_phases={sorted(completed)}')
    atomic_text(path, build_report(md, tags, log, root, complete=True))
    # The finished report is independent of this checkpoint; remove it to
    # make later fresh reruns possible without manual cleanup.
    checkpoint.unlink(missing_ok=True)
    log(f'WROTE {path.resolve()} ({path.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    mp.freeze_support()
    sys.exit(main())
