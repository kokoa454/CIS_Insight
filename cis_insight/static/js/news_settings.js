// フォーム送信
document.getElementById('news-settings-form').addEventListener('submit', async (e) => {
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
        submitBtn.disabled = false;
        btnText.innerText = "更新完了";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
        setTimeout(() => {
            window.location.href = '/dashboard/';
        }, 500);
    } else {
        errorMsg.innerText = data.message;
        errorMsg.classList.remove('hidden');
        resetButton();
    }

    function resetButton() {
        submitBtn.disabled = false;
        btnText.innerText = "更新完了";
        btnSpinner.classList.add('hidden');
        btnIcon.classList.remove('hidden');
    }
});