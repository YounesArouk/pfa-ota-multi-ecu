import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "latest"
)

INTEGER_FIELDS = {
    "progress_pct",
    "rollback_counter",
    "consecutive_rollback_counter",
    "recovery_boot_counter",
    "wave_number",
    "ecu_count",
}

FLOAT_FIELDS = {
    "elapsed_s",
}

BOOLEAN_FIELDS = {
    "connected",
    "rollback_lockout",
}

LIST_FIELDS = {
    "dependencies",
    "ecu_ids",
}


class CampaignDataError(RuntimeError):
    """Erreur de lecture des données exportées."""


class CampaignDataStore:
    """Accès en lecture seule aux exports de campagne."""

    def __init__(
        self,
        data_directory: str | Path = (
            DEFAULT_DATA_DIRECTORY
        ),
    ):
        self.data_directory = Path(
            data_directory
        )

    def _resolve_file(
        self,
        filename: str,
    ) -> Path:
        path = self.data_directory / filename

        if not path.is_file():
            raise CampaignDataError(
                "Fichier de données introuvable : "
                f"{path}"
            )

        return path

    def _load_json_object(
        self,
        filename: str,
    ) -> dict[str, Any]:
        path = self._resolve_file(filename)

        try:
            with path.open(
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise CampaignDataError(
                "Impossible de lire le fichier JSON : "
                f"{path}"
            ) from error

        if not isinstance(data, dict):
            raise CampaignDataError(
                "Le fichier JSON doit contenir "
                f"un objet : {path}"
            )

        return data

    def _convert_csv_value(
        self,
        field: str,
        value: str | None,
    ) -> Any:
        if value is None:
            raise CampaignDataError(
                "Valeur CSV absente pour le champ "
                f"{field}"
            )

        if field in LIST_FIELDS:
            if value == "":
                return []

            return [
                item
                for item in value.split("|")
                if item
            ]

        if value == "":
            return None

        try:
            if field in INTEGER_FIELDS:
                return int(value)

            if field in FLOAT_FIELDS:
                return float(value)

            if field in BOOLEAN_FIELDS:
                if value == "True":
                    return True

                if value == "False":
                    return False

                raise ValueError(
                    "booléen invalide"
                )
        except ValueError as error:
            raise CampaignDataError(
                "Valeur CSV invalide pour "
                f"{field} : {value}"
            ) from error

        return value

    def _load_csv_records(
        self,
        filename: str,
    ) -> list[dict[str, Any]]:
        path = self._resolve_file(filename)

        try:
            with path.open(
                encoding="utf-8",
                newline="",
            ) as file:
                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    raise CampaignDataError(
                        "En-tête CSV absent : "
                        f"{path}"
                    )

                return [
                    {
                        field: (
                            self._convert_csv_value(
                                field,
                                value,
                            )
                        )
                        for field, value
                        in row.items()
                    }
                    for row in reader
                ]
        except (OSError, csv.Error) as error:
            raise CampaignDataError(
                "Impossible de lire le fichier CSV : "
                f"{path}"
            ) from error

    def load_campaign(
        self,
    ) -> dict[str, Any]:
        return self._load_json_object(
            "campaign-summary.json"
        )

    def load_kpis(
        self,
    ) -> dict[str, Any]:
        return self._load_json_object(
            "campaign-kpis.json"
        )

    def load_ecus(
        self,
    ) -> list[dict[str, Any]]:
        return self._load_csv_records(
            "ecu-results.csv"
        )

    def load_waves(
        self,
    ) -> list[dict[str, Any]]:
        return self._load_csv_records(
            "wave-timing.csv"
        )

    def load_events(
        self,
    ) -> list[dict[str, Any]]:
        return self._load_csv_records(
            "events.csv"
        )
