from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_TIMING_MODEL_PATH = (
    PROJECT_ROOT
    / "config"
    / "timing-model.json"
)


def load_timing_model(
    path: Path | None = None,
) -> dict[str, Any]:
    """Charge et valide le modèle temporel."""

    model_path = (
        path
        if path is not None
        else DEFAULT_TIMING_MODEL_PATH
    )

    with model_path.open(
        encoding="utf-8"
    ) as file:
        model = json.load(file)

    required_fields = {
        "schema_version",
        "model_id",
        "source_type",
        "execution_policy",
        "nominal_time_budget_s",
        "state_durations_s",
    }

    missing_fields = (
        required_fields - set(model)
    )

    if missing_fields:
        raise ValueError(
            "Champs temporels manquants : "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    durations = model["state_durations_s"]

    if not isinstance(durations, dict):
        raise ValueError(
            "state_durations_s doit être "
            "un objet JSON"
        )

    for state, duration in durations.items():
        if not isinstance(state, str) or not state:
            raise ValueError(
                "Nom d'état temporel invalide"
            )

        if (
            isinstance(duration, bool)
            or not isinstance(
                duration,
                (int, float),
            )
            or duration < 0
        ):
            raise ValueError(
                "Durée invalide pour "
                f"{state}: {duration}"
            )

    budget = model["nominal_time_budget_s"]

    if (
        isinstance(budget, bool)
        or not isinstance(
            budget,
            (int, float),
        )
        or budget <= 0
    ):
        raise ValueError(
            "Budget temporel invalide"
        )

    return model


def calculate_state_history_duration(
    state_history: Iterable[str],
    state_durations: Mapping[
        str,
        int | float,
    ],
) -> float:
    """Calcule la durée d'un historique ECU."""

    total = 0.0

    for state in state_history:
        if state not in state_durations:
            raise ValueError(
                "État absent du modèle temporel : "
                f"{state}"
            )

        total += float(
            state_durations[state]
        )

    return total


def calculate_wave_durations(
    executed_waves: Iterable[Iterable[str]],
    ecu_durations_s: Mapping[
        str,
        int | float,
    ],
) -> list[dict[str, Any]]:
    """
    Calcule la durée de chaque vague.

    Les ECU d'une même vague sont considérés
    comme exécutés en parallèle.
    """

    wave_results = []

    for wave_number, wave in enumerate(
        executed_waves,
        start=1,
    ):
        ecu_ids = list(wave)

        missing_ecus = [
            ecu_id
            for ecu_id in ecu_ids
            if ecu_id not in ecu_durations_s
        ]

        if missing_ecus:
            raise ValueError(
                "Durée absente pour : "
                + ", ".join(missing_ecus)
            )

        elapsed_s = max(
            (
                float(
                    ecu_durations_s[ecu_id]
                )
                for ecu_id in ecu_ids
            ),
            default=0.0,
        )

        wave_results.append(
            {
                "wave_number": wave_number,
                "ecu_ids": ecu_ids,
                "elapsed_s": elapsed_s,
            }
        )

    return wave_results


def build_timing_summary(
    ecus: Mapping[str, Any],
    executed_waves: Iterable[
        Iterable[str]
    ],
    model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construit les KPI temporels de campagne."""

    timing_model = (
        model
        if model is not None
        else load_timing_model()
    )

    state_durations = timing_model[
        "state_durations_s"
    ]

    waves = [
        list(wave)
        for wave in executed_waves
    ]

    targeted_ids = [
        ecu_id
        for wave in waves
        for ecu_id in wave
    ]

    if len(targeted_ids) != len(
        set(targeted_ids)
    ):
        raise ValueError(
            "Un ECU apparaît dans plusieurs vagues"
        )

    missing_ecus = [
        ecu_id
        for ecu_id in targeted_ids
        if ecu_id not in ecus
    ]

    if missing_ecus:
        raise ValueError(
            "ECU absent du parc : "
            + ", ".join(missing_ecus)
        )

    ecu_durations_s = {}

    for ecu_id in targeted_ids:
        ecu = ecus[ecu_id]

        ecu_durations_s[ecu_id] = (
            calculate_state_history_duration(
                ecu.state_history,
                state_durations,
            )
        )

    wave_durations = (
        calculate_wave_durations(
            waves,
            ecu_durations_s,
        )
    )

    elapsed_s = sum(
        wave["elapsed_s"]
        for wave in wave_durations
    )

    fleet_processing_s = sum(
        ecu_durations_s.values()
    )

    ecu_count = len(ecu_durations_s)

    average_ecu_duration_s = (
        round(
            fleet_processing_s / ecu_count,
            2,
        )
        if ecu_count
        else 0.0
    )

    max_ecu_duration_s = (
        max(ecu_durations_s.values())
        if ecu_durations_s
        else 0.0
    )

    min_ecu_duration_s = (
        min(ecu_durations_s.values())
        if ecu_durations_s
        else 0.0
    )

    time_budget_s = float(
        timing_model[
            "nominal_time_budget_s"
        ]
    )

    if elapsed_s <= time_budget_s:
        budget_status = "WITHIN_BUDGET"
    else:
        budget_status = "EXCEEDED"

    return {
        "timing_model_id": (
            timing_model["model_id"]
        ),
        "execution_policy": (
            timing_model[
                "execution_policy"
            ]
        ),
        "time_budget_s": time_budget_s,
        "elapsed_s": elapsed_s,
        "fleet_processing_s": (
            fleet_processing_s
        ),
        "average_ecu_duration_s": (
            average_ecu_duration_s
        ),
        "max_ecu_duration_s": (
            max_ecu_duration_s
        ),
        "min_ecu_duration_s": (
            min_ecu_duration_s
        ),
        "budget_status": budget_status,
        "budget_margin_s": max(
            time_budget_s - elapsed_s,
            0.0,
        ),
        "budget_overrun_s": max(
            elapsed_s - time_budget_s,
            0.0,
        ),
        "ecu_durations_s": ecu_durations_s,
        "wave_durations": wave_durations,
    }
