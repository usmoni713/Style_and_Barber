// Конфигурация API
const API_BASE_URL = 'http://localhost:8000';

// Состояние приложения
const appState = {
    currentPage: 'home',
    currentStep: 1,
    bookingData: {
        salon_id: null,
        service_id: null,
        master_id: null,
        date: null,
        time: null
    },
    user: null,
    token: null
};

// Утилиты для работы с localStorage
const storage = {
    getToken: () => localStorage.getItem('access_token'),
    setToken: (token) => {
        localStorage.setItem('access_token', token);
        appState.token = token;
    },
    removeToken: () => {
        localStorage.removeItem('access_token');
        appState.token = null;
    },
    getUser: () => {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        appState.user = user;
        return user;
    },
    setUser: (user) => {
        localStorage.setItem('user', JSON.stringify(user));
        appState.user = user;
    },
    removeUser: () => {
        localStorage.removeItem('user');
        appState.user = null;
    }
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

// Навигация между страницами
function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`${pageName}Page`);
    if (targetPage) {
        targetPage.classList.add('active');
        appState.currentPage = pageName;
        updateNavigation();
        
        // Загружаем данные для страницы
        if (pageName === 'home') {
            loadSalonsPreview();
        } else if (pageName === 'profile') {
            if (storage.getToken()) {
                loadUserProfile();
                loadAppointments();
            } else {
                showPage('login');
            }
        } else if (pageName === 'booking') {
            if (!storage.getToken()) {
                if (confirm('Для записи необходимо войти в систему. Войти сейчас?')) {
                    showPage('login');
                } else {
                    showPage('home');
                }
                return;
            }
            resetBooking();
            loadBookingStep(1);
        }
    }
}

function updateNavigation() {
    const token = storage.getToken();
    const loginLink = document.getElementById('loginLink');
    const profileLink = document.getElementById('profileLink');
    const logoutLink = document.getElementById('logoutLink');
    
    if (token) {
        loginLink.style.display = 'none';
        profileLink.style.display = 'inline-block';
        logoutLink.style.display = 'inline-block';
    } else {
        loginLink.style.display = 'inline-block';
        profileLink.style.display = 'none';
        logoutLink.style.display = 'none';
    }
}

// Инициализация навигации
document.querySelectorAll('.nav-link[data-page]').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.dataset.page;
        if (page) {
            showPage(page);
        }
    });
});

document.getElementById('logoutLink')?.addEventListener('click', (e) => {
    e.preventDefault();
    storage.removeToken();
    storage.removeUser();
    showPage('home');
    updateNavigation();
});

// Обработка формы входа
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('loginError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');

    const formData = new FormData(e.target);
    
    try {
        const response = await fetch(`${API_BASE_URL}/signin`, {
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
            storage.setUser({ username: formData.get('username') });
            updateNavigation();
            showPage('profile');
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
        const data = await apiRequest('/api/v1/users/signup', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        if (data.data === 'User created successfully') {
            // После регистрации автоматически входим
            const loginResponse = await fetch(`${API_BASE_URL}/signin`, {
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
                updateNavigation();
                showPage('profile');
            }
        }
    } catch (error) {
        errorDiv.textContent = error.message || 'Ошибка регистрации';
        errorDiv.classList.add('show');
    }
});

// Переключение между формами входа и регистрации
document.getElementById('showRegister')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('loginForm').parentElement.style.display = 'none';
    document.getElementById('registerCard').style.display = 'block';
});

document.getElementById('showLogin')?.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('loginForm').parentElement.style.display = 'block';
    document.getElementById('registerCard').style.display = 'none';
});

