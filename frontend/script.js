const API_BASE = '/api/stats';

async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}/${endpoint}`);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        return null;
    }
}

async function init() {
    // Total Time
    const totalTime = await fetchData('total-time');
    if (totalTime) {
        document.getElementById('total-hours').textContent = Math.round(totalTime.total_hours_played_2025);
    }

    // Top Artist
    const topArtist = await fetchData('top-artist');
    if (topArtist) {
        document.getElementById('top-artist-name').textContent = topArtist.artist_name;
        document.getElementById('top-artist-hours').textContent = `${Math.round(topArtist.total_hours_played)} hours`;
    }

    // Top Tracks
    const topTracks = await fetchData('top-tracks');
    if (topTracks) {
        const list = document.getElementById('top-tracks-list');
        list.innerHTML = topTracks.map((track, index) => `
            <li>
                <span class="rank">${index + 1}</span>
                <div class="info">
                    <div class="name">${track.track_name}</div>
                    <div class="meta">${track.artist_name}</div>
                </div>
                <div class="stat">${Math.round(track.total_minutes_played)} min</div>
            </li>
        `).join('');
    }

    // Top Podcasts
    const topPodcasts = await fetchData('top-podcasts');
    if (topPodcasts) {
        const list = document.getElementById('top-podcasts-list');
        list.innerHTML = topPodcasts.map((pod, index) => `
            <li>
                <span class="rank">${index + 1}</span>
                <div class="info">
                    <div class="name">${pod.episode_name}</div>
                    <div class="meta">${pod.episode_show_name}</div>
                </div>
                <div class="stat">${Math.round(pod.total_minutes_played)} min</div>
            </li>
        `).join('');
    }

    // Active Hour
    const activeHour = await fetchData('active-hour');
    if (activeHour) {
        const hour = activeHour.hour;
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        document.getElementById('active-hour-val').textContent = `${displayHour} ${ampm}`;
    }

    // Listening Periods
    const periods = await fetchData('listening-periods');
    if (periods) {
        const container = document.getElementById('periods-chart');
        const max = Math.max(...periods.map(p => p.total_minutes_played));
        container.innerHTML = periods.map(p => `
            <div class="bar-container">
                <div class="bar-label">${p.period}</div>
                <div class="bar-bg">
                    <div class="bar-fill" style="width: ${(p.total_minutes_played / max) * 100}%"></div>
                </div>
            </div>
        `).join('');
    }

    // Top Days
    const topDays = await fetchData('top-days');
    if (topDays) {
        const list = document.getElementById('top-days-list');
        list.innerHTML = topDays.map(day => `
            <li>
                <div class="info">
                    <div class="name">${day.day_of_week}, ${day.month} ${new Date(day.day).getDate()}</div>
                </div>
                <div class="stat">${Math.round(day.total_minutes_played)} min</div>
            </li>
        `).join('');
    }

    // Most Played
    const mostPlayed = await fetchData('most-played');
    if (mostPlayed) {
        document.getElementById('most-played-name').textContent = mostPlayed.track_name;
        document.getElementById('most-played-count').textContent = `${mostPlayed.play_count} plays`;
    }

    // Skips
    const skips = await fetchData('skips');
    if (skips) {
        const list = document.getElementById('skips-list');
        list.innerHTML = skips.slice(0, 5).map(track => `
            <li>
                <div class="info">${track.track_name}</div>
                <div class="stat">${track.skips} skips</div>
            </li>
        `).join('');
    }
}

init();
