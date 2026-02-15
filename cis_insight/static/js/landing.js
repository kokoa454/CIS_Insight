// 地図関連
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

// モーダル関連
function openModal() {
    const modal = document.getElementById('email-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.classList.add('overflow-hidden');
}

function closeModal() {
    const modal = document.getElementById('email-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.body.classList.remove('overflow-hidden');
}

function showSuccess() {
    const toast = document.getElementById('success-toast');
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        hideSuccess();
    }, 5000);
}

function hideSuccess() {
    const toast = document.getElementById('success-toast');
    toast.classList.add('hidden');
}

function showError(message) {
    const toast = document.getElementById('error-toast');
    const errorMessage = document.getElementById('error-message');
    toast.classList.remove('hidden');
    errorMessage.textContent = message;
    
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    const toast = document.getElementById('error-toast');
    toast.classList.add('hidden');
}

// フォーム送信
document.getElementById('pre-sign-up-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
    const email = document.getElementById('user-email').value;

    const response = await fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ email: email }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess();
        } else {
            console.log(data.error_message);
            showError(data.message);
        }
    })
    .catch(error => {
        console.log(error);
        showError('申し訳ありません。仮登録に失敗しました。時間を空けてから再度お試しください。');
    });

    closeModal();
});