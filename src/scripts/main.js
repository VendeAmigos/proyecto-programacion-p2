// ===================================
// SMARTWATCH E-COMMERCE
// Main JavaScript File (ES6+)
// ===================================

/**
 * GUEST CART MANAGEMENT
 * Handles localStorage for guest users
 */
const GuestCart = {
    STORAGE_KEY: 'smartwatch_cart',
    
    getCart() {
        const cart = localStorage.getItem(this.STORAGE_KEY);
        return cart ? JSON.parse(cart) : {};
    },
    
    addItem(productId, cantidad = 1) {
        const cart = this.getCart();
        cart[productId] = (cart[productId] || 0) + cantidad;
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    removeItem(productId) {
        const cart = this.getCart();
        delete cart[productId];
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    updateItem(productId, cantidad) {
        const cart = this.getCart();
        if (cantidad > 0) {
            cart[productId] = cantidad;
        } else {
            delete cart[productId];
        }
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    getTotalItems() {
        const cart = this.getCart();
        return Object.values(cart).reduce((sum, qty) => sum + qty, 0);
    },
    
    clear() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateBadge();
    },
    
    updateBadge() {
        const badge = document.querySelector('.cart-badge');
        if (badge) {
            const totalItems = this.getTotalItems();
            badge.textContent = totalItems;
            badge.style.display = totalItems > 0 ? 'flex' : 'none';
        }
    }
};

/**
 * INITIALIZE ON DOM READY
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize cart badge
    GuestCart.updateBadge();
    
    // Alert auto-dismiss
    dismissAlerts();
    
    // Form validation
    validateForms();
    
    // Quantity input validation
    validateQuantityInputs();
    
    // Smooth scroll links
    initSmoothScroll();
});

/**
 * Auto-dismiss alerts after 5 seconds
 */
function dismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

/**
 * Validate quantity inputs
 */
function validateQuantityInputs() {
    const inputs = document.querySelectorAll('.qty-input, .qty-input-large, .qty');
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            let value = parseInt(this.value) || 1;
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || 999;
            
            this.value = Math.max(min, Math.min(max, value));
        });
    });
}

/**
 * Form validation with visual feedback
 */
function validateForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = '#ff453a';
                    input.addEventListener('input', function() {
                        this.style.borderColor = '';
                    }, { once: true });
                }
            });
            
            if (!isValid) e.preventDefault();
        });
    });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Export for use in modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GuestCart };
}
