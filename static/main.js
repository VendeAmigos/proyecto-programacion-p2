// main.js - Client-side JavaScript

// ===== GUEST CART MANAGEMENT (localStorage) =====
const GuestCart = {
    STORAGE_KEY: 'smartwatch_cart',
    
    getCart: function() {
        const cart = localStorage.getItem(this.STORAGE_KEY);
        return cart ? JSON.parse(cart) : {};
    },
    
    addItem: function(productId, cantidad = 1) {
        const cart = this.getCart();
        if (cart[productId]) {
            cart[productId] += cantidad;
        } else {
            cart[productId] = cantidad;
        }
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    removeItem: function(productId) {
        const cart = this.getCart();
        delete cart[productId];
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    updateItem: function(productId, cantidad) {
        const cart = this.getCart();
        if (cantidad > 0) {
            cart[productId] = cantidad;
        } else {
            delete cart[productId];
        }
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(cart));
        this.updateBadge();
    },
    
    getTotalItems: function() {
        const cart = this.getCart();
        return Object.values(cart).reduce((sum, qty) => sum + qty, 0);
    },
    
    clear: function() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateBadge();
    },
    
    updateBadge: function() {
        const badge = document.querySelector('.cart-badge');
        if (badge) {
            const totalItems = this.getTotalItems();
            if (totalItems > 0) {
                badge.textContent = totalItems;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize guest cart badge
    GuestCart.updateBadge();

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });

    // Quantity input validation
    const qtyInputs = document.querySelectorAll('.qty-input, .qty-input-large');
    qtyInputs.forEach(input => {
        input.addEventListener('change', function() {
            let value = parseInt(this.value);
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || 999;

            if (isNaN(value) || value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required], textarea[required]');
            let isValid = true;

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = '#ff453a';
                    input.addEventListener('input', function() {
                        this.style.borderColor = '';
                    });
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // Smooth scroll links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Handle "Add to Cart" button behavior
    const addToCartButtons = document.querySelectorAll('.btn-add-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const form = this.closest('form') || document.querySelector('form[action*="carrito_agregar"]');
            if (!form) return;
            
            // Check if quantity input exists
            const qtyInput = form.querySelector('input[name="cantidad"]');
            const cantidad = qtyInput ? parseInt(qtyInput.value) || 1 : 1;
            
            // Get product ID (could be from form or data attribute)
            const productId = form.querySelector('input[name="producto_id"]')?.value || 
                             this.getAttribute('data-product-id');
            
            if (!productId) {
                e.preventDefault();
                console.warn('Product ID not found');
                return;
            }
            
            // For guest users (no authentication), use localStorage
            const isGuest = !document.querySelector('body').getAttribute('data-user-authenticated');
            if (isGuest) {
                e.preventDefault();
                GuestCart.addItem(parseInt(productId), cantidad);
                
                // Show feedback
                const productName = this.getAttribute('data-product-name') || 'Producto';
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert--success';
                alertDiv.innerHTML = `✓ ${cantidad} ${productName} agregado(s) al carrito.`;
                alertDiv.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 10000; padding: 16px 20px; background: #34c759; color: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
                document.body.appendChild(alertDiv);
                
                setTimeout(() => {
                    alertDiv.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => alertDiv.remove(), 300);
                }, 5000);
            }
        });
    });
});

// Fadeout animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
`;
document.head.appendChild(style);

