

document.addEventListener('DOMContentLoaded', function() {
    // Валидация полей цены
    const priceMin = document.querySelector('input[name="price_min"]');
    const priceMax = document.querySelector('input[name="price_max"]');
    
    function validatePriceInput(input) {
        if (!input) return;
        // Удаляем все не-цифры
        input.value = input.value.replace(/[^\d]/g, '');
        
        // Ограничиваем максимальное значение (например, 1,000,000)
        const maxValue = 1000000;
        if (parseInt(input.value) > maxValue) {
            input.value = maxValue;
        }
    }
    
    if (priceMin) {
        priceMin.addEventListener('input', function(e) {
            validatePriceInput(this);
        });
        
        priceMin.addEventListener('blur', function() {
            if (this.value) {
                // Убираем лидирующие нули
                this.value = parseInt(this.value) || '';
            }
        });
    }
    
    if (priceMax) {
        priceMax.addEventListener('input', function(e) {
            validatePriceInput(this);
        });
        
        priceMax.addEventListener('blur', function() {
            if (this.value) {
                // Убираем лидирующие нули
                this.value = parseInt(this.value) || '';
            }
        });
    }
    
    // Автоматическое применение фильтров при изменении (кроме текстовых полей)
    const filterForm = document.querySelector('.filter-panel form');
    if (filterForm) {
        const debounce = (func, wait) => {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        };
        
        // Для select элементов - отправка при изменении
        const filterSelects = filterForm.querySelectorAll('select');
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                filterForm.submit();
            });
        });
        
        // Для полей цены - отправка после завершения ввода (дебаунс)
        const priceInputs = filterForm.querySelectorAll('input[name="price_min"], input[name="price_max"]');
        const submitForm = debounce(() => {
            filterForm.submit();
        }, 1000);
        
        priceInputs.forEach(input => {
            input.addEventListener('input', function() {
                // Ждем 1 секунду после последнего ввода
                submitForm();
            });
        });
    }
    
    // Кнопка сброса фильтров
    const resetBtn = document.querySelector('.reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/courses';
        });
    }
    
    // Отображение активных фильтров
    function displayActiveFilters() {
        const activeFilters = [];
        const urlParams = new URLSearchParams(window.location.search);
        
        if (urlParams.get('category') && urlParams.get('category') !== 'all') {
            activeFilters.push({
                name: 'category',
                value: urlParams.get('category'),
                label: `Категория: ${urlParams.get('category')}`
            });
        }
        
        if (urlParams.get('level') && urlParams.get('level') !== 'all') {
            const levelLabels = {
                'beginner': 'Начинающий',
                'middle': 'Средний',
                'pro': 'Профессионал'
            };
            activeFilters.push({
                name: 'level',
                value: urlParams.get('level'),
                label: `Уровень: ${levelLabels[urlParams.get('level')] || urlParams.get('level')}`
            });
        }
        
        if (urlParams.get('format') && urlParams.get('format') !== 'all') {
            const formatLabels = {
                'online': 'Онлайн',
                'offline': 'Офлайн',
                'mixed': 'Смешанный'
            };
            activeFilters.push({
                name: 'format',
                value: urlParams.get('format'),
                label: `Формат: ${formatLabels[urlParams.get('format')] || urlParams.get('format')}`
            });
        }
        
        if (urlParams.get('price_min')) {
            activeFilters.push({
                name: 'price_min',
                value: urlParams.get('price_min'),
                label: `Цена от: ${urlParams.get('price_min')} ₽`
            });
        }
        
        if (urlParams.get('price_max')) {
            activeFilters.push({
                name: 'price_max',
                value: urlParams.get('price_max'),
                label: `Цена до: ${urlParams.get('price_max')} ₽`
            });
        }
        
        // Отображение активных фильтров (опционально)
        if (activeFilters.length > 0) {
            console.log('Активные фильтры:', activeFilters);
            // Здесь можно добавить код для отображения активных фильтров на странице
        }
    }
    
    displayActiveFilters();
});
