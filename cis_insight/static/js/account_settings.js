// モバイルユーザメニュー関連
function toggleMobileUserMenu() {
    const menu = document.getElementById('mobile-user-menu');
    menu.classList.toggle('hidden');
    const closeMenu = (e) => {
        if (!menu.contains(e.target) && !e.target.closest('button')) {
            menu.classList.add('hidden');
            document.removeEventListener('click', closeMenu);
        }
    };
    if (!menu.classList.contains('hidden')) {
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    }
}

// 画像表示関連
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('icon-preview');
            if (preview) {
                preview.src = e.target.result;
            } else {
                // プレースホルダーをプレビューに差し替え
                const placeholder = document.getElementById('icon-placeholder');
                const img = document.createElement('img');
                img.id = "icon-preview";
                img.src = e.target.result;
                img.className = "w-24 h-24 rounded-full object-cover border-4 border-slate-50 ring-1 ring-slate-200 shadow-lg";
                placeholder.replaceWith(img);
            }
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// フォーム関連
document.getElementById('account-settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const errorMsg = document.getElementById('form-error');

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    submitBtn.disabled = true;
    btnText.innerText = "更新中...";
    btnSpinner.classList.remove('hidden');
    btnIcon.classList.add('hidden');
    errorMsg.classList.add('hidden');
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        const data = await response.json();

        if (data.status === "success") {
            btnText.innerText = "更新完了";
            setTimeout(() => {
                window.location.href = '/dashboard/';
            }, 800);
        } else {
            if (errorMsg) {
                errorMsg.innerText = data.message || "エラーが発生しました";
                errorMsg.classList.remove('hidden');
            }
            resetButton();
        }
    } catch (error) {
        console.error("Error:", error);
        if (errorMsg) {
            errorMsg.innerText = "通信に失敗しました。";
            errorMsg.classList.remove('hidden');
        }
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "設定保存";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});

// パスワード変更関連
const passwordModal = document.getElementById('password-modal');
const passwordBtn = document.getElementById('password_change');

passwordBtn.addEventListener('click', (e) => {
    e.preventDefault();
    passwordModal.classList.remove('hidden');
    passwordModal.classList.add('flex');
});

function closePasswordModal() {
    passwordModal.classList.add('hidden');
    passwordModal.classList.remove('flex');
}

document.getElementById('confirm-password-change').addEventListener('click', async function() {
    const btn = this;
    const originalText = btn.innerText;
    
    btn.disabled = true;
    btn.innerText = '送信中...';

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    const response = await fetch(this.dataset.url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
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

    btn.disabled = false;
    btn.innerText = originalText;
});

function showSuccess() {
    const toast = document.getElementById('success-toast');
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 5000);
}

function showError(msg) {
    const toast = document.getElementById('error-toast');
    document.getElementById('error-message').innerText = msg;
    toast.classList.remove('hidden');
}
