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