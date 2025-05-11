// Global API base URL
const API_BASE = '/api';

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize page data
    loadInitialData();
    
    // Add event listeners
    setupEventListeners();
    
    // Set up hover effects for anime cards (will work for both static and dynamic cards)
    setupCardHoverEffects();
});

async function loadInitialData() {
    try {
        // Load data for the current page
        const path = window.location.pathname;
        
        if (path === '/' || path === '/index.html') {
            await loadHomepageData();
        } else if (path === '/movies') {
            await loadMoviesData();
        } else if (path === '/tv-series') {
            await loadTVSeriesData();
        }
        // Add more page-specific loaders as needed
        
    } catch (error) {
        console.error('Error loading initial data:', error);
        showErrorNotification('Failed to load page data. Please try again later.');
    }
}

async function loadHomepageData() {
    // Show loading states
    document.querySelectorAll('[data-loading]').forEach(el => {
        el.classList.add('loading');
    });

    try {
        // Fetch all data in parallel
        const [trending, searches, posts] = await Promise.all([
            fetchData(`${API_BASE}/trending`),
            fetchData(`${API_BASE}/top-searches`),
            fetchData(`${API_BASE}/trending-posts`)
        ]);

        // Render the data
        if (trending) {
            renderAnimeCards('trending-anime-container', trending);
        }
        
        if (searches) {
            renderTopSearches('top-searches-container', searches);
        }
        
        if (posts) {
            renderTrendingPosts('trending-posts-container', posts);
        }
        
    } finally {
        // Hide loading states
        document.querySelectorAll('[data-loading]').forEach(el => {
            el.classList.remove('loading');
        });
    }
}

async function loadMoviesData() {
    try {
        const movies = await fetchData(`${API_BASE}/movies`);
        if (movies) {
            renderAnimeCards('movies-container', movies);
        }
    } catch (error) {
        console.error('Error loading movies:', error);
        throw error;
    }
}

async function loadTVSeriesData() {
    try {
        const series = await fetchData(`${API_BASE}/tv-series`);
        if (series) {
            renderAnimeCards('tv-series-container', series);
        }
    } catch (error) {
        console.error('Error loading TV series:', error);
        throw error;
    }
}

function setupEventListeners() {
    // Search form handling (preserved from original)
    const searchForm = document.querySelector('.search-container form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.focus();
                // Optional: show validation error
                showErrorNotification('Please enter a search term');
            }
        });
    }
    
    // Add click handlers for dynamically loaded anime cards
    document.addEventListener('click', function(e) {
        const card = e.target.closest('.anime-card');
        if (card) {
            const animeId = card.dataset.animeId;
            if (animeId) {
                window.location.href = `/anime/${animeId}`;
            }
        }
    });
}

function setupCardHoverEffects() {
    // This works for both static and dynamically loaded cards
    document.addEventListener('mouseover', function(e) {
        const card = e.target.closest('.anime-card');
        if (card) {
            card.style.transform = 'translateY(-5px)';
            card.style.transition = 'transform 0.2s ease';
        }
    }, true);
    
    document.addEventListener('mouseout', function(e) {
        const card = e.target.closest('.anime-card');
        if (card) {
            card.style.transform = 'translateY(0)';
        }
    }, true);
}

// Helper Functions

async function fetchData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        showErrorNotification('Failed to load data. Please try again.');
        return null;
    }
}

function renderAnimeCards(containerId, animeList) {
    const container = document.getElementById(containerId);
    if (!container || !animeList) return;
    
    container.innerHTML = animeList.map(anime => `
        <div class="anime-card" data-anime-id="${anime.id}">
            <img src="${anime.image}" alt="${anime.title}" loading="lazy">
            <div class="anime-info">
                <h3>${anime.title}</h3>
                ${anime.description ? `<p>${anime.description.substring(0, 100)}...</p>` : ''}
            </div>
        </div>
    `).join('');
}

function renderTopSearches(containerId, searches) {
    const container = document.getElementById(containerId);
    if (!container || !searches) return;
    
    container.innerHTML = searches.map(search => `
        <li>
            <a href="/search?q=${encodeURIComponent(search.term)}">
                ${search.term}
            </a>
        </li>
    `).join('');
}

function renderTrendingPosts(containerId, posts) {
    const container = document.getElementById(containerId);
    if (!container || !posts) return;
    
    container.innerHTML = posts.map(post => `
        <div class="trending-post">
            <h4>${post.title}</h4>
            <div class="post-meta">
                <span class="category">${post.category}</span>
                <span class="time">${post.time_posted}</span>
                <span class="comments">${post.comment_count} comments</span>
            </div>
        </div>
    `).join('');
}

function showErrorNotification(message) {
    // Create or use existing notification system
    const notification = document.createElement('div');
    notification.className = 'error-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}