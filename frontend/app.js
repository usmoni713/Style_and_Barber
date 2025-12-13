// Конфигурация API
const API_BASE_URL = 'http://localhost:8000';

// Утилиты для работы с localStorage
const storage = {
    getToken: () => localStorage.getItem('access_token'),
    setToken: (token) => localStorage.setItem('access_token', token),
    removeToken: () => localStorage.removeItem('access_token'),
    getUser: () => JSON.parse(localStorage.getItem('user') || '{}'),
    setUser: (user) => localStorage.setItem('user', JSON.stringify(user)),
    removeUser: () => localStorage.removeItem('user')
};

// Функция для выполнения API запросов
async function apiRequest(url, options = {}) {
    const token = storage.getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка запроса');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Обработка формы входа
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('loginError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');

    const formData = new FormData(e.target);
    
    // OAuth2 требует form-data, а не JSON
    try {
        const response = await fetch(`${API_BASE_URL}/singin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: formData.get('username'),
                password: formData.get('password')
            })
        });

        const data = await response.json();

        if (response.ok) {
            storage.setToken(data.access_token);
            // Получаем информацию о пользователе (можно добавить отдельный эндпоинт)
            storage.setUser({ username: formData.get('username') });
            showMainContent();
            loadAppointments();
        } else {
            errorDiv.textContent = data.detail || 'Ошибка входа';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Ошибка подключения к серверу';
        errorDiv.classList.add('show');
    }
});

// Обработка формы регистрации
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('registerError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');

    const formData = new FormData(e.target);
    const userData = {
        name: formData.get('name'),
        lastname: formData.get('lastname') || null,
        email: formData.get('email'),
        phone: formData.get('phone') || null,
        password: formData.get('password')
    };

    try {
        const data = await apiRequest('/singup', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        if (data.data === 'User created successfully') {
            // После регистрации автоматически входим
            const loginResponse = await fetch(`${API_BASE_URL}/singin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: userData.email,
                    password: userData.password
                })
            });

            const loginData = await loginResponse.json();
            if (loginResponse.ok) {
                storage.setToken(loginData.access_token);
                storage.setUser({ username: userData.email, name: userData.name });
                showMainContent();
                loadAppointments();
            }
        }
    } catch (error) {
        errorDiv.textContent = error.message || 'Ошибка регистрации';
        errorDiv.classList.add('show');
    }
});

// Переключение между формами входа и регистрации
document.getElementById('showLogin')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('registerSection').style.display = 'none';
});

// Показать форму регистрации (можно добавить кнопку "Регистрация" на форме входа)
// Для упрощения добавим ссылку в форму входа
if (!document.querySelector('#loginSection a[href="#register"]')) {
    const loginSection = document.getElementById('loginSection');
    const registerLink = document.createElement('p');
    registerLink.className = 'switch-form';
    registerLink.innerHTML = 'Нет аккаунта? <a href="#" id="showRegister">Зарегистрироваться</a>';
    loginSection.appendChild(registerLink);
    
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('registerSection').style.display = 'block';
    });
}

// Выход из системы
document.getElementById('logoutBtn')?.addEventListener('click', () => {
    storage.removeToken();
    storage.removeUser();
    showLoginForm();
});

// Показать основной контент
function showMainContent() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'none';
    const mainContent = document.getElementById('mainContent');
    mainContent.style.display = 'block';
    
    const user = storage.getUser();
    if (user.name) {
        document.getElementById('userName').textContent = `Привет, ${user.name}!`;
    } else {
        document.getElementById('userName').textContent = `Привет, ${user.username || 'Пользователь'}!`;
    }
    
    // Инициализируем обработчики вкладок после того, как контент стал видимым
    // Используем небольшую задержку для гарантии обновления DOM
    setTimeout(() => {
        initTabs();
    }, 10);
    
    // Загружаем данные для формы создания записи
    loadSalons();
    loadServices();
}

// Показать форму входа
function showLoginForm() {
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
}

// Функция для инициализации переключения вкладок
function initTabs() {
    // Находим все кнопки вкладок
    const tabButtons = document.querySelectorAll('.tab-btn');
    console.log('Инициализация вкладок, найдено кнопок:', tabButtons.length);
    
    if (tabButtons.length === 0) {
        console.warn('Кнопки вкладок не найдены!');
        return;
    }
    
    tabButtons.forEach(btn => {
        // Проверяем, не добавлен ли уже обработчик
        if (btn.dataset.handlerAttached === 'true') {
            return; // Обработчик уже добавлен
        }
        
        // Добавляем обработчик
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const tabName = this.dataset.tab;
            console.log('Клик по вкладке:', tabName);
            
            // Убираем активный класс со всех кнопок и контента
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Добавляем активный класс выбранным
            this.classList.add('active');
            
            // Преобразуем имя вкладки в ID
            // appointments -> appointmentsTab
            // new-appointment -> newAppointmentTab
            let tabId;
            if (tabName === 'new-appointment') {
                tabId = 'newAppointmentTab';
            } else {
                // Для других вкладок просто добавляем Tab с заглавной буквы
                tabId = tabName + 'Tab';
            }
            
            const tabContent = document.getElementById(tabId);
            if (tabContent) {
                tabContent.classList.add('active');
                console.log('Вкладка активирована:', tabName, '->', tabId);
            } else {
                console.error('Контент вкладки не найден:', tabId);
            }
            
            // Если открыли вкладку создания записи, загружаем данные
            if (tabName === 'new-appointment') {
                console.log('Загрузка данных для новой записи...');
                loadSalons();
                loadServices();
            }
        });
        
        // Помечаем, что обработчик добавлен
        btn.dataset.handlerAttached = 'true';
        console.log('Обработчик добавлен для вкладки:', btn.dataset.tab);
    });
}

