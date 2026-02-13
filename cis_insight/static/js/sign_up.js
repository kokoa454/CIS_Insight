// ユーザー名チェック
const usernameInput = document.getElementById('username');
const usernameStatus = document.getElementById('username-status');

usernameInput.addEventListener('input', () => {
    const username = usernameInput.value;
    
    if (username.length > 16) {
        usernameStatus.hidden = false;
        usernameStatus.innerText = '16文字以内で入力してください';
        usernameStatus.className = 'text-red-600';
        return;
    }
    
    if (!/^[a-z0-9_]+$/.test(username)) {
        usernameStatus.hidden = false;
        usernameStatus.innerText = '小文字英数字またはアンダースコアのみ使用できます';
        usernameStatus.className = 'text-red-600';
        return;
    }

    usernameStatus.hidden = true;
});

// 表示名チェック
const displayNameInput = document.getElementById('display_name');
const displayNameStatus = document.getElementById('display_name-status');

displayNameInput.addEventListener('input', () => {
    const displayName = displayNameInput.value;
    
    if (displayName.length > 16) {
        displayNameStatus.hidden = false;
        displayNameStatus.innerText = '16文字以内で入力してください';
        displayNameStatus.className = 'text-red-600';
        return;
    }

    displayNameStatus.hidden = true;
});

// パスワードチェック
const passwordInput = document.getElementById('password');
const passwordStatus = document.getElementById('password-status');

passwordInput.addEventListener('input', () => {
    const password = passwordInput.value;
    
    if (password.length < 8) {
        passwordStatus.hidden = false;
        passwordStatus.innerText = '8文字以上で入力してください';
        passwordStatus.className = 'text-red-600';
        return;
    }

    passwordStatus.hidden = true;
});

// パスワード確認チェック
const passwordConfirmInput = document.getElementById('password-confirm');
const passwordConfirmStatus = document.getElementById('password-confirm-status');

passwordConfirmInput.addEventListener('input', () => {
    const passwordConfirm = passwordConfirmInput.value;
    
    if (passwordConfirm !== passwordInput.value) {
        passwordConfirmStatus.hidden = false;
        passwordConfirmStatus.innerText = 'パスワードが一致しません';
        passwordConfirmStatus.className = 'text-red-600';
        return;
    }

    passwordConfirmStatus.hidden = true;
});

// フォーム送信
document.getElementById('final-signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const usernameStatus = document.getElementById('username-status');
    const displayNameStatus = document.getElementById('display_name-status');
    const passwordStatus = document.getElementById('password-status');
    const passwordConfirmStatus = document.getElementById('password-confirm-status');
    const errorMsg = document.getElementById('form-error');

    if (usernameStatus.hidden == false || displayNameStatus.hidden == false || passwordStatus.hidden == false || passwordConfirmStatus.hidden == false) {
        errorMsg.innerText = "入力内容に誤りがあります";
        errorMsg.classList.remove('hidden');
        return;
    }

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    submitBtn.disabled = true;
    btnText.innerText = "登録中...";
    btnSpinner.classList.remove('hidden');
    btnIcon.classList.add('hidden');
    errorMsg.classList.add('hidden');

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status == "success") {
            window.location.href = '/dashboard/';
        } else {
            errorMsg.innerText = data.message;
            errorMsg.classList.remove('hidden');
            resetButton();
        }
    })
    .catch(error => {
        console.error(error);
        errorMsg.innerText = "通信エラーが発生しました。";
        errorMsg.classList.remove('hidden');
        resetButton();
    });

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "登録を完了してダッシュボードへ";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});