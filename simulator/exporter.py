from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


ECU_FIELDS = [
    "campaign_id",
    "ecu_id",
    "name",
    "domain",
    "source_type",
    "current_version",
    "target_version",
    "active_partition",
    "ota_status",
    "health_status",
    "connected",
    "progress_pct",
    "elapsed_s",
    "rollback_trigger",
    "rollback_counter",
    "consecutive_rollback_counter",
    "rollback_lockout",
    "recovery_boot_counter",
    "dependencies",
]

WAVE_FIELDS = [
    "campaign_id",
    "wave_number",
    "ecu_count",
    "ecu_ids",
    "elapsed_s",
]

EVENT_FIELDS = [
    "event_id",
    "timestamp",
    "campaign_id",
    "ecu_id",
    "source_type",
    "level",
    "event_code",
    "ota_status",
    "progress_pct",
    "message",
    "rollback_trigger",
]


def _percentage(
    value: int | float,
    total: int | float,
) -> float:
    """Calcule un pourcentage sécurisé."""

    if total == 0:
        return 0.0

    return round(
        float(value) / float(total) * 100,
        2,
    )


def build_campaign_kpis(
    summary: dict[str, Any],
) -> dict[str, Any]:
    """Construit les KPI fonctionnels et temporels."""

    total_ecus = int(summary["total_ecus"])
    confirmed_ecus = int(
        summary["confirmed_ecus"]
    )
    rejected_ecus = int(
        summary["rejected_ecus"]
    )
    rolled_back_ecus = int(
        summary["rolled_back_ecus"]
    )
    blocked_ecus = int(
        summary["blocked_ecus"]
    )
    locked_out_ecus = int(
        summary["locked_out_ecus"]
    )
    recovery_ecus = int(
        summary["recovery_ecus"]
    )
    offline_ecus = int(
        summary.get("offline_ecus", 0)
    )

    terminal_ecus = (
        confirmed_ecus
        + rejected_ecus
        + rolled_back_ecus
        + blocked_ecus
        + locked_out_ecus
        + recovery_ecus
        + offline_ecus
    )

    if terminal_ecus != total_ecus:
        raise ValueError(
            "Compteurs ECU incohérents : "
            f"{terminal_ecus}/{total_ecus}"
        )

    failed_ecus = (
        total_ecus - confirmed_ecus
    )

    timing = summary["timing"]
    elapsed_s = float(summary["elapsed_s"])
    time_budget_s = float(
        summary["time_budget_s"]
    )

    return {
        "schema_version": "1.0",
        "campaign_id": summary["campaign_id"],
        "source_mode": summary["source_mode"],
        "campaign_status": summary["status"],
        "total_ecus": total_ecus,
        "terminal_ecus": terminal_ecus,
        "confirmed_ecus": confirmed_ecus,
        "failed_ecus": failed_ecus,
        "rejected_ecus": rejected_ecus,
        "rolled_back_ecus": (
            rolled_back_ecus
        ),
        "blocked_ecus": blocked_ecus,
        "locked_out_ecus": (
            locked_out_ecus
        ),
        "recovery_ecus": recovery_ecus,
        "offline_ecus": offline_ecus,
        "confirmation_rate_pct": (
            _percentage(
                confirmed_ecus,
                total_ecus,
            )
        ),
        "failure_rate_pct": _percentage(
            failed_ecus,
            total_ecus,
        ),
        "rejection_rate_pct": _percentage(
            rejected_ecus,
            total_ecus,
        ),
        "rollback_rate_pct": _percentage(
            rolled_back_ecus,
            total_ecus,
        ),
        "blocked_rate_pct": _percentage(
            blocked_ecus,
            total_ecus,
        ),
        "lockout_rate_pct": _percentage(
            locked_out_ecus,
            total_ecus,
        ),
        "recovery_rate_pct": _percentage(
            recovery_ecus,
            total_ecus,
        ),
        "elapsed_s": elapsed_s,
        "time_budget_s": time_budget_s,
        "budget_status": (
            timing["budget_status"]
        ),
        "budget_utilization_pct": (
            _percentage(
                elapsed_s,
                time_budget_s,
            )
        ),
        "budget_margin_s": (
            timing["budget_margin_s"]
        ),
        "budget_overrun_s": (
            timing["budget_overrun_s"]
        ),
        "fleet_processing_s": (
            timing["fleet_processing_s"]
        ),
        "average_ecu_duration_s": (
            timing[
                "average_ecu_duration_s"
            ]
        ),
        "max_ecu_duration_s": (
            timing["max_ecu_duration_s"]
        ),
        "min_ecu_duration_s": (
            timing["min_ecu_duration_s"]
        ),
        "total_waves": len(
            summary["executed_waves"]
        ),
        "event_count": len(
            summary["events"]
        ),
    }


