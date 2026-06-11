// remember-me関連
const rememberMeCheckbox = document.getElementById('remember_me');
const usernameInput = document.getElementById('username');

document.addEventListener('DOMContentLoaded', () => {
    const savedUsername = localStorage.getItem('cis_insight_remember_username');
    if (savedUsername) {
        usernameInput.value = savedUsername;
        rememberMeCheckbox.checked = true;
    }
});

// フォーム送信処理
const signInForm = document.getElementById('sign-in-form');

signInForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const errorMsg = document.getElementById('form-error');
    const passwordInput = document.getElementById('password');

    if (usernameInput.value == "") {
        errorMsg.innerText = "ユーザー名を入力してください";
        errorMsg.classList.remove('hidden');
        return;
    }

    if (passwordInput.value == "") {
        errorMsg.innerText = "パスワードを入力してください";
        errorMsg.classList.remove('hidden');
        return;
    }

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    submitBtn.disabled = true;
    btnText.innerText = "ログイン中...";
    btnSpinner.classList.remove('hidden');
    btnIcon.classList.add('hidden');
    errorMsg.classList.add('hidden');

    const response = await fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    });

    const data = await response.json();
    if (data.status == "success") {
        if (rememberMeCheckbox.checked) {
            localStorage.setItem('cis_insight_remember_username', usernameInput.value);
        } else {
            localStorage.removeItem('cis_insight_remember_username');
        }
        window.location.href = '/dashboard/';
    } else {
        errorMsg.innerText = data.message;
        errorMsg.classList.remove('hidden');
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "ログイン";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});

// モーダル関連
function openModal() {
    const modal = document.getElementById('password-reset-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.classList.add('overflow-hidden');
}

function closeModal() {
    const modal = document.getElementById('password-reset-modal');
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

// パスワードリセットフォーム
document.getElementById('password-reset-button').addEventListener('click', openModal);
document.getElementById('password-reset-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
    const email = document.getElementById('user-email').value;

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ email: email }),
        })
        
        const data = await response.json();
        if (data.status === 'success') {
            showSuccess();
            closeModal();
        } else {
            showError(data.message);
        }
    } catch(error) {
        showError('申し訳ありません。パスワードリセット用のメールの送信に失敗しました。時間を空けてから再度お試しください。');
    }
});
