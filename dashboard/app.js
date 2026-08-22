"use strict";

const state = {
  config: null,
  campaign: null,
  kpis: null,
  ecus: [],
  waves: [],
  events: [],
  loading: false,
};

const elements = {};

function getElement(id) {
  return document.getElementById(id);
}

function cacheElements() {
  const ids = [
    "connectionState",
    "connectionLabel",
    "refreshButton",
    "errorBanner",
    "campaignTitle",
    "campaignStatus",
    "campaignRelease",
    "sourceMode",
    "lastUpdated",
    "totalEcus",
    "confirmedEcus",
    "confirmationRate",
    "failedEcus",
    "failureRate",
    "elapsedTime",
    "timeBudget",
    "budgetCard",
    "budgetMargin",
    "budgetStatus",
    "statusChart",
    "waveChart",
    "ecuSearch",
    "statusFilter",
    "ecuTableBody",
    "ecuTableSummary",
    "eventLevelFilter",
    "eventTableBody",
    "eventTableSummary",
  ];

  for (const id of ids) {
    elements[id] = getElement(id);
  }
}

function escapeHtml(value) {
  const characters = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };

  return String(value).replace(
    /[&<>"']/g,
    (character) => characters[character],
  );
}

function displayValue(value) {
  if (
    value === null
    || value === undefined
    || value === ""
  ) {
    return "—";
  }

  return String(value);
}

function formatNumber(value, digits = 0) {
  return new Intl.NumberFormat(
    "fr-FR",
    {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    },
  ).format(value);
}

function formatTimestamp(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    },
  ).format(date);
}

function getStatusDefinition(status) {
  return state.config.status_definitions.find(
    (item) => item.status === status,
  );
}

function getStatusColor(status) {
  const definition = getStatusDefinition(status);

  if (definition) {
    return definition.color;
  }

  if (status === "COMPLETED_WITH_FAILURES") {
    return "#F59E0B";
  }

  if (status === "COMPLETED") {
    return "#22C55E";
  }

  return "#8FA3BF";
}

function getStatusLabel(status) {
  const definition = getStatusDefinition(status);

  if (definition) {
    return definition.label;
  }

  const campaignLabels = {
    COMPLETED: "Terminée",
    COMPLETED_WITH_FAILURES: (
      "Terminée avec défaillances"
    ),
  };

  return (
    campaignLabels[status]
    || displayValue(status).replaceAll("_", " ")
  );
}

function applyTheme() {
  const theme = state.config.theme;
  const root = document.documentElement;

  const variables = {
    background: "--background",
    surface: "--surface",
    surface_alt: "--surface-alt",
    border: "--border",
    primary: "--primary",
    text: "--text",
    muted_text: "--muted",
  };

  for (const [key, variable] of Object.entries(
    variables,
  )) {
    if (theme[key]) {
      root.style.setProperty(
        variable,
        theme[key],
      );
    }
  }
}

async function fetchJson(path) {
  const response = await fetch(
    path,
    {
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      `${path} retourne HTTP ${response.status}`,
    );
  }

  return response.json();
}

function setConnection(status, label) {
  elements.connectionState.classList.remove(
    "online",
    "offline",
  );

  if (status) {
    elements.connectionState.classList.add(
      status,
    );
  }

  elements.connectionLabel.textContent = label;
}

function showError(error) {
  elements.errorBanner.textContent = (
    "Impossible de charger les données : "
    + error.message
  );
  elements.errorBanner.hidden = false;

  setConnection(
    "offline",
    "API indisponible",
  );
}

function clearError() {
  elements.errorBanner.hidden = true;
  elements.errorBanner.textContent = "";
}

