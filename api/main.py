from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, HTTPException

from api.data_store import (
    CampaignDataError,
    CampaignDataStore,
)


API_TITLE = "PFE Multi-ECU OTA API"
API_VERSION = "1.0.0"
SOURCE_MODE = "SIMULATION"

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "API en lecture seule pour les données "
        "de campagne OTA multi-ECU."
    ),
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
