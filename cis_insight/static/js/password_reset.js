document.getElementById('password-reset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnIcon = document.getElementById('btn-icon');
    const errorMsg = document.getElementById('form-error');

    errorMsg.innerText = "";

    const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

    const password = form.querySelector('input[name="password"]').value;
    const password_confirm = form.querySelector('input[name="password_confirm"]').value;
    const verification_code = form.querySelector('input[name="verification_code"]').value;

    submitBtn.disabled = true;
    btnText.innerText = "パスワードを再設定中...";
    btnSpinner.classList.remove('hidden');
    btnIcon.classList.add('hidden');
    errorMsg.classList.add('hidden');

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                password: password,
                password_confirm: password_confirm,
                verification_code: verification_code
            })
        });

        const data = await response.json();
        if (data.status == "success") {
            window.location.href = data.redirect_url || '/password_reset_complete/'; 
        } else {
            errorMsg.innerText = data.message;
            errorMsg.classList.remove('hidden');
            resetButton();
        }
    } catch(error) {
        errorMsg.innerText = "パスワードの再設定に失敗しました。時間を空けてから再度お試しください。";
        errorMsg.classList.remove('hidden');
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "パスワードをリセットする";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});