function renderCampaign() {
  const campaign = state.campaign;
  const kpis = state.kpis;

  elements.campaignTitle.textContent = (
    campaign.campaign_id
  );
  elements.campaignRelease.textContent = (
    `Release : ${campaign.release_id}`
  );
  elements.sourceMode.textContent = (
    campaign.source_mode
  );

  const statusColor = getStatusColor(
    campaign.status,
  );

  elements.campaignStatus.textContent = (
    getStatusLabel(campaign.status)
  );
  elements.campaignStatus.style.color = (
    statusColor
  );
  elements.campaignStatus.style.borderColor = (
    `${statusColor}66`
  );
  elements.campaignStatus.style.background = (
    `${statusColor}1C`
  );

  elements.lastUpdated.textContent = (
    new Intl.DateTimeFormat(
      "fr-FR",
      {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      },
    ).format(new Date())
  );

  elements.totalEcus.textContent = (
    kpis.total_ecus
  );
  elements.confirmedEcus.textContent = (
    kpis.confirmed_ecus
  );
  elements.confirmationRate.textContent = (
    `${formatNumber(
      kpis.confirmation_rate_pct,
      2,
    )} %`
  );
  elements.failedEcus.textContent = (
    kpis.failed_ecus
  );
  elements.failureRate.textContent = (
    `${formatNumber(
      kpis.failure_rate_pct,
      2,
    )} %`
  );
  elements.elapsedTime.textContent = (
    `${formatNumber(kpis.elapsed_s, 1)} s`
  );
  elements.timeBudget.textContent = (
    `${formatNumber(
      kpis.time_budget_s,
      1,
    )} s`
  );

  elements.budgetCard.classList.remove(
    "success",
    "danger",
    "warning",
  );

  if (kpis.budget_status === "EXCEEDED") {
    elements.budgetMargin.textContent = (
      `-${formatNumber(
        kpis.budget_overrun_s,
        1,
      )} s`
    );
    elements.budgetStatus.textContent = (
      "Budget dépassé"
    );
    elements.budgetCard.classList.add(
      "danger",
    );
  } else {
    elements.budgetMargin.textContent = (
      `+${formatNumber(
        kpis.budget_margin_s,
        1,
      )} s`
    );
    elements.budgetStatus.textContent = (
      "Dans le budget"
    );
    elements.budgetCard.classList.add(
      "success",
    );
  }
}

function renderStatusChart() {
  const kpis = state.kpis;
  const total = kpis.total_ecus;

  const counts = {
    CONFIRMED: kpis.confirmed_ecus,
    REJECTED: kpis.rejected_ecus,
    ROLLED_BACK: kpis.rolled_back_ecus,
    BLOCKED: kpis.blocked_ecus,
    ROLLBACK_LOCKOUT: (
      kpis.locked_out_ecus
    ),
    RECOVERY_BOOT: kpis.recovery_ecus,
  };

  const rows = state.config.status_definitions.map(
    (definition) => {
      const count = (
        counts[definition.status] || 0
      );
      const percentage = (
        total > 0
        ? (count / total) * 100
        : 0
      );

      return `
        <div
          class="status-row"
          style="
            --status-color:
              ${escapeHtml(definition.color)};
            --bar-width:
              ${percentage.toFixed(2)}%;
          "
        >
          <div class="status-row-heading">
            <span class="status-row-label">
              <span
                class="status-swatch"
                aria-hidden="true"
              ></span>
              ${escapeHtml(definition.label)}
            </span>

            <span class="status-count">
              ${count}
            </span>
          </div>

          <div class="status-track">
            <div
              class="status-fill"
              title="${percentage.toFixed(2)} %"
            ></div>
          </div>
        </div>
      `;
    },
  );

  elements.statusChart.innerHTML = `
    <div class="status-list">
      ${rows.join("")}
    </div>
  `;
}

