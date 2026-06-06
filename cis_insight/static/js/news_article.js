document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById('article-container');
    
    if (!container || !container.dataset.articleId) {
        return; 
    }
    
    const articleId = container.dataset.articleId;
    const apiUrl = `/api/news_article_content/news_article_id=${articleId}/`;
    const apiUrl_translated = `/api/news_article_content_translated/news_article_id=${articleId}/`;

    const contentRuContainer = document.getElementById('content-ru-container');
    const contentJaContainer = document.getElementById('content-ja-container');

    const isContentAdded = contentRuContainer.dataset.isContentAdded.toLowerCase() == "true";
    const isContentTranslated = contentJaContainer.dataset.isContentTranslated.toLowerCase() == "true";

    if(isContentAdded && !isContentTranslated){
        fetch(apiUrl_translated)
            .then(response => {
                if (!response.ok) {
                    throw new Error('翻訳処理でエラーが発生しました。');
                }
                return response.json();
            })
            .then(data => {
                if (data.content_ja) {
                    document.getElementById('spinner-ja').classList.add('hidden');
                    const jaTarget = document.getElementById('content-ja');
                    jaTarget.innerText = data.content_ja;
                    jaTarget.classList.remove('hidden');
                } else {
                    showTranslationError();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showTranslationError();
            });
    }
    else if(!isContentAdded && isContentTranslated){
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('原文取得処理でエラーが発生しました。');
                }
                return response.json();
            })
            .then(data => {
                if (data.content_ru) {
                    document.getElementById('spinner-ru').classList.add('hidden');
                    const ruTarget = document.getElementById('content-ru');
                    ruTarget.innerText = data.content_ru;
                    ruTarget.classList.remove('hidden');
                } else {
                    throw new Error('原文データが空です。');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showOriginalError();
            });
    }
    else{
        fetch(apiUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('原文取得処理でエラーが発生しました。');
                }
                return response.json();
            })
            .then(data => {
                if (data.content_ru) {
                    document.getElementById('spinner-ru').classList.add('hidden');
                    const ruTarget = document.getElementById('content-ru');
                    ruTarget.innerText = data.content_ru;
                    ruTarget.classList.remove('hidden');
                    return fetch(apiUrl_translated);
                } else {
                    throw new Error('原文データが空です。');
                }
            })
            .then(response => {
                if (!response) return;
                if (!response.ok) {
                    throw new Error('翻訳処理でエラーが発生しました。');
                }
                return response.json();
            })
            .then(data => {
                if (!data) return;
                if (data.content_ja) {
                    document.getElementById('spinner-ja').classList.add('hidden');
                    const jaTarget = document.getElementById('content-ja');
                    jaTarget.innerText = data.content_ja;
                    jaTarget.classList.remove('hidden');
                } else {
                    showTranslationError();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('翻訳')) {
                    showTranslationError();
                } else {
                    showOriginalError();
                    showTranslationError();
                }
            });
    }
        
    function showTranslationError() {
        const spinnerJa = document.getElementById('spinner-ja');
        if (spinnerJa) spinnerJa.innerHTML = '<span class="text-sm text-red-500 font-normal">翻訳の取得に失敗しました。再読み込みしてください。</span>';
    }

    function showOriginalError() {
        const spinnerRu = document.getElementById('spinner-ru');
        if (spinnerRu) spinnerRu.innerHTML = '<span class="text-sm text-red-500 font-normal">原文の取得に失敗しました。再読み込みしてください。</span>';
    }
});