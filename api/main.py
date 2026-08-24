from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.qemu_rauc_connector import load_qemu_ecu
from api.data_store import (
    CampaignDataError,
    CampaignDataStore,
)


API_TITLE = "PFE Multi-ECU OTA API"
API_VERSION = "1.0.0"
SOURCE_MODE = "HYBRID"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIRECTORY = (
    PROJECT_ROOT
    / "dashboard"
)

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "API en lecture seule pour les données "
        "de campagne OTA multi-ECU."
    ),
)

app.mount(
    "/dashboard",
    StaticFiles(
        directory=DASHBOARD_DIRECTORY,
        html=True,
    ),
    name="dashboard",
)

data_store = CampaignDataStore()


def _load_or_raise(
    loader: Callable[[], Any],
) -> Any:
    try:
        return loader()
    except CampaignDataError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@app.get(
    "/",
    include_in_schema=False,
)
def get_root() -> RedirectResponse:
    return RedirectResponse(
        url="/dashboard/",
        status_code=307,
    )


@app.get(
    "/health",
    tags=["System"],
)
def get_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": API_TITLE,
        "api_version": API_VERSION,
        "source_mode": SOURCE_MODE,
        "read_only": True,
    }


@app.get(
    "/api/v1/campaign",
    tags=["Campaign"],
)
def get_campaign() -> dict[str, Any]:
    return _load_or_raise(
        data_store.load_campaign
    )


@app.get(
    "/api/v1/kpis",
    tags=["Campaign"],
)
def get_kpis() -> dict[str, Any]:
    return _load_or_raise(
        data_store.load_kpis
    )


@app.get(
    "/api/v1/ecus",
    tags=["ECUs"],
)
def get_ecus() -> list[dict[str, Any]]:
    return _load_or_raise(
        data_store.load_ecus
    )

@app.get(
    "/api/v1/waves",
    tags=["Waves"],
)
def get_waves() -> list[dict[str, Any]]:
    return _load_or_raise(
        data_store.load_waves
    )


@app.get(
    "/api/v1/events",
    tags=["Events"],
)
def get_events() -> list[dict[str, Any]]:
    return _load_or_raise(
        data_store.load_events
    )

@app.get(
    "/api/v1/sources",
    tags=["Sources"],
)
def get_sources() -> dict[str, Any]:
    campaign = _load_or_raise(
        data_store.load_campaign
    )

    qemu_ecu = load_qemu_ecu()

    return {
        "schema_version": "1.0",
        "source_mode": SOURCE_MODE,
        "simulated_fleet": {
            "source_type": "SIMULATED",
            "available": True,
            "campaign_id": campaign[
                "campaign_id"
            ],
            "total_ecus": campaign[
                "total_ecus"
            ],
        },
        "qemu_rauc_target": {
            "source_type": qemu_ecu[
                "source_type"
            ],
            "ecu_id": qemu_ecu["ecu_id"],
            "available": qemu_ecu[
                "connected"
            ],
            "connected": qemu_ecu[
                "connected"
            ],
            "health_status": qemu_ecu[
                "health_status"
            ],
            "ota_status": qemu_ecu[
                "ota_status"
            ],
            "current_version": qemu_ecu.get(
                "current_version"
            ),
            "active_partition": qemu_ecu.get(
                "active_partition"
            ),
            "connector_error": qemu_ecu.get(
                "connector_error"
            ),
        },
    }


@app.get(
    "/api/v1/qemu-ecu",
    tags=["ECUs"],
)
def get_qemu_ecu() -> dict[str, Any]:
    return load_qemu_ecu()