function renderWaveChart() {
  const maxDuration = Math.max(
    ...state.waves.map(
      (wave) => wave.elapsed_s,
    ),
    1,
  );

  const bars = state.waves.map(
    (wave) => {
      const height = (
        wave.elapsed_s / maxDuration
      ) * 100;

      return `
        <div class="wave-item">
          <span class="wave-value">
            ${formatNumber(wave.elapsed_s, 1)} s
          </span>

          <div class="wave-track">
            <div
              class="wave-fill"
              style="
                --wave-height:
                  ${height.toFixed(2)}%;
              "
              title="${
                escapeHtml(
                  wave.ecu_ids.join(", "),
                )
              }"
            ></div>
          </div>

          <span class="wave-label">
            Vague ${wave.wave_number}
          </span>

          <span class="wave-ecu-count">
            ${wave.ecu_count} ECU
          </span>
        </div>
      `;
    },
  );

  elements.waveChart.innerHTML = `
    <div class="wave-bars">
      ${bars.join("")}
    </div>
  `;
}

function populateStatusFilter() {
  const selected = elements.statusFilter.value;

  const options = (
    state.config.status_definitions.map(
      (definition) => `
        <option
          value="${escapeHtml(
            definition.status,
          )}"
        >
          ${escapeHtml(definition.label)}
        </option>
      `,
    )
  );

  elements.statusFilter.innerHTML = `
    <option value="">
      Tous les états
    </option>
    ${options.join("")}
  `;

  elements.statusFilter.value = selected;
}

function populateEventFilter() {
  const selected = (
    elements.eventLevelFilter.value
  );

  const levels = [
    ...new Set(
      state.events.map(
        (event) => event.level,
      ),
    ),
  ].sort();

  elements.eventLevelFilter.innerHTML = `
    <option value="">
      Tous les niveaux
    </option>
    ${
      levels.map(
        (level) => `
          <option value="${escapeHtml(level)}">
            ${escapeHtml(level)}
          </option>
        `,
      ).join("")
    }
  `;

  elements.eventLevelFilter.value = selected;
}