def _write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def export_campaign_data(
    summary: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Exporte une campagne en JSON et CSV."""

    destination = Path(output_dir)

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {
        "summary": (
            destination
            / "campaign-summary.json"
        ),
        "kpis": (
            destination
            / "campaign-kpis.json"
        ),
        "ecus": (
            destination
            / "ecu-results.csv"
        ),
        "waves": (
            destination
            / "wave-timing.csv"
        ),
        "events": (
            destination
            / "events.csv"
        ),
    }

    kpis = build_campaign_kpis(summary)

    _write_json(
        paths["summary"],
        summary,
    )
    _write_json(
        paths["kpis"],
        kpis,
    )

    ecu_rows = []

    for ecu in sorted(
        summary["ecus"],
        key=lambda state: state["ecu_id"],
    ):
        ecu_rows.append(
            {
                "campaign_id": (
                    summary["campaign_id"]
                ),
                "ecu_id": ecu["ecu_id"],
                "name": ecu["name"],
                "domain": ecu["domain"],
                "source_type": (
                    ecu["source_type"]
                ),
                "current_version": (
                    ecu["current_version"]
                ),
                "target_version": (
                    ecu["target_version"]
                ),
                "active_partition": (
                    ecu["active_partition"]
                ),
                "ota_status": (
                    ecu["ota_status"]
                ),
                "health_status": (
                    ecu["health_status"]
                ),
                "connected": ecu["connected"],
                "progress_pct": (
                    ecu["progress_pct"]
                ),
                "elapsed_s": (
                    ecu["elapsed_s"]
                ),
                "rollback_trigger": (
                    ecu["rollback_trigger"]
                ),
                "rollback_counter": (
                    ecu["rollback_counter"]
                ),
                "consecutive_rollback_counter": (
                    ecu[
                        "consecutive_rollback_counter"
                    ]
                ),
                "rollback_lockout": (
                    ecu["rollback_lockout"]
                ),
                "recovery_boot_counter": (
                    ecu[
                        "recovery_boot_counter"
                    ]
                ),
                "dependencies": "|".join(
                    ecu["dependencies"]
                ),
            }
        )

    _write_csv(
        paths["ecus"],
        ECU_FIELDS,
        ecu_rows,
    )

    wave_rows = []

    for wave in summary["timing"][
        "wave_durations"
    ]:
        wave_rows.append(
            {
                "campaign_id": (
                    summary["campaign_id"]
                ),
                "wave_number": (
                    wave["wave_number"]
                ),
                "ecu_count": len(
                    wave["ecu_ids"]
                ),
                "ecu_ids": "|".join(
                    wave["ecu_ids"]
                ),
                "elapsed_s": (
                    wave["elapsed_s"]
                ),
            }
        )

    _write_csv(
        paths["waves"],
        WAVE_FIELDS,
        wave_rows,
    )

    event_rows = [
        {
            field: event.get(field)
            for field in EVENT_FIELDS
        }
        for event in summary["events"]
    ]

    _write_csv(
        paths["events"],
        EVENT_FIELDS,
        event_rows,
    )

    return paths
