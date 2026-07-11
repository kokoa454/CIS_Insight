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

if (sentinel) {
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
}

window.addEventListener('pageshow', () => {
    fetch('/api/news_count/')
        .then(res => res.json())
        .then(data => {
            document.querySelectorAll('.user_news_count').forEach(element => {
                element.innerText = data.read_count;
            });
        });
});

const homeButton = document.getElementById('nav-home');
if (homeButton && scrollableContainer) {
    homeButton.addEventListener('click', (e) => {
        if (window.location.pathname === '/dashboard/' || window.location.pathname === '/') {
            e.preventDefault();
            
            // 上部へスムーズスクロールさせてから更新
            scrollableContainer.scrollTo({ top: 0, behavior: 'smooth' });
            
            setTimeout(() => {
                window.location.reload();
            }, 300);
        }
    });
}

const pullSpinner = document.getElementById('pull-spinner');
if (scrollableContainer && pullSpinner) {
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    const pullThreshold = 80;

    scrollableContainer.addEventListener('touchstart', (e) => {
        if (scrollableContainer.scrollTop === 0) {
            startY = e.touches[0].pageY;
            isPulling = true;
        }
    }, { passive: true });

    scrollableContainer.addEventListener('touchmove', (e) => {
        if (!isPulling) return;
        
        currentY = e.touches[0].pageY;
        const diff = currentY - startY;
        
        if (diff > 0) {
            const dragDistance = Math.min(diff * 0.4, pullThreshold + 20);
            
            pullSpinner.style.transform = `translate(-50%, ${dragDistance}px) scale(${Math.min(dragDistance / pullThreshold, 1)})`;
            pullSpinner.style.opacity = Math.min(dragDistance / pullThreshold, 1);
        }
    }, { passive: true });

    scrollableContainer.addEventListener('touchend', () => {
        if (!isPulling) return;
        isPulling = false;
        
        const diff = currentY - startY;
        
        if (diff >= pullThreshold && scrollableContainer.scrollTop === 0) {
            pullSpinner.style.transform = `translate(-50%, ${pullThreshold}px) scale(1)`;
            setTimeout(() => {
                window.location.reload();
            }, 400);
        } else {
            pullSpinner.style.opacity = '0';
            pullSpinner.style.transform = 'translate(-50%, 0px) scale(75)';
        }
        
        startY = 0;
        currentY = 0;
    });
}