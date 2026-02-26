// モバイルユーザーメニューの開閉
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

// フォーム送信
document.getElementById('rss-settings-form').addEventListener('submit', async (e) => {
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
    btnText.innerText = "登録中...";
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
            btnText.innerText = "登録完了";
            setTimeout(() => {
                window.location.href = '/rss_settings/';
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

// RSS有効無効
let currentRss = null;

const rssDeactivateForm = document.getElementById("rss-deactivate-form");
const rssActivateForm = document.getElementById("rss-activate-form");
const rssDeleteForm = document.getElementById("rss-delete-form");

document.querySelectorAll(".rss-activate-deactivate-btn")
.forEach(button => {

    button.addEventListener("click", () => {

        currentRss = {
            id: button.dataset.id,
            isActive: button.dataset.isActive,
            company: button.dataset.company,
            url: button.dataset.url
        };

        if (currentRss.isActive === "True") {
            const modal = document.getElementById("rss-deactivate-confirm-modal");
            modal.classList.remove("hidden");
            modal.classList.add("flex");

            document.getElementById("rss-deactivate-confirm-company").value = currentRss.company;
            document.getElementById("rss-deactivate-confirm-url").value = currentRss.url;

        } else {
            const modal = document.getElementById("rss-activate-confirm-modal");
            modal.classList.remove("hidden");
            modal.classList.add("flex");

            document.getElementById("rss-activate-confirm-company").value = currentRss.company;
            document.getElementById("rss-activate-confirm-url").value = currentRss.url;
        }
    });
});


rssDeactivateForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentRss) return;

    try {
        const csrfToken = document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

        const response = await fetch("/api/deactivate_rss/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                rss_id: currentRss.id,
                rss_is_active: currentRss.isActive,
                rss_company: currentRss.company,
                rss_url: currentRss.url
            })
        });

        const data = await response.json();
        if (data.status === "success") {
            showSuccess("RSS設定を無効化しました。");
            setTimeout(() => {
                window.location.href = '/rss_settings/';
            }, 800);
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        showError("通信に失敗しました。" + error);
    }
});

rssActivateForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentRss) return;

    try{
        const csrfToken = document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

        const response = await fetch("/api/activate_rss/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                rss_id: currentRss.id,
                rss_is_active: currentRss.isActive,
                rss_company: currentRss.company,
                rss_url: currentRss.url
            })
        });

        const data = await response.json();
        if (data.status === "success") {
            showSuccess("RSS設定を有効化しました。");
            setTimeout(() => {
                window.location.href = '/rss_settings/';
            }, 800);
        } else {
            showError(data.message);
        }
    }catch (error) {
        console.error("Error:", error);
        showError("通信に失敗しました。" + error);
    }
});

// RSS削除
document.querySelectorAll(".rss-delete-btn")
.forEach(button => {

    button.addEventListener("click", () => {

        currentRss = {
            id: button.dataset.id,
            company: button.dataset.company,
            isActive: button.dataset.isActive,
            url: button.dataset.url
        };

        const modal = document.getElementById("rss-delete-confirm-modal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");

        document.getElementById("rss-delete-confirm-company").value = currentRss.company;
        document.getElementById("rss-delete-confirm-url").value = currentRss.url;
    });
}); 

rssDeleteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log(currentRss);
    if (!currentRss) return;

    try {
        const csrfToken = document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

        const response = await fetch("/api/delete_rss/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                rss_id: currentRss.id,
                rss_is_active: currentRss.isActive,
                rss_company: currentRss.company,
                rss_url: currentRss.url
            })
        });

        const data = await response.json();
        if (data.status === "success") {
            showSuccess("RSS設定を削除しました。");
            setTimeout(() => {
                window.location.href = '/rss_settings/';
            }, 800);
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        showError("通信に失敗しました。" + error);
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

function closeRssDeactivateConfirmModal() {
    const rssDeactivateConfirmModal = document.getElementById("rss-deactivate-confirm-modal");
    rssDeactivateConfirmModal.classList.add("hidden");
    rssDeactivateConfirmModal.classList.remove("flex");
}

function closeRssActivateConfirmModal() {
    const rssActivateConfirmModal = document.getElementById("rss-activate-confirm-modal");
    rssActivateConfirmModal.classList.add("hidden");
    rssActivateConfirmModal.classList.remove("flex");
}

function closeRssDeleteConfirmModal() {
    const rssDeleteConfirmModal = document.getElementById("rss-delete-confirm-modal");
    rssDeleteConfirmModal.classList.add("hidden");
    rssDeleteConfirmModal.classList.remove("flex");
}