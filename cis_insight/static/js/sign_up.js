// フォーム送信
document.getElementById('final-signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const errorMsg = document.getElementById('form-error');
    const username = document.getElementById('username').value;
    const displayName = document.getElementById('display_name').value;
    const password = document.getElementById('password').value;
    const passwordConfirm = document.getElementById('password-confirm').value;

    errorMsg.innerText = "";

    if (username.length > 16) {
        errorMsg.innerText += 'ユーザーネームは16文字以内で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (!/^[a-z0-9_]+$/.test(username)) {
        errorMsg.innerText += 'ユーザーネームは小文字英数字またはアンダースコアのみ使用できます\n';
        errorMsg.classList.remove('hidden');
    }

    if (displayName.length > 16) {
        errorMsg.innerText += '表示名は16文字以内で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (password.length < 8) {
        errorMsg.innerText += 'パスワードは8文字以上で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (password !== passwordConfirm) {
        errorMsg.innerText += 'パスワードが一致しません\n';
        errorMsg.classList.remove('hidden');
    }

    if (errorMsg.innerText != "") {
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

    const response = await fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    const data = await response.json();
    if (data.status == "success") {
        window.location.href = '/dashboard/';
    } else {
        errorMsg.innerText = data.message;
        errorMsg.classList.remove('hidden');
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "登録を完了してダッシュボードへ";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});