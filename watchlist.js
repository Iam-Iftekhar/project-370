// Function to handle adding to watchlist
async function addToWatchlist(button) {
    const animeId = button.getAttribute('data-anime-id');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
    
    try {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        
        const response = await fetch('/watchlist/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ anime_id: animeId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update button state
            button.innerHTML = '<i class="fas fa-check"></i> In Watchlist';
            button.classList.remove('btn-primary');
            button.classList.add('btn-success');
            
            // Update watchlist count
            updateWatchlistCount(data.watchlist_count);
            
            // Show toast notification
            showToast('Added to your watchlist!');
        } else {
            throw new Error(data.message || 'Failed to add to watchlist');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message, 'error');
        button.innerHTML = '<i class="fas fa-plus"></i> Add to Watchlist';
        button.disabled = false;
    }
}

// Function to update watchlist count
function updateWatchlistCount(count) {
    const countElement = document.getElementById('watchlistCount');
    if (countElement) {
        countElement.textContent = count;
        countElement.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

// Function to show toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast show position-fixed bottom-0 end-0 m-3 bg-${type} text-white`;
    toast.style.zIndex = '1100';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize watchlist count on page load
document.addEventListener('DOMContentLoaded', () => {
    fetch('/watchlist/count')
        .then(response => response.json())
        .then(data => updateWatchlistCount(data.count))
        .catch(error => console.error('Error fetching watchlist count:', error));
});