// Загрузка списка записей
async function loadAppointments() {
    const listDiv = document.getElementById('appointmentsList');
    listDiv.innerHTML = '<p class="loading">Загрузка...</p>';

    try {
        const data = await apiRequest('/appointments');
        const appointments = data.appointments || [];

        if (appointments.length === 0) {
            listDiv.innerHTML = '<div class="empty-state">У вас пока нет записей</div>';
            return;
        }

        listDiv.innerHTML = appointments.map(apt => `
            <div class="appointment-item">
                <h3>Запись #${apt.id}</h3>
                <p><strong>Дата и время:</strong> ${formatDateTime(apt.date_time)}</p>
                <p><strong>Окончание:</strong> ${formatDateTime(apt.end_time)}</p>
                <p><strong>Салон ID:</strong> ${apt.salon_id}</p>
                <p><strong>Мастер ID:</strong> ${apt.master_id}</p>
                <p><strong>Услуга ID:</strong> ${apt.service_id}</p>
                ${apt.comment ? `<p><strong>Комментарий:</strong> ${apt.comment}</p>` : ''}
                <span class="status ${apt.status ? 'active' : 'cancelled'}">
                    ${apt.status ? 'Подтверждена' : 'Отменена'}
                </span>
            </div>
        `).join('');
    } catch (error) {
        listDiv.innerHTML = `<div class="error-message show">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Загрузка салонов
async function loadSalons() {
    try {
        const data = await apiRequest('/salons');
        const select = document.getElementById('salonSelect');
        select.innerHTML = '<option value="">Выберите салон...</option>';
        
        data.salons.forEach(salon => {
            const option = document.createElement('option');
            option.value = salon.id;
            option.textContent = `${salon.title} - ${salon.address}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки салонов:', error);
    }
}

// Загрузка услуг
async function loadServices() {
    try {
        const data = await apiRequest('/services');
        const select = document.getElementById('serviceSelect');
        select.innerHTML = '<option value="">Выберите услугу...</option>';
        
        data.services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.description} - ${service.base_price}₽ (${service.duration_minutes} мин)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка загрузки услуг:', error);
    }
}

// Загрузка мастеров при выборе салона
document.getElementById('salonSelect')?.addEventListener('change', async (e) => {
    const salonId = e.target.value;
    const masterSelect = document.getElementById('masterSelect');
    masterSelect.innerHTML = '<option value="">Выберите мастера...</option>';

    if (salonId) {
        try {
            const data = await apiRequest(`/masters?salon_id=${salonId}`);
            data.masters.forEach(master => {
                const option = document.createElement('option');
                option.value = master.id;
                option.textContent = `${master.specialization} - ${master.about || 'Мастер'}`;
                masterSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка загрузки мастеров:', error);
        }
    }
});

// Обработка формы создания записи
document.getElementById('newAppointmentForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('appointmentError');
    const successDiv = document.getElementById('appointmentSuccess');
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');
    successDiv.textContent = '';
    successDiv.classList.remove('show');

    const formData = new FormData(e.target);
    const appointmentData = {
        salon_id: parseInt(formData.get('salon_id')),
        master_id: parseInt(formData.get('master_id')),
        service_id: parseInt(formData.get('service_id')),
        date_time: formData.get('date_time'),
        comment: formData.get('comment') || null
    };

    try {
        const data = await apiRequest('/appointments/add', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });

        successDiv.textContent = 'Запись успешно создана!';
        successDiv.classList.add('show');
        
        // Очищаем форму
        e.target.reset();
        
        // Переключаемся на вкладку с записями и обновляем список
        document.querySelector('.tab-btn[data-tab="appointments"]').click();
        loadAppointments();
    } catch (error) {
        errorDiv.textContent = error.message || 'Ошибка создания записи';
        errorDiv.classList.add('show');
    }
});

// Форматирование даты и времени
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'Не указано';
    const date = new Date(dateTimeString);
    return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Проверка авторизации при загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
    const token = storage.getToken();
    if (token) {
        showMainContent();
        loadAppointments();
    } else {
        showLoginForm();
    }
});

