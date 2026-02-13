const API_ENDPOINT = "/api/v2/wrapped";
const TRACKS_CHART_ID = "top-tracks-chart";
const PERIODS_CHART_ID = "periods-chart";

let topTracksChart = null;
let periodsChart = null;

const statusPanel = document.getElementById("status-panel");
const statusMessage = document.getElementById("status-message");
const retryButton = document.getElementById("retry-btn");
const generatedAtEl = document.getElementById("generated-at");
const totalHoursEl = document.getElementById("total-hours");
const topArtistNameEl = document.getElementById("top-artist-name");
const topArtistHoursEl = document.getElementById("top-artist-hours");
const activeHourEl = document.getElementById("active-hour-val");
const activeHourMinutesEl = document.getElementById("active-hour-minutes");
const podcastsListEl = document.getElementById("top-podcasts-list");
const topDaysListEl = document.getElementById("top-days-list");
const mostPlayedNameEl = document.getElementById("most-played-name");
const mostPlayedCountEl = document.getElementById("most-played-count");
const skipsListEl = document.getElementById("skips-list");
const topTracksEmptyEl = document.getElementById("top-tracks-empty");
const periodsEmptyEl = document.getElementById("periods-empty");

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function asArray(value) {
    return Array.isArray(value) ? value : [];
}

function toNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function setStatus(state, message) {
    statusPanel.classList.remove("loading", "error", "ready");
    statusPanel.classList.add(state);
    statusMessage.textContent = message;
}

function formatHour(hourValue) {
    const hour = Number(hourValue);
    if (!Number.isInteger(hour) || hour < 0 || hour > 23) {
        return "--";
    }
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;
    return `${displayHour} ${ampm}`;
}

function formatGeneratedAt(timestamp) {
    if (!timestamp) {
        return "Summary cache timestamp unavailable.";
    }

    const generatedDate = new Date(timestamp);
    if (Number.isNaN(generatedDate.getTime())) {
        return "Summary generated date is unavailable.";
    }

    return `Summary generated on ${generatedDate.toLocaleString()}.`;
}

function renderInsightList(container, rows, renderRow, emptyMessage) {
    if (!rows.length) {
        container.innerHTML = `<li><span class="insight-sub">${escapeHtml(emptyMessage)}</span></li>`;
        return;
    }
    container.innerHTML = rows.map(renderRow).join("");
}

function showChartEmptyState(canvasId, emptyEl, message) {
    const canvas = document.getElementById(canvasId);
    canvas.style.display = "none";
    emptyEl.textContent = message;
}

function showChart(canvasId, emptyEl) {
    const canvas = document.getElementById(canvasId);
    canvas.style.display = "block";
    emptyEl.textContent = "";
}

function renderTopTracksChart(topTracks) {
    const rows = asArray(topTracks);
    const labels = rows.map((track) => {
        const name = track.track_name || "Unknown Track";
        const artist = track.artist_name || "Unknown Artist";
        return `${name} · ${artist}`;
    });
    const minutes = rows.map((track) => toNumber(track.total_minutes_played));

    if (topTracksChart) {
        topTracksChart.destroy();
    }

    if (typeof Chart === "undefined") {
        showChartEmptyState(TRACKS_CHART_ID, topTracksEmptyEl, "Chart library is unavailable.");
        return;
    }

    if (!labels.length) {
        showChartEmptyState(TRACKS_CHART_ID, topTracksEmptyEl, "No track data available.");
        return;
    }

    showChart(TRACKS_CHART_ID, topTracksEmptyEl);
    const ctx = document.getElementById(TRACKS_CHART_ID);

    topTracksChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Minutes Played",
                    data: minutes,
                    backgroundColor: "rgba(226, 85, 47, 0.75)",
                    borderColor: "rgba(182, 61, 31, 1)",
                    borderRadius: 10,
                    borderWidth: 1.2,
                },
            ],
        },
        options: {
            animation: { duration: 800 },
            indexAxis: "y",
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${Math.round(context.raw)} min`,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: "#5f6b82" },
                    grid: { color: "rgba(31, 39, 55, 0.08)" },
                },
                y: {
                    ticks: { color: "#1f2737" },
                    grid: { display: false },
                },
            },
        },
    });
}

function renderPeriodsChart(periods) {
    const rows = asArray(periods);
    const labels = rows.map((period) => period.period || "Unknown");
    const minutes = rows.map((period) => toNumber(period.total_minutes_played));

    if (periodsChart) {
        periodsChart.destroy();
    }

    if (typeof Chart === "undefined") {
        showChartEmptyState(PERIODS_CHART_ID, periodsEmptyEl, "Chart library is unavailable.");
        return;
    }

    if (!labels.length) {
        showChartEmptyState(PERIODS_CHART_ID, periodsEmptyEl, "No listening period data available.");
        return;
    }

    showChart(PERIODS_CHART_ID, periodsEmptyEl);
    const ctx = document.getElementById(PERIODS_CHART_ID);

    periodsChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [
                {
                    data: minutes,
                    backgroundColor: ["#e2552f", "#0a9d85", "#f0b14a", "#4676d7"],
                    borderColor: "#fbf8f0",
                    borderWidth: 3,
                },
            ],
        },
        options: {
            animation: { duration: 900 },
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#1f2737",
                        font: { family: "Manrope", size: 12, weight: "700" },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.label}: ${Math.round(context.raw)} min`,
                    },
                },
            },
        },
    });
}

