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

// メールアドレス変更関連
const emailChangeBtn = document.getElementById("email_change");
const emailChangeModal = document.getElementById("email-change-modal");
const emailChangeConfirmModal = document.getElementById("email-change-confirm-modal");
const emailChangeForm = document.getElementById("email-change-form");
const emailChangeConfirmForm = document.getElementById("email-change-confirm-form");
const openEmailChangeConfirmModalBtn = document.getElementById("open-email-change-confirm-modal-btn");
const emailInput = document.getElementById("email-change-input");
const confirmEmailInput = document.getElementById("email-change-confirm-input");
const confirmEmailChangeBtn = document.getElementById("confirm-email-change");

function openEmailChangeModal() {
    emailChangeModal.classList.remove('hidden');
    emailChangeModal.classList.add('flex');
}

function closeEmailChangeModal() {
    emailChangeModal.classList.add('hidden');
    emailChangeModal.classList.remove('flex');
}

function openEmailChangeConfirmModal() {
    emailChangeConfirmModal.classList.remove('hidden');
    emailChangeConfirmModal.classList.add('flex');
}

function closeEmailChangeConfirmModal() {
    emailChangeConfirmModal.classList.add('hidden');
    emailChangeConfirmModal.classList.remove('flex');
}

emailChangeBtn.addEventListener("click", () => {
    openEmailChangeModal();
});

openEmailChangeConfirmModalBtn.addEventListener("click", () => {

    if (!emailChangeForm.checkValidity()) {
        emailChangeForm.reportValidity();
        return;
    }

    const email = emailInput.value.trim();

    confirmEmailInput.value = email;

    closeEmailChangeModal();
    openEmailChangeConfirmModal();
});

emailChangeConfirmForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = confirmEmailInput.value;

    confirmEmailChangeBtn.disabled = true;
    confirmEmailChangeBtn.innerText = "送信中...";

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    try{
        const response = await fetch(emailChangeConfirmForm.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({email: email})
        })

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess("メールアドレスの変更用リンクを送信しました。メールをご確認ください。");
            closeEmailChangeConfirmModal();
        } else {
            console.log(data.error_message);
            showError(data.message);
        }
    } catch (error) {
        console.log(error);
        showError('申し訳ありません。メールアドレスの変更用リンクの送信に失敗しました。時間を空けてから再度お試しください。');
    }

    confirmEmailChangeBtn.disabled = false;
    confirmEmailChangeBtn.innerText = "メールを送信";
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeEmailChangeModal();
        closeEmailChangeConfirmModal();
    }
});

// パスワード変更関連
const passwordChangeBtn = document.getElementById("password_change");
const passwordChangeModal = document.getElementById("password-change-modal");
const passwordChangeConfirmModal = document.getElementById("password-change-confirm-modal");
const passwordChangeForm = document.getElementById("password-change-form");
const passwordChangeConfirmForm = document.getElementById("password-change-confirm-form");
const openPasswordChangeConfirmModalBtn = document.getElementById("open-password-change-confirm-modal-btn");
const confirmPasswordChangeBtn = document.getElementById("confirm-password-change");

function openPasswordChangeModal() {
    passwordChangeModal.classList.remove('hidden');
    passwordChangeModal.classList.add('flex');
}

function closePasswordChangeModal() {
    passwordChangeModal.classList.add('hidden');
    passwordChangeModal.classList.remove('flex');
}

function openPasswordChangeConfirmModal() {
    passwordChangeConfirmModal.classList.remove('hidden');
    passwordChangeConfirmModal.classList.add('flex');
}

function closePasswordChangeConfirmModal() {
    passwordChangeConfirmModal.classList.add('hidden');
    passwordChangeConfirmModal.classList.remove('flex');
}

passwordChangeBtn.addEventListener("click", () => {
    openPasswordChangeModal();
});

openPasswordChangeConfirmModalBtn.addEventListener("click", () => {

    const currentPassword = document.getElementById("current-password-input").value;
    const newPassword = document.getElementById("new-password-input").value;
    const newPasswordConfirm = document.getElementById("new-password-confirm-input").value;

    closePasswordChangeModal();
    openPasswordChangeConfirmModal();

    document.getElementById("current-password-input-confirm").value = currentPassword;
    document.getElementById("new-password-input-confirm").value = newPassword;
    document.getElementById("new-password-confirm-input-confirm").value = newPasswordConfirm;
});

passwordChangeConfirmForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(passwordChangeConfirmForm);

    confirmPasswordChangeBtn.disabled = true;
    confirmPasswordChangeBtn.innerText = "送信中...";

    const csrfToken = document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

    try{
        const response = await fetch(passwordChangeConfirmForm.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: formData
        })

        const data = await response.json();
        if (data.status === 'success') {
            showSuccess("パスワードを変更しました。ログインし直してください。");
            closePasswordChangeConfirmModal();
            setTimeout(() => {
                window.location.href = "/sign_in/";
            }, 2000);
        } else {
            console.log(data.error_message);
            showError(data.message);
        }
    } catch (error) {
        console.log(error);
        showError('申し訳ありません。パスワードの変更に失敗しました。時間を空けてから再度お試しください。');
    }

    confirmPasswordChangeBtn.disabled = false;
    confirmPasswordChangeBtn.innerText = "パスワードを変更";
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closePasswordChangeModal();
        closePasswordChangeConfirmModal();
    }
});

function showSuccess(msg){
    const successToast = document.getElementById("success-toast");
    const successMessage = document.getElementById("success-message");
    successMessage.innerText = msg;
    successToast.classList.remove("hidden");
    successToast.classList.add("flex");
    setTimeout(() => {
        successToast.classList.add("hidden");
        successToast.classList.remove("flex");
    }, 2000);
}

function showError(msg){
    const errorToast = document.getElementById("error-toast");
    const errorMessage = document.getElementById("error-message");
    errorMessage.innerText = msg;
    errorToast.classList.remove("hidden");
    errorToast.classList.add("flex");
    setTimeout(() => {
        errorToast.classList.add("hidden");
        errorToast.classList.remove("flex");
    }, 2000);
}