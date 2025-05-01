document.addEventListener('DOMContentLoaded', function() {
    // Only connect if user is authenticated
    if (document.body.dataset.userAuthenticated === 'true') {
        const notificationSocket = new WebSocket(
            'ws://' + window.location.host + '/ws/notifications/'
        );

        notificationSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.type === 'notification') {
                const notification = data.notification;
                showNotification(notification);
                updateNotificationBadge();
            }
        };

        notificationSocket.onclose = function(e) {
            console.error('Notification socket closed unexpectedly');
        };
    }
});

function showNotification(notification) {
    // Create notification element
    const toastHtml = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-notification-id="${notification.id}">
            <div class="toast-header">
                <strong class="me-auto">${notification.title}</strong>
                <small class="text-muted">just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${notification.message}
                ${notification.content_object ? 
                    `<br><a href="${notification.content_object.url}" class="btn btn-sm btn-primary mt-2">View Details</a>` 
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