function renderPodcasts(topPodcasts) {
    const rows = asArray(topPodcasts);
    renderInsightList(
        podcastsListEl,
        rows,
        (podcast, index) => `
            <li>
                <span class="insight-rank">${index + 1}</span>
                <div>
                    <p class="insight-title">${escapeHtml(podcast.episode_name || "Unknown Episode")}</p>
                    <p class="insight-sub">${escapeHtml(podcast.episode_show_name || "Unknown Show")}</p>
                </div>
                <span class="insight-value">${Math.round(toNumber(podcast.total_minutes_played))} min</span>
            </li>
        `,
        "No podcast data available."
    );
}

function renderTopDays(topDays) {
    const rows = asArray(topDays);
    renderInsightList(
        topDaysListEl,
        rows,
        (day, index) => {
            const dateObj = new Date(day.day);
            const dayNumber = Number.isNaN(dateObj.getTime()) ? "" : ` ${dateObj.getDate()}`;
            const label = `${day.day_of_week || "Unknown"}, ${day.month || ""}${dayNumber}`.trim();

            return `
                <li>
                    <span class="insight-rank">${index + 1}</span>
                    <div>
                        <p class="insight-title">${escapeHtml(label)}</p>
                        <p class="insight-sub">${escapeHtml(day.day || "")}</p>
                    </div>
                    <span class="insight-value">${Math.round(toNumber(day.total_minutes_played))} min</span>
                </li>
            `;
        },
        "No top-day data available."
    );
}

function renderSkips(skips) {
    const rows = asArray(skips).slice(0, 5);
    renderInsightList(
        skipsListEl,
        rows,
        (track) => `
            <li>
                <span class="insight-title">${escapeHtml(track.track_name || "Unknown Track")}</span>
                <span class="insight-value">${Math.round(toNumber(track.skips))} skips</span>
            </li>
        `,
        "No skip data available."
    );
}

function renderWrapped(wrapped) {
    const topArtist = wrapped.top_artist || {};
    const activeHour = wrapped.active_hour || {};
    const mostPlayed = wrapped.most_played || {};

    totalHoursEl.textContent = Math.round(toNumber(wrapped.total_time?.hours)).toLocaleString();
    topArtistNameEl.textContent = topArtist.artist_name || "No data";
    topArtistHoursEl.textContent = topArtist.artist_name
        ? `${Math.round(toNumber(topArtist.total_hours_played))} hours`
        : "No artist data";

    activeHourEl.textContent = formatHour(activeHour.hour);
    activeHourMinutesEl.textContent = activeHour.hour !== undefined
        ? `${Math.round(toNumber(activeHour.total_minutes_played))} minutes`
        : "No hour data";

    mostPlayedNameEl.textContent = mostPlayed.track_name || "No data";
    mostPlayedCountEl.textContent = mostPlayed.track_name
        ? `${Math.round(toNumber(mostPlayed.play_count))} plays`
        : "No track play-count data";

    generatedAtEl.textContent = formatGeneratedAt(wrapped.generated_at);

    renderTopTracksChart(wrapped.top_tracks);
    renderPeriodsChart(wrapped.listening_periods);
    renderPodcasts(wrapped.top_podcasts);
    renderTopDays(wrapped.top_days);
    renderSkips(wrapped.skips);
}

async function fetchWrappedData() {
    const response = await fetch(API_ENDPOINT, {
        headers: { Accept: "application/json" },
    });

    if (!response.ok) {
        let detail = `Request failed with status ${response.status}.`;
        try {
            const body = await response.json();
            if (body?.detail) {
                detail = body.detail;
            }
        } catch (_err) {
            // No-op: keep fallback status message.
        }
        throw new Error(detail);
    }

    return response.json();
}

function animateEntrance() {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion || typeof gsap === "undefined") {
        return;
    }

    gsap.from(".hero", { opacity: 0, y: 24, duration: 0.6, ease: "power2.out" });
    gsap.from(".grid-layout .reveal", {
        opacity: 0,
        y: 20,
        duration: 0.5,
        stagger: 0.06,
        ease: "power2.out",
        delay: 0.15,
    });
}

async function loadWrapped() {
    setStatus("loading", "Loading wrapped data...");

    try {
        const wrapped = await fetchWrappedData();
        renderWrapped(wrapped);
        animateEntrance();
        setStatus("ready", "Wrapped data loaded.");
    } catch (error) {
        console.error(error);
        setStatus("error", error.message || "Unable to load wrapped data.");
    }
}

retryButton.addEventListener("click", loadWrapped);
loadWrapped();
