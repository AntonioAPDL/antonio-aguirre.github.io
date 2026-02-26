from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from .config import PipelineConfig
from .herbie_adapter import inventory_frame, make_herbie


CYCLE_HOURS: Tuple[int, ...] = (0, 6, 12, 18)


@dataclass(frozen=True)
class CycleSelection:
    init_time_utc: dt.datetime
    details: Dict[str, Any]


def cycle_tag(init_time_utc: dt.datetime) -> str:
    return init_time_utc.strftime("%Y%m%d_%H")


def floor_to_cycle(now_utc: dt.datetime) -> dt.datetime:
    now_utc = now_utc.astimezone(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    cycle_hour = max((h for h in CYCLE_HOURS if h <= now_utc.hour), default=None)
    if cycle_hour is None:
        prev_day = now_utc - dt.timedelta(days=1)
        return prev_day.replace(hour=18)
    return now_utc.replace(hour=cycle_hour)


def build_candidate_cycles(now_utc: dt.datetime, lookback_hours: int) -> List[dt.datetime]:
    latest = floor_to_cycle(now_utc)
    count = max(1, int(lookback_hours // 6) + 1)
    return [latest - dt.timedelta(hours=6 * i) for i in range(count)]


def _member_has_inventory(
    init_time_utc: dt.datetime,
    model: str,
    product: str,
    member: str,
    fxx: int,
    source_priority: Sequence[str],
    attempts: int = 3,
) -> bool:
    import time

    for idx in range(attempts):
        try:
            handle = make_herbie(
                init_time_utc=init_time_utc,
                model=model,
                product=product,
                member=member,
                fxx=fxx,
                source_priority=list(source_priority),
            )
            inv = inventory_frame(handle)
            return not inv.empty
        except Exception:
            if idx >= attempts - 1:
                return False
            time.sleep(0.6 * (2 ** idx))
    return False


def discover_latest_complete_cycle(
    cfg: PipelineConfig,
    now_utc: dt.datetime,
) -> CycleSelection:
    candidates = build_candidate_cycles(now_utc, cfg.runtime.candidate_lookback_hours)
    sentinel_product = cfg.products_try[0]
    sentinel_member = "c00" if "c00" in cfg.members else cfg.members[0]
    end_lead = cfg.leads.end
    probe_lead = cfg.runtime.completeness_probe_fxx

    candidate_notes: List[Dict[str, Any]] = []

    for candidate in candidates:
        f0_ok = _member_has_inventory(
            candidate, cfg.model, sentinel_product, sentinel_member, 0, cfg.source_priority
        )
        fend_ok = _member_has_inventory(
            candidate,
            cfg.model,
            sentinel_product,
            sentinel_member,
            end_lead,
            cfg.source_priority,
        )
        if not (f0_ok and fend_ok):
            candidate_notes.append(
                {
                    "init_time_utc": candidate.isoformat(),
                    "status": "rejected",
                    "reason": f"sentinel_missing_f0_or_f{end_lead}",
                    "sentinel_product": sentinel_product,
                    "sentinel_member": sentinel_member,
                    "f0_ok": f0_ok,
                    "fend_ok": fend_ok,
                }
            )
            continue

        available_members: List[str] = []
        with ThreadPoolExecutor(max_workers=max(1, min(cfg.runtime.max_workers, len(cfg.members)))) as pool:
            futures = {
                pool.submit(
                    _member_has_inventory,
                    candidate,
                    cfg.model,
                    sentinel_product,
                    member,
                    probe_lead,
                    cfg.source_priority,
                ): member
                for member in cfg.members
            }
            for future in as_completed(futures):
                member = futures[future]
                try:
                    if future.result():
                        available_members.append(member)
                except Exception:
                    pass

        available_members.sort()
        count = len(available_members)
        if count < cfg.runtime.require_member_count:
            candidate_notes.append(
                {
                    "init_time_utc": candidate.isoformat(),
                    "status": "rejected",
                    "reason": "incomplete_members",
                    "required_members": cfg.runtime.require_member_count,
                    "available_members_count": count,
                    "probe_fxx": probe_lead,
                }
            )
            continue

        candidate_notes.append(
            {
                "init_time_utc": candidate.isoformat(),
                "status": "selected",
                "sentinel_product": sentinel_product,
                "sentinel_member": sentinel_member,
                "probe_fxx": probe_lead,
                "available_members_count": count,
            }
        )
        return CycleSelection(
            init_time_utc=candidate,
            details={
                "candidates_checked": candidate_notes,
            },
        )

    raise RuntimeError(
        "No complete GEFS cycle found in lookback window. Candidate results: "
        + str(candidate_notes)
    )
