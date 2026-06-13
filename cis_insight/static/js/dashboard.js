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

const scrollableContainer = document.querySelector('.overflow-y-auto');
const sentinel = document.getElementById('scroll-sentinel');
const container = document.getElementById('news-container');
const spinner = document.getElementById('loading-spinner');
let page = 1;
let isLoading = false;

const observer = new IntersectionObserver(async (entries) => {
    if (entries[0].isIntersecting && !isLoading) {
        isLoading = true;
        spinner.classList.remove('hidden');
        
        page++;
        try {
            const response = await fetch(`/includes/news_article_list/?page=${page}`);
            const data = await response.json();
            
            if (data.html && data.html.trim() !== "") {
                container.insertAdjacentHTML('beforeend', data.html);
            }
            if (!data.has_next) {
                observer.unobserve(sentinel);
                sentinel.style.display = 'none';
            }
        } catch (e) {
            console.error(e);
        } finally {
            spinner.classList.add('hidden');
            isLoading = false;
        }
    }
}, {
    root: scrollableContainer,
    rootMargin: '200px',
    threshold: 0
});

observer.observe(sentinel);

window.addEventListener('pageshow', () => {
    fetch('/api/news_count/')
        .then(res => res.json())
        .then(data => {
            document.querySelectorAll('.user_news_count').forEach(element => {
                element.innerText = data.read_count;
            });
        });
});