function renderEcuTable() {
  const search = (
    elements.ecuSearch.value
      .trim()
      .toLowerCase()
  );
  const selectedStatus = (
    elements.statusFilter.value
  );

  const filtered = state.ecus.filter(
    (ecu) => {
      const matchesStatus = (
        !selectedStatus
        || ecu.ota_status === selectedStatus
      );

      const searchableText = [
        ecu.ecu_id,
        ecu.name,
        ecu.domain,
        ecu.rollback_trigger,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return (
        matchesStatus
        && (
          !search
          || searchableText.includes(search)
        )
      );
    },
  );

  if (filtered.length === 0) {
    elements.ecuTableBody.innerHTML = `
      <tr>
        <td
          class="empty-state"
          colspan="8"
        >
          Aucun ECU ne correspond au filtre.
        </td>
      </tr>
    `;
  } else {
    elements.ecuTableBody.innerHTML = (
      filtered.map(
        (ecu) => {
          const color = getStatusColor(
            ecu.ota_status,
          );

          return `
            <tr>
              <td>
                <strong>
                  ${escapeHtml(ecu.ecu_id)}
                </strong>
              </td>

              <td>${escapeHtml(ecu.name)}</td>

              <td>
                ${escapeHtml(ecu.domain)}
              </td>

              <td>
                ${escapeHtml(
                  displayValue(
                    ecu.target_version,
                  ),
                )}
              </td>

              <td>
                <span
                  class="status-badge"
                  style="
                    --badge-color:
                      ${escapeHtml(color)};
                  "
                >
                  ${escapeHtml(
                    getStatusLabel(
                      ecu.ota_status,
                    ),
                  )}
                </span>
              </td>

              <td>
                ${formatNumber(
                  ecu.elapsed_s,
                  1,
                )} s
              </td>

              <td>
                ${escapeHtml(
                  ecu.active_partition,
                )}
              </td>

              <td class="muted-value">
                ${escapeHtml(
                  displayValue(
                    ecu.rollback_trigger,
                  ),
                )}
              </td>
            </tr>
          `;
        },
      ).join("")
    );
  }

  elements.ecuTableSummary.textContent = (
    `${filtered.length} ECU affichés `
    + `sur ${state.ecus.length}`
  );
}

function getLevelClass(level) {
  const classes = {
    WARNING: "warning",
    ERROR: "error",
    CRITICAL: "error",
  };

  return classes[level] || "";
}

function renderEventTable() {
  const selectedLevel = (
    elements.eventLevelFilter.value
  );

  const filtered = state.events
    .filter(
      (event) => (
        !selectedLevel
        || event.level === selectedLevel
      ),
    )
    .slice()
    .reverse();

  if (filtered.length === 0) {
    elements.eventTableBody.innerHTML = `
      <tr>
        <td
          class="empty-state"
          colspan="6"
        >
          Aucun événement ne correspond
          au filtre.
        </td>
      </tr>
    `;
  } else {
    elements.eventTableBody.innerHTML = (
      filtered.map(
        (event) => `
          <tr>
            <td>
              ${escapeHtml(
                formatTimestamp(
                  event.timestamp,
                ),
              )}
            </td>

            <td>
              ${escapeHtml(
                displayValue(event.ecu_id),
              )}
            </td>

            <td>
              <span
                class="level-badge ${
                  getLevelClass(event.level)
                }"
              >
                ${escapeHtml(event.level)}
              </span>
            </td>

            <td>
              ${escapeHtml(event.event_code)}
            </td>

            <td class="muted-value">
              ${escapeHtml(
                displayValue(
                  event.ota_status,
                ),
              )}
            </td>

            <td>
              ${escapeHtml(event.message)}
            </td>
          </tr>
        `,
      ).join("")
    );
  }

  elements.eventTableSummary.textContent = (
    `${filtered.length} événements affichés `
    + `sur ${state.events.length}`
  );
}

function renderDashboard() {
  renderCampaign();
  renderStatusChart();
  renderWaveChart();
  populateStatusFilter();
  populateEventFilter();
  renderEcuTable();
  renderEventTable();
}

async function loadConfig() {
  if (state.config) {
    return;
  }

  state.config = await fetchJson(
    "/dashboard/config.json",
  );

  applyTheme();
}

async function loadDashboard() {
  if (state.loading) {
    return;
  }

  state.loading = true;
  elements.refreshButton.disabled = true;

  setConnection(
    "",
    "Synchronisation…",
  );
  clearError();

  try {
    await loadConfig();

    const routes = state.config.api_routes;

    const [
      health,
      campaign,
      kpis,
      ecus,
      waves,
      events,
    ] = await Promise.all([
      fetchJson(routes.health),
      fetchJson(routes.campaign),
      fetchJson(routes.kpis),
      fetchJson(routes.ecus),
      fetchJson(routes.waves),
      fetchJson(routes.events),
    ]);

    if (health.status !== "ok") {
      throw new Error(
        "Le service API n’est pas prêt.",
      );
    }

    state.campaign = campaign;
    state.kpis = kpis;
    state.ecus = ecus;
    state.waves = waves;
    state.events = events;

    renderDashboard();

    setConnection(
      "online",
      "API connectée",
    );
  } catch (error) {
    showError(error);
  } finally {
    state.loading = false;
    elements.refreshButton.disabled = false;
  }
}

async function initialize() {
  cacheElements();

  elements.refreshButton.addEventListener(
    "click",
    loadDashboard,
  );
  elements.ecuSearch.addEventListener(
    "input",
    renderEcuTable,
  );
  elements.statusFilter.addEventListener(
    "change",
    renderEcuTable,
  );
  elements.eventLevelFilter.addEventListener(
    "change",
    renderEventTable,
  );

  await loadDashboard();

  const intervalSeconds = (
    state.config?.refresh_interval_s || 10
  );

  window.setInterval(
    loadDashboard,
    intervalSeconds * 1000,
  );
}

document.addEventListener(
  "DOMContentLoaded",
  initialize,
);
