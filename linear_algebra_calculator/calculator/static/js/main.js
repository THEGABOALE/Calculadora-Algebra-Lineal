
window.tailwind = window.tailwind || {};
tailwind.config = {
    theme: {
        extend: {
            animation: {
                'float': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                }
            }
        }
    }
};

/* 2) DOM logic: parallax and card fade-in */
document.addEventListener('DOMContentLoaded', function() {
    const parallaxElements = document.querySelectorAll('.parallax');

    window.addEventListener('scroll', function() {
        let scroll = window.pageYOffset;
        parallaxElements.forEach(function(element) {
            let speed = 0.5;
            element.style.transform = `translateY(${scroll * speed}px)`;
        });
    });

    // Efecto de aparición suave para las cards
    const cards = document.querySelectorAll('.glass');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';

        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 200 + (index * 100));
    });
});