// Основные JavaScript функции для Clienterra CRM

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Автоматическое скрытие уведомлений
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                alert.classList.add('fade');
                setTimeout(() => alert.remove(), 300);
            }, 3000);
        }
    });

    // Подтверждение удаления
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Вы уверены, что хотите удалить этот элемент?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Автосохранение форм
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    autoSaveForms.forEach(form => {
        let saveTimeout;
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    autoSaveForm(form);
                }, 2000);
            });
        });
    });

    // Поиск в реальном времени
    const searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const target = document.querySelector(this.getAttribute('data-search-target'));
            const searchTerm = this.value.toLowerCase();
            const rows = target.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });
});

// Функция показа уведомлений
function showNotification(message, type = 'info', duration = 3000) {
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };

    const alertClass = alertTypes[type] || alertTypes['info'];
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        <i class="fas fa-${getIconForType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Получение иконки для типа уведомления
function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || icons['info'];
}

// Автосохранение формы
function autoSaveForm(form) {
    const formData = new FormData(form);
    const url = form.getAttribute('data-autosave-url') || form.action;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Auto-Save': 'true'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Изменения сохранены автоматически', 'success', 2000);
        }
    })
    .catch(error => {
        console.error('Ошибка автосохранения:', error);
    });
}

// Форматирование даты
function formatDate(dateString, options = {}) {
    const date = new Date(dateString);
    const defaultOptions = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return date.toLocaleDateString('ru-RU', { ...defaultOptions, ...options });
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success', 2000);
    }).catch(err => {
        console.error('Ошибка копирования:', err);
        showNotification('Ошибка копирования', 'error');
    });
}

// Валидация форм
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Загрузка данных с индикатором
function loadWithSpinner(element, url, options = {}) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<div class="text-center"><div class="loading"></div></div>';
    
    return fetch(url, options)
        .then(response => response.json())
        .then(data => {
            element.innerHTML = originalContent;
            return data;
        })
        .catch(error => {
            element.innerHTML = originalContent;
            throw error;
        });
}

// Экспорт данных
function exportData(data, filename, type = 'json') {
    let content, mimeType;
    
    switch (type) {
        case 'csv':
            content = convertToCSV(data);
            mimeType = 'text/csv';
            break;
        case 'json':
        default:
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            break;
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Конвертация в CSV
function convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

// Управление темой
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    showNotification(`Тема изменена на ${newTheme === 'dark' ? 'тёмную' : 'светлую'}`, 'info');
}

// Инициализация темы при загрузке
(function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();

// Функции для быстрых действий
function showNewClientModal() {
    showNotification('Функция добавления клиента будет доступна в следующем обновлении', 'info');
}

function exportClients() {
    showNotification('Экспорт данных будет доступен в следующем обновлении', 'info');
}

function showAnalytics() {
    showNotification('Детальная аналитика будет доступна в следующем обновлении', 'info');
}

function showSettings() {
    window.location.href = '/settings';
} 