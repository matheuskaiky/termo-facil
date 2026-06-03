#!/usr/bin/env python3
"""
Termo Fácil — Monitor de recursos (VRAM + RAM) para o HPC.

Imprime UM snapshot do consumo de memória de vídeo (por GPU, com suporte a
múltiplas GPUs) e da memória RAM do sistema, depois sai. Feito para ser
reexecutado em loop pelo `watch`:

    watch -n 1 python3 hpc/monitor.py        # atualiza a cada 1s
    watch -n 0.5 -c python3 hpc/monitor.py   # com cores (watch -c)

Sem dependências externas: a VRAM é lida via `nvidia-smi` e a RAM via
`/proc/meminfo`. `psutil`/`pynvml`, se instalados, NÃO são necessários — o
script funciona em qualquer nó do cluster apenas com o driver NVIDIA presente.

Saída/uso:
    python3 hpc/monitor.py            # snapshot legível (MiB / GiB)
    python3 hpc/monitor.py --gib      # força unidade GiB nas GPUs
    python3 hpc/monitor.py --no-color # desliga cores mesmo em TTY
    python3 hpc/monitor.py --color    # liga cores mesmo sem TTY (use watch -c)
    python3 hpc/monitor.py --json     # uma linha JSON (para logs/coleta)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys


# ─────────────────────────── cores (opcional) ────────────────────────────────
class _C:
    enabled = False

    @classmethod
    def wrap(cls, code: str, text: str) -> str:
        if not cls.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"


def bold(t: str) -> str:
    return _C.wrap("1", t)


def dim(t: str) -> str:
    return _C.wrap("2", t)


def color_pct(pct: float, text: str) -> str:
    """Verde < 60%, amarelo 60–85%, vermelho > 85% (espelha o design system)."""
    if pct >= 85:
        return _C.wrap("31", text)   # vermelho
    if pct >= 60:
        return _C.wrap("33", text)   # amarelo
    return _C.wrap("32", text)       # verde


# ───────────────────────────── coleta de GPU ─────────────────────────────────
_GPU_FIELDS = [
    "index",
    "name",
    "memory.used",
    "memory.total",
    "utilization.gpu",
    "temperature.gpu",
]


def read_gpus() -> tuple[list[dict], str | None]:
    """
    Lê a VRAM por GPU, em MiB. Tenta o `nvidia-smi` primeiro (mais rico:
    inclui util% e temperatura) e, se ele falhar (NVML/driver-smi quebrados),
    cai para o **PyTorch CUDA** — que mede VRAM via cudaMemGetInfo, sem NVML.

    Retorna (lista_de_gpus, erro). Cada GPU traz a chave `source`
    ("nvidia-smi" ou "torch"); no caminho torch, util%/temp ficam None.
    """
    gpus, smi_err = _read_gpus_nvidia_smi()
    if gpus:
        for g in gpus:
            g["source"] = "nvidia-smi"
        return gpus, None

    tg, torch_err = _read_gpus_torch()
    if tg:
        return tg, None

    parts = []
    if smi_err:
        parts.append(f"nvidia-smi: {smi_err}")
    if torch_err:
        parts.append(f"torch: {torch_err}")
    return [], " | ".join(parts) if parts else "nenhuma fonte de GPU disponível"


def _read_gpus_nvidia_smi() -> tuple[list[dict], str | None]:
    """Leitura via nvidia-smi (CSV). Vazio + erro se NVML/smi indisponível."""
    if shutil.which("nvidia-smi") is None:
        return [], "nvidia-smi não encontrado (driver NVIDIA ausente?)"

    query = "--query-gpu=" + ",".join(_GPU_FIELDS)
    try:
        out = subprocess.run(
            ["nvidia-smi", query, "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return [], f"falha ao executar nvidia-smi: {exc}"

    if out.returncode != 0:
        msg = (out.stderr or out.stdout or "").strip().splitlines()
        return [], (msg[0] if msg else f"nvidia-smi retornou {out.returncode}")

    gpus: list[dict] = []
    for line in out.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(_GPU_FIELDS):
            continue

        def _num(v: str) -> float | None:
            try:
                return float(v)
            except ValueError:
                return None  # ex.: "[N/A]" em algumas GPUs/MIG

        used = _num(parts[2])
        total = _num(parts[3])
        gpus.append(
            {
                "index": parts[0],
                "name": parts[1],
                "mem_used_mib": used,
                "mem_total_mib": total,
                "mem_pct": (used / total * 100.0) if used and total else None,
                "util_pct": _num(parts[4]),
                "temp_c": _num(parts[5]),
            }
        )
    return gpus, None


def _read_gpus_torch() -> tuple[list[dict], str | None]:
    """
    Fallback via PyTorch para nós com CUDA funcional mas NVML/nvidia-smi
    quebrados. `torch.cuda.mem_get_info` usa cudaMemGetInfo (runtime CUDA),
    então reporta o uso REAL do device (todos os processos) sem depender do
    NVML. util%/temperatura não são expostos por essa via → ficam None.
    """
    import warnings

    try:
        import torch  # import tardio: só paga o custo quando o smi falha
    except Exception as exc:
        return [], f"PyTorch não importável ({exc})"

    # Com NVML quebrado, o torch emite "Can't initialize NVML"; a contagem/uso
    # de devices ainda funcionam via runtime CUDA, então silenciamos o ruído.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            if not torch.cuda.is_available():
                return [], "torch.cuda.is_available() == False"
            count = torch.cuda.device_count()
        except Exception as exc:
            return [], f"falha ao inicializar CUDA ({exc})"

        gpus: list[dict] = []
        for i in range(count):
            try:
                free_b, total_b = torch.cuda.mem_get_info(i)  # bytes (free, total)
                name = torch.cuda.get_device_name(i)
            except Exception as exc:
                gpus.append(
                    {
                        "index": str(i),
                        "name": f"(erro: {exc})",
                        "mem_used_mib": None,
                        "mem_total_mib": None,
                        "mem_pct": None,
                        "util_pct": None,
                        "temp_c": None,
                        "source": "torch",
                    }
                )
                continue
            used_b = total_b - free_b
            gpus.append(
                {
                    "index": str(i),
                    "name": name,
                    "mem_used_mib": used_b / (1024 * 1024),
                    "mem_total_mib": total_b / (1024 * 1024),
                    "mem_pct": (used_b / total_b * 100.0) if total_b else None,
                    "util_pct": None,   # NVML indisponível nesta via
                    "temp_c": None,
                    "source": "torch",
                }
            )

    return gpus, None


# ───────────────────────────── coleta de RAM ─────────────────────────────────
def read_ram() -> tuple[dict | None, str | None]:
    """RAM do sistema via /proc/meminfo (Linux). Valores em MiB."""
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            info = {}
            for line in fh:
                key, _, rest = line.partition(":")
                kb = rest.strip().split()
                if kb:
                    try:
                        info[key] = int(kb[0])  # valor em kB
                    except ValueError:
                        pass
    except OSError as exc:
        return None, f"/proc/meminfo indisponível: {exc}"

    total_kb = info.get("MemTotal")
    # MemAvailable é a melhor estimativa de "livre real" (kernel >= 3.14).
    avail_kb = info.get("MemAvailable")
    if avail_kb is None:  # fallback grosseiro para kernels antigos
        avail_kb = (
            info.get("MemFree", 0)
            + info.get("Buffers", 0)
            + info.get("Cached", 0)
        )
    if not total_kb:
        return None, "MemTotal ausente em /proc/meminfo"

    used_kb = total_kb - avail_kb
    return (
        {
            "total_mib": total_kb / 1024.0,
            "used_mib": used_kb / 1024.0,
            "avail_mib": avail_kb / 1024.0,
            "pct": used_kb / total_kb * 100.0,
        },
        None,
    )


# ─────────────────────────────── formatação ──────────────────────────────────
def fmt_mem(mib: float | None, gib: bool) -> str:
    if mib is None:
        return "   N/A"
    if gib:
        return f"{mib / 1024.0:7.2f} GiB"
    return f"{mib:8.0f} MiB"


# Sentinela para linhas separadoras dentro do conteúdo.
_SEP = object()


def _content(gpus: list[dict], gpu_err: str | None,
             ram: dict | None, ram_err: str | None, gib: bool) -> list:
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list = [
        bold("Termo Fácil — Monitor de Recursos (VRAM + RAM)"),
        dim(now),
        _SEP,
    ]

    # ── GPUs ──
    if gpu_err:
        rows.append("GPU: " + gpu_err)
    elif not gpus:
        rows.append("GPU: nenhuma GPU detectada")
    else:
        agg_used = sum(g["mem_used_mib"] or 0 for g in gpus)
        agg_total = sum(g["mem_total_mib"] or 0 for g in gpus)
        for g in gpus:
            pct = g["mem_pct"]
            pct_txt = f"{pct:5.1f}%" if pct is not None else "  N/A"
            mem = f"{fmt_mem(g['mem_used_mib'], gib)} / {fmt_mem(g['mem_total_mib'], gib)}"
            util = f"{g['util_pct']:3.0f}%" if g["util_pct"] is not None else "N/A"
            temp = f"{g['temp_c']:3.0f}C" if g["temp_c"] is not None else " N/A"
            head = f"GPU {g['index']} {_clip(g['name'], 22):22}"
            body = f"{mem}  [{_bar(pct, 18)}] {color_pct(pct or 0, pct_txt)}  util {util}  {temp}"
            rows.append(f"{head} {body}")

        if len(gpus) > 1 and agg_total:
            apct = agg_used / agg_total * 100.0
            apct_txt = color_pct(apct, f"{apct:5.1f}%")
            mem = f"{fmt_mem(agg_used, gib)} / {fmt_mem(agg_total, gib)}"
            rows.append(f"TOTAL ({len(gpus)} GPUs){' ' * 9}{mem}  [{_bar(apct, 18)}] {apct_txt}")

        if any(g.get("source") == "torch" for g in gpus):
            rows.append(dim("VRAM via PyTorch CUDA (NVML/nvidia-smi off) — util%/temp indisponíveis"))

    rows.append(_SEP)

    # ── RAM ──
    if ram_err:
        rows.append("RAM: " + ram_err)
    elif ram:
        pct_txt = color_pct(ram["pct"], f"{ram['pct']:5.1f}%")
        mem = f"{fmt_mem(ram['used_mib'], gib)} / {fmt_mem(ram['total_mib'], gib)}"
        free = fmt_mem(ram["avail_mib"], gib)
        rows.append(f"RAM{' ' * 19}{mem}  [{_bar(ram['pct'], 18)}] {pct_txt}  livre {free}")

    return rows


def render(gpus: list[dict], gpu_err: str | None,
           ram: dict | None, ram_err: str | None, gib: bool) -> str:
    rows = _content(gpus, gpu_err, ram, ram_err, gib)
    inner = max((_visible_len(r) for r in rows if r is not _SEP), default=0)
    width = max(46, inner + 2)  # +2 = um espaço de margem de cada lado

    out = ["╔" + "═" * width + "╗"]
    for r in rows:
        if r is _SEP:
            out.append("╠" + "═" * width + "╣")
        else:
            out.append("║ " + _pad(r, width - 1) + "║")
    out.append("╚" + "═" * width + "╝")
    return "\n".join(out)


def _bar(pct: float | None, n: int) -> str:
    if pct is None:
        return " " * n
    filled = max(0, min(n, round(pct / 100.0 * n)))
    return "█" * filled + "░" * (n - filled)


def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _visible_len(s: str) -> int:
    """Comprimento ignorando códigos ANSI (para alinhar a borda da box)."""
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\033":
            j = s.find("m", i)
            if j != -1:
                i = j + 1
                continue
        out += 1
        i += 1
    return out


def _pad(s: str, width: int) -> str:
    pad = width - _visible_len(s)
    return s + " " * max(0, pad)


# ──────────────────────────────────── main ───────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Monitor de VRAM (multi-GPU) e RAM para o HPC. Use com watch -n.",
    )
    ap.add_argument("--gib", action="store_true", help="exibe memória em GiB (padrão: MiB)")
    ap.add_argument("--json", action="store_true", help="saída em uma linha JSON")
    ap.add_argument("--color", action="store_true", help="força cores (use com watch -c)")
    ap.add_argument("--no-color", action="store_true", help="desliga cores")
    args = ap.parse_args(argv)

    gpus, gpu_err = read_gpus()
    ram, ram_err = read_ram()

    if args.json:
        print(json.dumps(
            {
                "ts": _dt.datetime.now().isoformat(timespec="seconds"),
                "gpus": gpus,
                "gpu_error": gpu_err,
                "ram": ram,
                "ram_error": ram_err,
            },
            ensure_ascii=False,
        ))
        return 0

    if args.color:
        _C.enabled = True
    elif args.no_color:
        _C.enabled = False
    else:
        _C.enabled = sys.stdout.isatty()

    print(render(gpus, gpu_err, ram, ram_err, args.gib))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
