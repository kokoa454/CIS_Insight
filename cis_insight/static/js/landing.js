document.addEventListener('DOMContentLoaded', () => {
    const tooltip = document.getElementById('country-tooltip');
    const paths = document.querySelectorAll('.country-path');
    const container = tooltip.parentElement;

    paths.forEach(path => {
        const countryId = path.id.replace('map-', '');
        const targetBtn = document.getElementById(`btn-${countryId}`);

        const highlight = () => {
            path.style.fill = '#ef4444';
            path.style.stroke = '#b91c1c';
            path.style.transform = 'scale(1.02)';
            if (targetBtn) {
                targetBtn.classList.add('border-red-500', 'bg-red-50', 'ring-2', 'ring-red-100');
            }
        };

        const reset = () => {
            path.style.fill = '#ffffff';
            path.style.stroke = '#000000';
            path.style.transform = 'scale(1)';
            if (targetBtn) {
                targetBtn.classList.remove('border-red-500', 'bg-red-50', 'ring-2', 'ring-red-100');
            }
        };

        path.addEventListener('mouseenter', () => {
            highlight();
            tooltip.innerText = path.getAttribute('data-name');
            tooltip.style.opacity = '1';
            if (targetBtn) {
                targetBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });

        path.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            tooltip.style.left = (e.clientX - rect.left + 15) + 'px';
            tooltip.style.top = (e.clientY - rect.top - 40) + 'px';
        });

        path.addEventListener('mouseleave', () => {
            reset();
            tooltip.style.opacity = '0';
        });

        if (targetBtn) {
            targetBtn.addEventListener('mouseenter', highlight);
            targetBtn.addEventListener('mouseleave', reset);

            targetBtn.addEventListener('click', () => {
                highlight();
                setTimeout(reset, 2000);
            });
        }
    });
});