// Загрузка салонов для главной страницы
async function loadSalonsPreview() {
    try {
        const data = await apiRequest('/salons');
        const container = document.getElementById('salonsPreview');
        
        if (data.salons && data.salons.length > 0) {
            container.innerHTML = data.salons.map(salon => `
                <div class="salon-card">
                    <h3>${salon.title}</h3>
                    <p><strong>Адрес:</strong> ${salon.address}</p>
                    <p><strong>Телефон:</strong> ${salon.phone || 'Не указан'}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p>Информация о салонах временно недоступна</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки салонов:', error);
        document.getElementById('salonsPreview').innerHTML = '<p>Ошибка загрузки информации о салонах</p>';
    }
}

// Процесс записи
function resetBooking() {
    appState.currentStep = 1;
    appState.bookingData = {
        salon_id: null,
        service_id: null,
        master_id: null,
        date: null,
        time: null
    };
}

function updateBookingSteps() {
    document.querySelectorAll('.step').forEach((step, index) => {
        const stepNum = index + 1;
        if (stepNum < appState.currentStep) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (stepNum === appState.currentStep) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
}

async function loadBookingStep(step) {
    appState.currentStep = step;
    updateBookingSteps();
    
    // Скрываем все шаги
    document.querySelectorAll('.booking-step-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Показываем текущий шаг
    const currentStepElement = document.getElementById(`step${step}`);
    if (currentStepElement) {
        currentStepElement.style.display = 'block';
    }
    
    // Показываем/скрываем кнопку "Назад"
    const prevBtn = document.getElementById('prevBtn');
    if (prevBtn) {
        prevBtn.style.display = step > 1 ? 'block' : 'none';
    }
    
    // Загружаем данные для шага
    switch(step) {
        case 1:
            await loadSalonsForBooking();
            break;
        case 2:
            await loadServicesForBooking();
            break;
        case 3:
            await loadMastersForBooking();
            break;
        case 4:
            setupDatePicker();
            break;
        case 5:
            showBookingSummary();
            break;
    }
}

// Шаг 1: Загрузка салонов
async function loadSalonsForBooking() {
    const container = document.getElementById('salonsList');
    container.innerHTML = '<p class="loading">Загрузка салонов...</p>';
    
    try {
        const data = await apiRequest('/salons');
        if (data.salons && data.salons.length > 0) {
            container.innerHTML = data.salons.map(salon => `
                <div class="salon-card selectable" data-salon-id="${salon.id}">
                    <h3>${salon.title}</h3>
                    <p><strong>Адрес:</strong> ${salon.address}</p>
                    <p><strong>Телефон:</strong> ${salon.phone || 'Не указан'}</p>
                </div>
            `).join('');
            
            // Добавляем обработчики клика
            container.querySelectorAll('.salon-card.selectable').forEach(card => {
                card.addEventListener('click', () => {
                    const salonId = parseInt(card.dataset.salonId);
                    appState.bookingData.salon_id = salonId;
                    card.classList.add('selected');
                    container.querySelectorAll('.salon-card').forEach(c => {
                        if (c !== card) c.classList.remove('selected');
                    });
                    setTimeout(() => loadBookingStep(2), 500);
                });
            });
        } else {
            container.innerHTML = '<p>Салонов не найдено</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">Ошибка загрузки: ${error.message}</p>`;
    }
}

// Шаг 2: Загрузка услуг
async function loadServicesForBooking() {
    const container = document.getElementById('servicesList');
    container.innerHTML = '<p class="loading">Загрузка услуг...</p>';
    
    try {
        const data = await apiRequest(`/services?salon_id=${appState.bookingData.salon_id}`);
        if (data.services && data.services.length > 0) {
            container.innerHTML = data.services.map(service => `
                <div class="service-card selectable" data-service-id="${service.id}">
                    <h3>${service.description || 'Услуга'}</h3>
                    <p><strong>Продолжительность:</strong> ${service.duration_minutes} мин</p>
                    <p><strong>Цена:</strong> ${service.base_price}₽</p>
                </div>
            `).join('');
            
            container.querySelectorAll('.service-card.selectable').forEach(card => {
                card.addEventListener('click', () => {
                    const serviceId = parseInt(card.dataset.serviceId);
                    appState.bookingData.service_id = serviceId;
                    card.classList.add('selected');
                    container.querySelectorAll('.service-card').forEach(c => {
                        if (c !== card) c.classList.remove('selected');
                    });
                    setTimeout(() => loadBookingStep(3), 500);
                });
            });
        } else {
            container.innerHTML = '<p>Услуг не найдено</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">Ошибка загрузки: ${error.message}</p>`;
    }
}

// Шаг 3: Загрузка мастеров
async function loadMastersForBooking() {
    const container = document.getElementById('mastersList');
    const anyMasterRadio = document.getElementById('anyMaster');
    
    container.innerHTML = '<p class="loading">Загрузка мастеров...</p>';
    
    try {
        const data = await apiRequest(`/masters?salon_id=${appState.bookingData.salon_id}&service_id=${appState.bookingData.service_id}`);
        
        if (data.masters && data.masters.length > 0) {
            container.innerHTML = data.masters.map(master => `
                <div class="master-card selectable" data-master-id="${master.id}">
                    <h3>${master.specialization || 'Мастер'}</h3>
                    <p>${master.about || 'Профессиональный мастер'}</p>
                </div>
            `).join('');
            
            container.querySelectorAll('.master-card.selectable').forEach(card => {
                card.addEventListener('click', () => {
                    const masterId = parseInt(card.dataset.masterId);
                    appState.bookingData.master_id = masterId;
                    anyMasterRadio.checked = false;
                    card.classList.add('selected');
                    container.querySelectorAll('.master-card').forEach(c => {
                        if (c !== card) c.classList.remove('selected');
                    });
                    setTimeout(() => loadBookingStep(4), 500);
                });
            });
            
            anyMasterRadio.addEventListener('change', () => {
                if (anyMasterRadio.checked) {
                    appState.bookingData.master_id = null;
                    container.querySelectorAll('.master-card').forEach(c => c.classList.remove('selected'));
                    setTimeout(() => loadBookingStep(4), 500);
                }
            });
        } else {
            container.innerHTML = '<p>Мастеров не найдено</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">Ошибка загрузки: ${error.message}</p>`;
    }
}

// Шаг 4: Выбор даты и времени
function setupDatePicker() {
    const dateInput = document.getElementById('appointmentDate');
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    dateInput.min = tomorrow.toISOString().split('T')[0];
    dateInput.value = '';
    
    dateInput.addEventListener('change', async (e) => {
        const selectedDate = e.target.value;
        if (selectedDate) {
            appState.bookingData.date = selectedDate;
            await loadTimeSlots(selectedDate);
        }
    });
}

async function loadTimeSlots(dateStr) {
    const container = document.getElementById('timeSlots');
    container.innerHTML = '<p class="loading">Загрузка доступного времени...</p>';
    
    try {
        const response = await apiRequest(`/free_slots?salon_id=${appState.bookingData.salon_id}&service_id=${appState.bookingData.service_id}&target_date=${dateStr}${appState.bookingData.master_id ? `&master_id=${appState.bookingData.master_id}` : ''}`);
        
        if (response.slots && response.slots.length > 0) {
            let allSlots = [];
            response.slots.forEach(masterSlot => {
                if (masterSlot.slots && masterSlot.slots.length > 0) {
                    masterSlot.slots.forEach(slot => {
                        allSlots.push({
                            ...slot,
                            master_id: masterSlot.master_id
                        });
                    });
                }
            });
            
            // Сортируем слоты по времени
            allSlots.sort((a, b) => new Date(a.start) - new Date(b.start));
            
            if (allSlots.length > 0) {
                container.innerHTML = `
                    <h3>Доступное время:</h3>
                    <div class="time-grid">
                        ${allSlots.map(slot => {
                            const startTime = new Date(slot.start);
                            const endTime = new Date(slot.end);
                            const timeStr = `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')} - ${endTime.getHours().toString().padStart(2, '0')}:${endTime.getMinutes().toString().padStart(2, '0')}`;
                            return `
                                <button class="time-slot-btn" data-start="${slot.start}" data-master-id="${slot.master_id}">
                                    ${timeStr}
                                </button>
                            `;
                        }).join('')}
                    </div>
                `;
                
                container.querySelectorAll('.time-slot-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        appState.bookingData.time = btn.dataset.start;
                        if (!appState.bookingData.master_id && btn.dataset.masterId) {
                            appState.bookingData.master_id = parseInt(btn.dataset.masterId);
                        }
                        container.querySelectorAll('.time-slot-btn').forEach(b => b.classList.remove('selected'));
                        btn.classList.add('selected');
                        setTimeout(() => loadBookingStep(5), 500);
                    });
                });
            } else {
                container.innerHTML = '<p>На выбранную дату нет свободного времени</p>';
            }
        } else {
            container.innerHTML = '<p>На выбранную дату нет свободного времени</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">Ошибка загрузки: ${error.message}</p>`;
    }
}

// Шаг 5: Подтверждение
async function showBookingSummary() {
    const summaryDiv = document.getElementById('bookingSummary');
    const userDataFields = document.getElementById('userDataFields');
    
    // Загружаем данные для отображения
    const [salonsData, servicesData, mastersData] = await Promise.all([
        apiRequest('/salons'),
        apiRequest('/services'),
        apiRequest(`/masters?salon_id=${appState.bookingData.salon_id}`)
    ]);
    
    const salon = salonsData.salons.find(s => s.id === appState.bookingData.salon_id);
    const service = servicesData.services.find(s => s.id === appState.bookingData.service_id);
    const master = appState.bookingData.master_id ? mastersData.masters.find(m => m.id === appState.bookingData.master_id) : null;
    
    const dateTime = new Date(appState.bookingData.time);
    const dateStr = dateTime.toLocaleDateString('ru-RU');
    const timeStr = dateTime.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    
    summaryDiv.innerHTML = `
        <div class="summary-item">
            <strong>Салон:</strong> ${salon?.title || 'Не выбран'}
        </div>
        <div class="summary-item">
            <strong>Услуга:</strong> ${service?.description || 'Не выбрана'} (${service?.duration_minutes} мин, ${service?.base_price}₽)
        </div>
        <div class="summary-item">
            <strong>Мастер:</strong> ${master ? (master.specialization || 'Мастер') : 'Любой свободный'}
        </div>
        <div class="summary-item">
            <strong>Дата и время:</strong> ${dateStr} в ${timeStr}
        </div>
    `;
    
    // Поля для данных пользователя уже заполнены, так как пользователь авторизован
    userDataFields.innerHTML = '<p>Данные будут взяты из вашего профиля</p>';
}

// Обработка формы подтверждения записи
document.getElementById('bookingForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorDiv = document.getElementById('bookingError');
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');
    
    const comment = document.getElementById('bookingComment').value;
    
    const appointmentData = {
        salon_id: appState.bookingData.salon_id,
        master_id: appState.bookingData.master_id,
        service_id: appState.bookingData.service_id,
        date_time: appState.bookingData.time,
        comment: comment || null
    };
    
    try {
        const data = await apiRequest('/api/v1/users/appointments', {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
        
        // Показываем страницу успеха
        appState.currentStep = 6;
        updateBookingSteps();
        document.querySelectorAll('.booking-step-content').forEach(content => {
            content.style.display = 'none';
        });
        const successPage = document.getElementById('step6');
        successPage.style.display = 'block';
        
        // Заполняем детали успеха
        const successDetails = document.getElementById('successDetails');
        const dateTime = new Date(appointmentData.date_time);
        successDetails.innerHTML = `
            <p><strong>Номер записи:</strong> #${data.appointment?.id || 'N/A'}</p>
            <p><strong>Дата и время:</strong> ${dateTime.toLocaleString('ru-RU')}</p>
            <p>Запись успешно создана! Мы отправили вам подтверждение.</p>
        `;
        
    } catch (error) {
        errorDiv.textContent = error.message || 'Ошибка создания записи';
        errorDiv.classList.add('show');
    }
});

// Кнопка "Назад" в процессе записи
document.getElementById('prevBtn')?.addEventListener('click', () => {
    if (appState.currentStep > 1) {
        loadBookingStep(appState.currentStep - 1);
    }
});

// Загрузка профиля пользователя
async function loadUserProfile() {
    const container = document.getElementById('userProfileInfo');
    const user = storage.getUser();
    
    container.innerHTML = `
        <p><strong>Email/Телефон:</strong> ${user.username || 'Не указан'}</p>
        <p><strong>Имя:</strong> ${user.name || 'Не указано'}</p>
    `;
}

// Загрузка записей пользователя
async function loadAppointments() {
    const listDiv = document.getElementById('appointmentsList');
    listDiv.innerHTML = '<p class="loading">Загрузка...</p>';

    try {
        const data = await apiRequest('/api/v1/users/appointments');
        const appointments = data.appointments || [];

        if (appointments.length === 0) {
            listDiv.innerHTML = '<div class="empty-state">У вас пока нет записей</div>';
            return;
        }

        listDiv.innerHTML = appointments.map(apt => {
            const isPast = new Date(apt.date_time) < new Date();
            const canCancel = apt.status && !isPast;
            const dateTime = new Date(apt.date_time);
            const endTime = new Date(apt.end_time);
            
            return `
            <div class="appointment-item">
                <h3>Запись #${apt.id}</h3>
                <p><strong>Дата и время:</strong> ${formatDateTime(apt.date_time)}</p>
                <p><strong>Окончание:</strong> ${formatDateTime(apt.end_time)}</p>
                <p><strong>Салон ID:</strong> ${apt.salon_id}</p>
                <p><strong>Мастер ID:</strong> ${apt.master_id}</p>
                <p><strong>Услуга ID:</strong> ${apt.service_id}</p>
                ${apt.comment ? `<p><strong>Комментарий:</strong> ${apt.comment}</p>` : ''}
                <div class="appointment-actions">
                    <span class="status ${apt.status ? 'active' : 'cancelled'}">
                        ${apt.status ? 'Подтверждена' : 'Отменена'}
                    </span>
                    ${canCancel ? `
                        <button class="btn btn-cancel" onclick="cancelAppointment(${apt.id})">
                            Отменить запись
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        }).join('');
    } catch (error) {
        listDiv.innerHTML = `<div class="error-message show">Ошибка загрузки: ${error.message}</div>`;
    }
}

// Отмена записи
window.cancelAppointment = async function(appointmentId) {
    if (!confirm('Вы уверены, что хотите отменить эту запись?')) {
        return;
    }

    try {
        await apiRequest(`/api/v1/users/appointments/${appointmentId}`, {
            method: 'DELETE'
        });

        alert('Запись успешно отменена');
        loadAppointments();
    } catch (error) {
        alert('Ошибка при отмене записи: ' + error.message);
        console.error('Ошибка отмены записи:', error);
    }
}

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

// Инициализация при загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
    const token = storage.getToken();
    if (token) {
        storage.getUser();
        updateNavigation();
    }
    
    // Обработка ссылок на страницу успеха
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.dataset.page) {
                e.preventDefault();
                showPage(link.dataset.page);
            }
        });
    });
    
    showPage('home');
});
