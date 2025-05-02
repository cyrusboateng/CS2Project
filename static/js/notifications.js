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
    
    // Create oscillators for a more intense siren sound
    const oscillators = [];
    const gainNodes = [];
    
    // Create multiple oscillators for a richer sound
    for (let i = 0; i < 3; i++) {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillators.push(oscillator);
        gainNodes.push(gainNode);
    }
    
    // High-pitched siren
    oscillators[0].type = 'sawtooth';
    oscillators[0].frequency.setValueAtTime(880, audioContext.currentTime);
    oscillators[0].frequency.linearRampToValueAtTime(1760, audioContext.currentTime + 0.25);
    oscillators[0].frequency.linearRampToValueAtTime(880, audioContext.currentTime + 0.5);
    
    // Mid-range harmonics
    oscillators[1].type = 'square';
    oscillators[1].frequency.setValueAtTime(440, audioContext.currentTime);
    oscillators[1].frequency.linearRampToValueAtTime(880, audioContext.currentTime + 0.25);
    oscillators[1].frequency.linearRampToValueAtTime(440, audioContext.currentTime + 0.5);
    
    // Low-frequency punch
    oscillators[2].type = 'triangle';
    oscillators[2].frequency.setValueAtTime(220, audioContext.currentTime);
    oscillators[2].frequency.linearRampToValueAtTime(110, audioContext.currentTime + 0.5);
    
    // Volume envelopes
    gainNodes.forEach((gainNode, i) => {
        gainNode.gain.setValueAtTime(0, audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.2 / (i + 1), audioContext.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.2 / (i + 1), audioContext.currentTime + 0.4);
        gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.5);
    });
    
    // Play all oscillators
    oscillators.forEach(osc => osc.start(audioContext.currentTime));
    oscillators.forEach(osc => osc.stop(audioContext.currentTime + 0.5));
    
    // Schedule second siren after a short delay
    setTimeout(() => {
        const oscillators2 = [];
        const gainNodes2 = [];
        
        for (let i = 0; i < 3; i++) {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillators2.push(oscillator);
            gainNodes2.push(gainNode);
        }
        
        // Reverse siren sweep
        oscillators2[0].type = 'sawtooth';
        oscillators2[0].frequency.setValueAtTime(1760, audioContext.currentTime);
        oscillators2[0].frequency.linearRampToValueAtTime(880, audioContext.currentTime + 0.25);
        oscillators2[0].frequency.linearRampToValueAtTime(1760, audioContext.currentTime + 0.5);
        
        oscillators2[1].type = 'square';
        oscillators2[1].frequency.setValueAtTime(880, audioContext.currentTime);
        oscillators2[1].frequency.linearRampToValueAtTime(440, audioContext.currentTime + 0.25);
        oscillators2[1].frequency.linearRampToValueAtTime(880, audioContext.currentTime + 0.5);
        
        oscillators2[2].type = 'triangle';
        oscillators2[2].frequency.setValueAtTime(110, audioContext.currentTime);
        oscillators2[2].frequency.linearRampToValueAtTime(220, audioContext.currentTime + 0.5);
        
        gainNodes2.forEach((gainNode, i) => {
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.2 / (i + 1), audioContext.currentTime + 0.1);
            gainNode.gain.setValueAtTime(0.2 / (i + 1), audioContext.currentTime + 0.4);
            gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.5);
        });
        
        oscillators2.forEach(osc => osc.start(audioContext.currentTime));
        oscillators2.forEach(osc => osc.stop(audioContext.currentTime + 0.5));
    }, 600);
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
        <div class="toast ${isCritical ? 'emergency-pulse' : ''}" 
             role="alert" 
             aria-live="${isCritical ? 'assertive' : 'polite'}" 
             aria-atomic="true" 
             data-notification-id="${notification.id}">
            <div class="toast-header ${isCritical ? 'emergency-header emergency-stripes' : ''}">
                ${isCritical ? '<i class="fas fa-exclamation-triangle me-2 emergency-shake"></i>' : ''}
                <strong class="me-auto text-white">
                    ${isCritical ? `<span class="fs-5 text-uppercase emergency-shake d-inline-block">⚠️ EMERGENCY ALERT</span>` : notification.title}
                </strong>
                <small class="text-white-50">just now</small>
                <button type="button" 
                        class="btn-close btn-close-white" 
                        data-bs-dismiss="toast" 
                        aria-label="Close"></button>
            </div>
            <div class="toast-body ${isCritical ? 'bg-danger bg-opacity-10 border-start border-danger border-4' : ''}">
                ${isCritical ? '<strong class="fs-5">' : ''}
                ${notification.message}
                ${isCritical ? '</strong>' : ''}
                ${notification.link ? 
                    `<div class="mt-3 pt-3 ${isCritical ? 'border-top border-danger' : 'border-top'}">
                        <a href="${notification.link}" 
                           class="btn ${isCritical ? 'btn-danger' : 'btn-primary'} ${isCritical ? 'emergency-shake' : ''} w-100">
                           <i class="fas fa-${isCritical ? 'ambulance' : 'eye'} me-2"></i>
                           <strong>View Critical Patient</strong>
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

function setupWebSocket() {
    const socket = new WebSocket('ws://' + window.location.host + '/ws/notifications/');

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
            showNotification(data.notification);
        }
    };

    document.querySelectorAll('.toast').forEach(toast => {
        toast.addEventListener('hidden.bs.toast', function() {
            const notificationId = this.getAttribute('data-notification-id');
            if (notificationId) {
                socket.send(JSON.stringify({type: 'read', notification_id: notificationId}));
            }
        });
    });
}

setupWebSocket();
