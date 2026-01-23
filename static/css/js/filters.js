// Валидация полей цены
document.addEventListener('DOMContentLoaded', function() {
    const priceMin = document.querySelector('input[name="price_min"]');
    const priceMax = document.querySelector('input[name="price_max"]');
    
    if (priceMin) {
        priceMin.addEventListener('input', function(e) {
            // Удаляем все не-цифры
            this.value = this.value.replace(/[^\d]/g, '');
        });
    }
    
    if (priceMax) {
        priceMax.addEventListener('input', function(e) {
            // Удаляем все не-цифры
            this.value = this.value.replace(/[^\d]/g, '');
        });
    }
    
    // Очистка пустых полей перед отправкой формы
    const filterForm = document.querySelector('.filter-panel form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[type="text"]');
            inputs.forEach(input => {
                if (input.value === '') {
                    input.disabled = true; // Не отправляем пустые поля
                }
            });
        });
    }
});
