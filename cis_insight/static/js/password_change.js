// フォーム送信
document.getElementById('password-change-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const errorMsg = document.getElementById('form-error');
    const oldPassword = document.getElementById('old_password').value;
    const newPassword = document.getElementById('new_password').value;
    const newPasswordConfirm = document.getElementById('new_password_confirm').value;

    errorMsg.innerText = "";

    if (oldPassword.length < 8) {
        errorMsg.innerText += '現在のパスワードは8文字以上で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (newPassword.length < 8) {
        errorMsg.innerText += '新しいパスワードは8文字以上で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (newPasswordConfirm.length < 8) {
        errorMsg.innerText += '新しいパスワード（確認用）は8文字以上で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (oldPassword === newPassword) {
        errorMsg.innerText += '新しいパスワードは現在のパスワードと同じにできません\n';
        errorMsg.classList.remove('hidden');
    }

    if (newPassword !== newPasswordConfirm) {
        errorMsg.innerText += '新しいパスワードが一致しません\n';
        errorMsg.classList.remove('hidden');
    }

    if (!newPassword.match(/^[a-zA-Z0-9]+$/)) {
        errorMsg.innerText += '新しいパスワードは英数字で入力してください\n';
        errorMsg.classList.remove('hidden');
    }

    if (errorMsg.innerText != "") {
        return;
    }

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    submitBtn.disabled = true;
    btnText.innerText = "更新中...";
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
        window.location.href = '/sign_in/';
    } else {
        errorMsg.innerText = data.message;
        errorMsg.classList.remove('hidden');
        submitBtn.disabled = false;
        btnText.innerText = "パスワードを更新";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});