// Переключение вкладок авторизации
function showLogin() {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function showRegister() {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

// Переключение вкладок админ-панели
function showAdminTab(tabName) {
    document.querySelectorAll('.admin-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

// Автозакрытие сообщений
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});

// Подтверждение удаления из корзины
const removeButtons = document.querySelectorAll('.remove-btn');
removeButtons.forEach(button => {
    button.addEventListener('click', function(e) {
        if(!confirm('Вы уверены, что хотите удалить этот товар?')) {
            e.preventDefault();
        }
    });
});

// Валидация формы оформления заказа
const checkoutForm = document.querySelector('.checkout-section form');
if(checkoutForm) {
    checkoutForm.addEventListener('submit', function(e) {
        const address = this.querySelector('[name="address"]').value;
        const phone = this.querySelector('[name="phone"]').value;
        
        if(address.length < 10) {
            e.preventDefault();
            alert('Пожалуйста, введите полный адрес доставки');
        }
        
        if(phone.length < 10) {
            e.preventDefault();
            alert('Пожалуйста, введите корректный номер телефона');
        }
    });
}
// Фильтрация каталога через AJAX (опционально)
document.addEventListener('DOMContentLoaded', function() {
    const categoryFilter = document.getElementById('category-filter');
    const sortFilter = document.getElementById('sort-filter');
    
    if (categoryFilter && sortFilter) {
        // Можно добавить AJAX-запрос вместо перезагрузки страницы
        // Но текущая реализация с form.submit() тоже работает хорошо
    }
});