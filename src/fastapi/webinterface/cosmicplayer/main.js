window.initCosmicplayerTab = function() {
    console.log("CosmicPlayer tab initialized");

    // Elements
    const streamForm = document.getElementById('stream-form');
    const streamUrlInput = document.getElementById('stream-url');
    const embedPlayer = document.getElementById('embed-player');
    const html5PlayerWrapper = document.getElementById('html5-player-wrapper');
    const html5Video = document.getElementById('html5-video');
    const playerPlaceholder = document.getElementById('player-placeholder');
    const videoTitle = document.getElementById('video-title');
    const videoSourceUrl = document.getElementById('video-source-url');
    const currentProviderTag = document.getElementById('current-provider-tag');
    const historyList = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history');
    const badges = document.querySelectorAll('.cosmic-player-tab .badge');
    const ambientGlow = document.getElementById('ambient-glow');

    // Custom controls
    const playPauseBtn = document.getElementById('play-pause-btn');
    const stopBtn = document.getElementById('stop-btn');
    const currentTimeDisplay = document.getElementById('current-time');
    const durationTimeDisplay = document.getElementById('duration-time');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressHover = document.querySelector('.progress-hover');
    const muteBtn = document.getElementById('mute-btn');
    const volumeSlider = document.getElementById('volume-slider');
    const speedSelect = document.getElementById('speed-select');
    const fullscreenBtn = document.getElementById('fullscreen-btn');

    let hlsInstance = null;
    let history = JSON.parse(localStorage.getItem('cosmic_player_history') || '[]');

    // Dynamic ambient glow colors per provider
    const providerColors = {
        youtube: 'radial-gradient(circle, rgba(255, 0, 0, 0.25) 0%, transparent 60%)',
        vk: 'radial-gradient(circle, rgba(74, 118, 168, 0.25) 0%, transparent 60%)',
        rutube: 'radial-gradient(circle, rgba(235, 95, 30, 0.25) 0%, transparent 60%)',
        hdrezka: 'radial-gradient(circle, rgba(242, 197, 17, 0.2) 0%, transparent 60%)',
        seasonvar: 'radial-gradient(circle, rgba(0, 242, 254, 0.2) 0%, transparent 60%)',
        kinogo: 'radial-gradient(circle, rgba(155, 81, 224, 0.2) 0%, transparent 60%)',
        direct: 'radial-gradient(circle, rgba(121, 40, 202, 0.25) 0%, transparent 60%)',
        offline: 'radial-gradient(circle, rgba(255, 255, 255, 0.05) 0%, transparent 60%)'
    };

    // Load history on start
    renderHistory();

    // Form submission
    streamForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = streamUrlInput.value.trim();
        if (url) {
            loadVideo(url);
        }
    });

    // Clear history
    clearHistoryBtn.addEventListener('click', () => {
        history = [];
        localStorage.setItem('cosmic_player_history', JSON.stringify(history));
        renderHistory();
    });

    // Router and url parser
    function loadVideo(url, title = null) {
        resetPlayers();

        const providerInfo = parseVideoUrl(url);
        const resolvedTitle = title || providerInfo.defaultTitle;
        
        highlightBadge(providerInfo.provider);

        // Update info panel
        videoTitle.textContent = resolvedTitle;
        videoSourceUrl.textContent = url;
        currentProviderTag.textContent = providerInfo.provider;
        
        // Update ambient glow color
        ambientGlow.style.background = providerColors[providerInfo.provider] || providerColors.direct;

        // Route to the correct player engine
        if (providerInfo.type === 'embed') {
            embedPlayer.src = providerInfo.embedUrl;
            embedPlayer.classList.remove('hidden');
        } else if (providerInfo.type === 'html5') {
            initHTML5Player(url);
            html5PlayerWrapper.classList.remove('hidden');
        } else if (providerInfo.type === 'iframe_fallback') {
            embedPlayer.src = url;
            embedPlayer.classList.remove('hidden');
        }

        // Add to history
        addToHistory(url, resolvedTitle, providerInfo.provider);
    }

    function resetPlayers() {
        embedPlayer.classList.add('hidden');
        embedPlayer.src = '';
        html5PlayerWrapper.classList.add('hidden');
        playerPlaceholder.classList.add('hidden');

        html5Video.pause();
        html5Video.src = '';

        if (hlsInstance) {
            hlsInstance.destroy();
            hlsInstance = null;
        }
    }

    // Video URL Parser
    function parseVideoUrl(url) {
        // YouTube Matcher
        const ytReg = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
        const ytMatch = url.match(ytReg);
        if (ytMatch) {
            return {
                provider: 'youtube',
                type: 'embed',
                embedUrl: `https://www.youtube.com/embed/${ytMatch[1]}?autoplay=1&rel=0`,
                defaultTitle: `YouTube Video (${ytMatch[1]})`
            };
        }

        // VK Matcher
        const vkReg = /vk\.com\/video(-?\d+)_(\d+)/;
        const vkMatch = url.match(vkReg);
        const vkEmbedReg = /oid=(-?\d+)&id=(\d+)(?:&hash=([a-f0-9]+))?/;
        const vkEmbedMatch = url.match(vkEmbedReg);

        if (vkMatch) {
            return {
                provider: 'vk',
                type: 'embed',
                embedUrl: `https://vk.com/video_ext.php?oid=${vkMatch[1]}&id=${vkMatch[2]}&autoplay=1`,
                defaultTitle: `VK Video (${vkMatch[1]}_${vkMatch[2]})`
            };
        } else if (vkEmbedMatch) {
            const hashParam = vkEmbedMatch[3] ? `&hash=${vkEmbedMatch[3]}` : '';
            return {
                provider: 'vk',
                type: 'embed',
                embedUrl: `https://vk.com/video_ext.php?oid=${vkEmbedMatch[1]}&id=${vkEmbedMatch[2]}${hashParam}&autoplay=1`,
                defaultTitle: `VK Embed Video`
            };
        }

        // RuTube Matcher
        const rutubeReg = /rutube\.ru\/(?:video|play\/embed)\/([a-f0-9]{32})/;
        const rutubeMatch = url.match(rutubeReg);
        if (rutubeMatch) {
            return {
                provider: 'rutube',
                type: 'embed',
                embedUrl: `https://rutube.ru/play/embed/${rutubeMatch[1]}?autoplay=1`,
                defaultTitle: `RuTube Video`
            };
        }

        // Direct Stream (MP4/HLS)
        const isHLS = url.includes('.m3u8');
        const isMP4 = url.includes('.mp4');
        if (isHLS || isMP4) {
            return {
                provider: 'direct',
                type: 'html5',
                defaultTitle: isHLS ? 'Прямой HLS поток' : 'Прямой MP4 файл'
            };
        }

        // SeasonVar
        if (url.includes('seasonvar.ru')) {
            return {
                provider: 'seasonvar',
                type: 'iframe_fallback',
                defaultTitle: 'СезонВар плеер'
            };
        }

        // HDRezka
        if (url.includes('rezka.ag') || url.includes('hdrezka')) {
            return {
                provider: 'hdrezka',
                type: 'iframe_fallback',
                defaultTitle: 'Резка плеер'
            };
        }

        // Kinogo
        if (url.includes('kinogo')) {
            return {
                provider: 'kinogo',
                type: 'iframe_fallback',
                defaultTitle: 'Киного плеер'
            };
        }

        // Default fallback
        return {
            provider: 'direct',
            type: 'html5',
            defaultTitle: 'Прямой видеоисточник'
        };
    }

    function initHTML5Player(url) {
        if (url.includes('.m3u8')) {
            if (typeof Hls !== 'undefined' && Hls.isSupported()) {
                hlsInstance = new Hls();
                hlsInstance.loadSource(url);
                hlsInstance.attachMedia(html5Video);
                hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
                    html5Video.play();
                });
            } else if (html5Video.canPlayType('application/vnd.apple.mpegurl')) {
                html5Video.src = url;
                html5Video.play();
            }
        } else {
            html5Video.src = url;
            html5Video.play();
        }

        playPauseBtn.textContent = '⏸';
    }

    // Video events
    html5Video.addEventListener('timeupdate', () => {
        const current = html5Video.currentTime;
        const total = html5Video.duration || 0;
        
        if (total > 0) {
            const pct = (current / total) * 100;
            progressBar.style.width = `${pct}%`;
        }

        currentTimeDisplay.textContent = formatTime(current);
        durationTimeDisplay.textContent = formatTime(total);
    });

    html5Video.addEventListener('loadedmetadata', () => {
        durationTimeDisplay.textContent = formatTime(html5Video.duration);
    });

    playPauseBtn.addEventListener('click', () => {
        if (html5Video.paused) {
            html5Video.play();
            playPauseBtn.textContent = '⏸';
        } else {
            html5Video.pause();
            playPauseBtn.textContent = '▶';
        }
    });

    stopBtn.addEventListener('click', () => {
        html5Video.pause();
        html5Video.currentTime = 0;
        playPauseBtn.textContent = '▶';
    });

    volumeSlider.addEventListener('input', (e) => {
        const vol = e.target.value;
        html5Video.volume = vol;
        if (vol === '0') {
            muteBtn.textContent = '🔇';
        } else {
            muteBtn.textContent = '🔊';
        }
    });

    muteBtn.addEventListener('click', () => {
        if (html5Video.muted) {
            html5Video.muted = false;
            volumeSlider.value = html5Video.volume;
            muteBtn.textContent = '🔊';
        } else {
            html5Video.muted = true;
            volumeSlider.value = 0;
            muteBtn.textContent = '🔇';
        }
    });

    speedSelect.addEventListener('change', (e) => {
        html5Video.playbackRate = parseFloat(e.target.value);
    });

    progressContainer.addEventListener('click', (e) => {
        const rect = progressContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const width = rect.width;
        const pct = clickX / width;
        
        html5Video.currentTime = pct * html5Video.duration;
    });

    progressContainer.addEventListener('mousemove', (e) => {
        const rect = progressContainer.getBoundingClientRect();
        const hoverX = e.clientX - rect.left;
        const pct = hoverX / rect.width;
        progressHover.style.width = `${pct * 100}%`;
    });

    progressContainer.addEventListener('mouseleave', () => {
        progressHover.style.width = '0%';
    });

    fullscreenBtn.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            html5PlayerWrapper.requestFullscreen().catch(err => {
                console.error(`Error enabling fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    });

    function formatTime(sec) {
        if (isNaN(sec)) return '0:00';
        const mins = Math.floor(sec / 60);
        const secs = Math.floor(sec % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }

    function highlightBadge(provider) {
        badges.forEach(badge => {
            if (badge.getAttribute('data-provider') === provider) {
                badge.classList.add('active');
            } else {
                badge.classList.remove('active');
            }
        });
    }

    function addToHistory(url, title, provider) {
        history = history.filter(item => item.url !== url);
        
        history.unshift({
            url,
            title,
            provider,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });

        if (history.length > 8) history.pop();

        localStorage.setItem('cosmic_player_history', JSON.stringify(history));
        renderHistory();
    }

    function renderHistory() {
        historyList.innerHTML = '';
        if (history.length === 0) {
            historyList.innerHTML = '<div class="empty-state">Нет недавно проигранных видео</div>';
            return;
        }

        history.forEach(item => {
            const el = document.createElement('div');
            el.className = 'history-item';
            el.innerHTML = `
                <div class="history-title" title="${item.title}">${item.title}</div>
                <div class="history-meta">
                    <span>${item.provider.toUpperCase()}</span>
                    <span>${item.timestamp}</span>
                </div>
            `;
            el.addEventListener('click', () => {
                streamUrlInput.value = item.url;
                loadVideo(item.url, item.title);
            });
            historyList.appendChild(el);
        });
    }

    badges.forEach(badge => {
        badge.addEventListener('click', () => {
            const provider = badge.getAttribute('data-provider');
            let demoUrl = '';

            switch (provider) {
                case 'youtube':
                    demoUrl = 'https://www.youtube.com/watch?v=aqz-KE-bpKQ';
                    break;
                case 'vk':
                    demoUrl = 'https://vk.com/video-22822305_456239018';
                    break;
                case 'rutube':
                    demoUrl = 'https://rutube.ru/video/e7cfcb8cb4310d54026fb4bd56e828d1/';
                    break;
                case 'direct':
                    demoUrl = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
                    break;
                case 'seasonvar':
                    demoUrl = 'http://seasonvar.ru';
                    break;
                case 'hdrezka':
                    demoUrl = 'https://rezka.ag';
                    break;
                case 'kinogo':
                    demoUrl = 'https://kinogo.biz';
                    break;
            }

            if (demoUrl) {
                streamUrlInput.value = demoUrl;
                loadVideo(demoUrl);
            }
        });
    });
};
