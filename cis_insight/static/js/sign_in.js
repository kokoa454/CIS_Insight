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