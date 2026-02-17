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

    errorMsg.innerText = "";

    const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

    submitBtn.disabled = true;
    btnText.innerText = "登録中...";
    btnSpinner.classList.remove('hidden');
    btnIcon.classList.add('hidden');
    errorMsg.classList.add('hidden');

    try{
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
    } catch(error) {
        errorMsg.innerText = "登録に失敗しました。時間を空けてから再度お試しください。";
        errorMsg.classList.remove('hidden');
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "登録完了";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});