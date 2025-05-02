document.addEventListener('DOMContentLoaded', function() {
    // Initialize notifications
    initializeNotifications();
});

function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }

    // Initialize unread badge
    updateNotificationBadge();
}

// Create audio context for critical alerts
let audioContext = null;

function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
}

function playAlertSound() {
    if (!audioContext) return;
    
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5 note
    
    gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

function showNotification(notification) {
    const isCritical = notification.notification_type === 'critical';
    
    // Play sound for critical notifications
    if (isCritical) {
        initAudioContext();
        playAlertSound();
    }
    
    // Create notification element
    const toastHtml = `
        <div class="toast ${isCritical ? 'critical' : ''}" 
             role="alert" 
             aria-live="${isCritical ? 'assertive' : 'polite'}" 
             aria-atomic="true" 
             data-notification-id="${notification.id}">
            <div class="toast-header">
                ${isCritical ? '<i class="fas fa-exclamation-triangle me-2"></i>' : ''}
                <strong class="me-auto">
                    ${isCritical ? '⚠️ CRITICAL ALERT' : notification.title}
                </strong>
                <small class="${isCritical ? 'text-white' : 'text-muted'}">just now</small>
                <button type="button" 
                        class="btn-close" 
                        data-bs-dismiss="toast" 
                        aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${isCritical ? '<strong>' : ''}
                ${notification.message}
                ${isCritical ? '</strong>' : ''}
                ${notification.link ? 
                    `<div class="mt-2 pt-2 ${isCritical ? 'border-top border-danger' : 'border-top'}">
                        <a href="${notification.link}" 
                           class="btn ${isCritical ? 'btn-danger' : 'btn-primary'} btn-sm">
                           <i class="fas fa-${isCritical ? 'ambulance' : 'eye'} me-1"></i>
                           View Patient
                        </a>
                    </div>` 
                    : ''}
            </div>
        </div>
    `;

    // Add to notification container
    const container = document.getElementById('notification-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'notification-container';
        newContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(newContainer);
    }

    // Add toast to container
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    document.getElementById('notification-container').appendChild(toastElement.firstChild);

    // Initialize and show toast
    const toast = new bootstrap.Toast(document.getElementById('notification-container').lastChild);
    toast.show();

    // Mark as read when clicked
    toastElement.querySelector('.toast').addEventListener('click', function() {
        markNotificationAsRead(notification.id);
    });
}

function markNotificationAsRead(notificationId) {
    fetch(`/notifications/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    }).then(response => {
        if (response.ok) {
            updateNotificationBadge();
        }
    });
}

function updateNotificationBadge() {
    fetch('/notifications/unread-count/')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                badge.textContent = data.count;
                badge.style.display = data.count > 0 ? 'inline' : 'none';
            }
        });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
