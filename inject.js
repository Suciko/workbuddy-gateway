(function() {
    if (window.checkinLoaderInjected) return;
    window.checkinLoaderInjected = true;
    console.log('[Injected] CodeBuddy UI Loader & AetherVerse Landing Page started');

    // Dynamically replace Favicon with custom Logo image
    function updateFavicon() {
        const logoEl = document.querySelector('img[src^="data:image"]') || 
                       document.querySelector('.logo img') ||
                       document.querySelector('img.logo');
        if (logoEl && logoEl.src) {
            let link = document.querySelector("link[rel*='icon']") || document.createElement('link');
            link.type = 'image/png';
            link.rel = 'shortcut icon';
            link.href = logoEl.src;
            if (!link.parentNode) {
                document.getElementsByTagName('head')[0].appendChild(link);
            }
        }
    }
    setInterval(updateFavicon, 1000);

    function hidePanel() {
        const wrapper = document.getElementById('checkin-iframe-wrapper');
        if (wrapper) {
            wrapper.style.display = 'none';
        }
        
        const contentArea = document.querySelector('.semi-layout-content, .ant-layout-content, main');
        if (contentArea) {
            Array.from(contentArea.children).forEach(child => {
                if (child.id !== 'checkin-iframe-wrapper') {
                    child.style.display = '';
                }
            });
        }
        
        const checkinLi = document.getElementById('checkin-menu-item');
        if (checkinLi) {
            checkinLi.classList.remove('semi-navigation-item-selected', 'semi-navigation-item-active', 'sidebar-nav-item-selected', 'ant-menu-item-selected');
            const myTextSpan = checkinLi.querySelector('.semi-navigation-item-text span');
            if (myTextSpan) myTextSpan.style.color = 'inherit';
        }
    }

    function init() {
        const settingLink = document.querySelector('a[href*="/setting"], .ant-menu-item a[href*="/setting"], [role="menuitem"] a[href*="/setting"]') ||
                            document.querySelector('a[href*="/channel"], .ant-menu-item a[href*="/channel"], [role="menuitem"] a[href*="/channel"]');
        
        if (settingLink) {
            if (document.getElementById('checkin-menu-item')) return;
            console.log('[Injected] Found settings link, inserting WeChat Check-in item.');
            
            const isSemi = settingLink.querySelector('.semi-navigation-item, li');
            
            if (isSemi) {
                // Semi Design
                const settingItemContainer = settingLink.parentNode;
                const menuContainer = settingItemContainer.parentNode;
                
                const newContainer = document.createElement(settingItemContainer.tagName);
                newContainer.className = settingItemContainer.className;
                
                const newLink = document.createElement('a');
                newLink.href = '#';
                newLink.id = 'checkin-menu-link';
                newLink.style.textDecoration = 'none';
                
                const newLi = document.createElement('li');
                newLi.id = 'checkin-menu-item';
                newLi.className = isSemi.className || 'semi-navigation-item-normal semi-navigation-item';
                newLi.role = 'menuitem';
                newLi.style.cursor = 'pointer';
                
                newLi.innerHTML = `
                    <i class="semi-navigation-item-icon semi-navigation-item-icon-info">
                        <div class="sidebar-icon-container flex-shrink-0" style="display: flex; align-items: center; justify-content: center;">
                            <svg viewBox="0 0 1024 1024" width="16" height="16" fill="currentColor">
                                <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm193.5 301.7l-210.6 292a31.8 31.8 0 0 1-51.7.3L318.5 484.9c-6-7.5-4.2-18.7 4-23.9l36-22.8c7.5-4.8 17.4-2.7 22.3 4.8l82 124.9 170.8-236.7c5.1-7.1 15-8.7 22.1-3.6l37.7 27.2c7.2 5.1 8.8 15 3.7 22.1z"></path>
                            </svg>
                        </div>
                    </i>
                    <span class="semi-navigation-item-text">
                        <span class="truncate font-medium text-sm" style="color: inherit;">CodeBuddy 控制台</span>
                    </span>
                `;
                
                newLink.appendChild(newLi);
                newContainer.appendChild(newLink);
                
                newLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    document.querySelectorAll('.semi-navigation-item-selected, .semi-navigation-item-active, .sidebar-nav-item-selected').forEach(el => {
                        el.classList.remove('semi-navigation-item-selected', 'semi-navigation-item-active', 'sidebar-nav-item-selected');
                        const ts = el.querySelector('.semi-navigation-item-text span');
                        if (ts) ts.style.color = 'inherit';
                    });
                    
                    newLi.classList.add('semi-navigation-item-selected');
                    const myTextSpan = newLi.querySelector('.semi-navigation-item-text span');
                    if (myTextSpan) myTextSpan.style.color = 'var(--semi-color-primary)';
                    
                    renderIframe();
                });
                
                menuContainer.insertBefore(newContainer, settingItemContainer.nextSibling);
            } else {
                // Ant Design fallback
                const settingLi = settingLink.closest('.ant-menu-item, li');
                if (settingLi) {
                    const li = document.createElement('li');
                    li.id = 'checkin-menu-item';
                    li.className = settingLi.className || 'ant-menu-item';
                    li.role = 'menuitem';
                    li.style.paddingLeft = '24px';
                    
                    li.innerHTML = `
                        <span class="ant-menu-title-content">
                            <a href="#" id="checkin-link" style="display: flex; align-items: center; gap: 8px; color: inherit; text-decoration: none;">
                                <svg viewBox="0 0 1024 1024" width="1em" height="1em" fill="currentColor" style="font-size: 16px;">
                                    <path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm193.5 301.7l-210.6 292a31.8 31.8 0 0 1-51.7.3L318.5 484.9c-6-7.5-4.2-18.7 4-23.9l36-22.8c7.5-4.8 17.4-2.7 22.3 4.8l82 124.9 170.8-236.7c5.1-7.1 15-8.7 22.1-3.6l37.7 27.2c7.2 5.1 8.8 15 3.7 22.1z"></path>
                                </svg>
                                <span>CodeBuddy 控制台</span>
                            </a>
                        </span>
                    `;
                    
                    li.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        document.querySelectorAll('.ant-menu-item-selected').forEach(el => {
                            el.classList.remove('ant-menu-item-selected');
                        });
                        li.classList.add('ant-menu-item-selected');
                        
                        renderIframe();
                    });
                    
                    settingLi.parentNode.insertBefore(li, settingLi.nextSibling);
                }
            }
        }
    }

    function renderIframe() {
        const contentArea = document.querySelector('.semi-layout-content, .ant-layout-content, main');
        if (contentArea) {
            console.log('[Injected] Embedding Quota & Check-in dashboard in main content area.');
            
            let wrapper = document.getElementById('checkin-iframe-wrapper');
            if (!wrapper) {
                wrapper = document.createElement('div');
                wrapper.id = 'checkin-iframe-wrapper';
                wrapper.style.width = '100%';
                wrapper.style.height = 'calc(100vh - 160px)';
                wrapper.style.padding = '0';
                wrapper.style.boxSizing = 'border-box';
                wrapper.style.background = 'transparent';
                wrapper.style.marginTop = '64px'; // Pushes it down below the sticky blurred header
                
                const isDark = document.body.classList.contains('dark') || 
                               document.documentElement.classList.contains('dark') ||
                               document.body.getAttribute('theme-mode') === 'dark' ||
                               document.documentElement.getAttribute('theme-mode') === 'dark';
                const theme = isDark ? 'dark' : 'light';
                
                const protocol = window.location.protocol;
                const hostname = window.location.hostname;
                const isLocal = ['localhost', '127.0.0.1', '::1'].includes(hostname);
                const iframePort = isLocal ? '8000' : '8001';
                const iframeSrc = protocol + '//' + hostname + ':' + iframePort + '/checkin-dashboard?theme=' + theme + '&v=' + new Date().getTime();
                
                wrapper.innerHTML = `<iframe src="${iframeSrc}" style="width: 100%; height: 100%; border: none; border-radius: 12px; background: transparent;"></iframe>`;
                contentArea.appendChild(wrapper);

                // Setup MutationObserver to notify theme change dynamically
                const observer = new MutationObserver(() => {
                    const currentDark = document.body.classList.contains('dark') || 
                                        document.documentElement.classList.contains('dark') ||
                                        document.body.getAttribute('theme-mode') === 'dark' ||
                                        document.documentElement.getAttribute('theme-mode') === 'dark';
                    const currentTheme = currentDark ? 'dark' : 'light';
                    const iframe = wrapper.querySelector('iframe');
                    if (iframe && iframe.contentWindow) {
                        iframe.contentWindow.postMessage({ type: 'theme-change', theme: currentTheme }, '*');
                    }
                });
                observer.observe(document.body, { attributes: true, attributeFilter: ['class', 'theme-mode'] });
                observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class', 'theme-mode'] });
            }
            
            wrapper.style.display = 'block';
            
            Array.from(contentArea.children).forEach(child => {
                if (child.id !== 'checkin-iframe-wrapper') {
                    child.style.display = 'none';
                }
            });
        } else {
            console.error('[Injected] Main content area not found.');
        }
    }

    // ----------------------------------------------------
    // Patina-style Custom Landing Page Integration
    // ----------------------------------------------------
    let systemStatus = null;
    function fetchStatus(callback) {
        if (systemStatus) {
            callback(systemStatus);
            return;
        }
        fetch('/api/status')
            .then(res => res.json())
            .then(resData => {
                if (resData && resData.success && resData.data) {
                    systemStatus = resData.data;
                    callback(systemStatus);
                } else {
                    callback({ SystemName: 'AetherVerse', Logo: '' });
                }
            })
            .catch(() => {
                callback({ SystemName: 'AetherVerse', Logo: '' });
            });
    }

    // Interactive helper functions exposed to global window
    window.aetherverseCopyText = function(text, btnId) {
        navigator.clipboard.writeText(text).then(() => {
            const btn = document.getElementById(btnId);
            if (btn) {
                const oldHtml = btn.innerHTML;
                btn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
                btn.style.color = '#4A9E8E';
                setTimeout(() => {
                    btn.innerHTML = oldHtml;
                    btn.style.color = '';
                }, 1500);
            }
        });
    };

    window.aetherverseSwitchTab = function(tabName) {
        const tabs = document.querySelectorAll('#aetherverse-landing .guide-tab');
        const contents = document.querySelectorAll('#aetherverse-landing .guide-content');
        
        tabs.forEach(tab => {
            if (tab.getAttribute('data-tab') === tabName) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });
        
        contents.forEach(content => {
            if (content.id === `guide-${tabName}`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
    };

    window.aetherverseToggleFaq = function(faqId) {
        const items = document.querySelectorAll('#aetherverse-landing .faq-item');
        items.forEach((item, index) => {
            if (index === faqId) {
                item.classList.toggle('active');
            } else {
                item.classList.remove('active');
            }
        });
    };


    window.aetherverseToggleFaq = function(faqId) {
        const items = document.querySelectorAll('#aetherverse-landing .faq-item');
        items.forEach((item, index) => {
            if (index === faqId) {
                item.classList.toggle('active');
            } else {
                item.classList.remove('active');
            }
        });
    };

    function renderLandingPage(container) {
        fetchStatus((status) => {
            const systemName = status.SystemName || 'AetherVerse';
            const logoSrc = status.Logo || '';
            const isLogged = localStorage.getItem('user') !== null;
            
            let logoHtml = '';
            if (logoSrc) {
                logoHtml = '<img src="' + logoSrc + '" alt="' + systemName + '" />';
            }
            
            container.innerHTML = `
                <!-- Google Fonts -->
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
                
                <style>
                    /* Safe layout integration & Hide native content/footer on landing page */
                    body.landing-active,
                    body.landing-active .semi-layout,
                    body.landing-active .ant-layout {
                        background-color: #030712 !important;
                        background: #030712 !important;
                    }

                    body.landing-active .semi-layout-content,
                    body.landing-active .ant-layout-content,
                    body.landing-active main,
                    body.landing-active .semi-layout-footer,
                    body.landing-active .ant-layout-footer,
                    body.landing-active footer {
                        display: none !important;
                    }

                    /* Transparent navbar with white text when landing page is active */
                    body.landing-active .semi-layout-header,
                    body.landing-active .ant-layout-header,
                    body.landing-active header,
                    body.landing-active .semi-navigation,
                    body.landing-active .semi-navigation-header,
                    body.landing-active .ant-menu-horizontal,
                    body.landing-active .ant-layout-header .ant-menu {
                        background: transparent !important;
                        background-color: transparent !important;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
                        backdrop-filter: blur(20px) !important;
                        -webkit-backdrop-filter: blur(20px) !important;
                        box-shadow: none !important;
                        position: sticky !important;
                        top: 0 !important;
                        z-index: 1000 !important;
                    }

                    body.landing-active .semi-layout-header *,
                    body.landing-active .ant-layout-header *,
                    body.landing-active header *,
                    body.landing-active .semi-navigation * {
                        color: #ffffff !important;
                    }

                    body.landing-active .semi-layout-header svg,
                    body.landing-active .semi-navigation svg,
                    body.landing-active header svg,
                    body.landing-active .ant-layout-header svg {
                        fill: #ffffff !important;
                        color: #ffffff !important;
                    }

                    body.landing-active .semi-layout-header img,
                    body.landing-active .ant-layout-header img,
                    body.landing-active header img {
                        color: initial !important;
                    }

                    /* Exclude portals and dropdown select menus from getting forced white text */
                    .semi-portal *,
                    .ant-select-dropdown *,
                    .ant-dropdown * {
                        color: initial !important;
                    }

                    #aetherverse-landing {
                        /* Force sui.io dark theme by default */
                        --bg-color: #030712;
                        --text-primary: #f8fafc;
                        --text-secondary: #94a3b8;
                        --accent: #298dff;
                        --accent-rgb: 41, 141, 255;
                        --border: rgba(255, 255, 255, 0.08);
                        --card-bg: rgba(15, 23, 42, 0.6);
                        --card-hover-border: rgba(41, 141, 255, 0.3);
                        --glow-color: rgba(41, 141, 255, 0.15);
                        --text-x: 50%;
                        --text-y: 50%;
                        --mouse-x: 50%;
                        --mouse-y: 50%;
                        
                        background: transparent;
                        color: var(--text-primary);
                        min-height: calc(100vh - 64px);
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        position: relative;
                        overflow: hidden;
                        padding-bottom: 80px;
                    }

                    /* API Endpoint container */
                    .endpoint-container-wrap {
                        display: flex;
                        justify-content: center;
                        margin-top: 60px;
                        margin-bottom: 80px;
                        position: relative;
                        z-index: 25;
                    }

                    .endpoint-container {
                        background: var(--card-bg);
                        border: 1px solid var(--border);
                        border-radius: 100px;
                        padding: 10px 24px;
                        display: flex;
                        align-items: center;
                        gap: 16px;
                        backdrop-filter: blur(12px);
                        -webkit-backdrop-filter: blur(12px);
                        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                        max-width: 90%;
                    }

                    .endpoint-dot-green {
                        width: 8px;
                        height: 8px;
                        background: #10b981;
                        border-radius: 50%;
                        box-shadow: 0 0 12px #10b981;
                        animation: pulse-green 2s infinite;
                    }

                    .endpoint-label-text {
                        font-size: 12px;
                        font-weight: 700;
                        letter-spacing: 0.5px;
                        color: #10b981;
                        text-transform: uppercase;
                    }

                    .url-base {
                        font-family: monospace;
                        font-size: 14px;
                        color: var(--text-primary);
                        background: rgba(0, 0, 0, 0.25);
                        padding: 4px 12px;
                        border-radius: 100px;
                        border: 1px solid var(--border);
                    }

                    .btn-copy {
                        background: transparent;
                        border: none;
                        color: var(--text-secondary);
                        cursor: pointer;
                        padding: 6px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        transition: all 0.2s;
                    }

                    .btn-copy:hover {
                        background: rgba(255,255,255,0.08);
                        color: var(--text-primary);
                    }

                    /* ---------------------------------------------------- */
                    /* Custom SVGs and 3D Cube Override for Webflow Layout */
                    /* ---------------------------------------------------- */
                    .timeline_card_anim {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 10px 0;
                    }
                    .scene-3d {
                        width: 70px;
                        height: 70px;
                        perspective: 200px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .wireframe-cube {
                        width: 40px;
                        height: 40px;
                        position: relative;
                        transform-style: preserve-3d;
                        animation: rotate-cube 14s linear infinite;
                    }
                    @keyframes rotate-cube {
                        0% { transform: rotateX(0deg) rotateY(0deg) rotateZ(0deg); }
                        100% { transform: rotateX(360deg) rotateY(360deg) rotateZ(360deg); }
                    }
                    .cube-face {
                        position: absolute;
                        width: 40px;
                        height: 40px;
                        border: 1px solid rgba(41, 141, 255, 0.55);
                        background: rgba(41, 141, 255, 0.05);
                        box-sizing: border-box;
                    }
                    .face-front  { transform: translateZ(20px); }
                    .face-back   { transform: rotateY(180deg) translateZ(20px); }
                    .face-left   { transform: rotateY(-90deg) translateZ(20px); }
                    .face-right  { transform: rotateY(90deg) translateZ(20px); }
                    .face-top    { transform: rotateX(90deg) translateZ(20px); }
                    .face-bottom { transform: rotateX(-90deg) translateZ(20px); }

                    /* Auto-scan rotation */
                    @keyframes spin-slow {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }

                    /* Pulse for scanners and endpoints */
                    @keyframes pulse-green {
                        0% { transform: scale(0.9); opacity: 0.4; }
                        50% { transform: scale(1.1); opacity: 1; }
                        100% { transform: scale(0.9); opacity: 0.4; }
                    }

                    /* Drop flows */
                    @keyframes drop-flow-r {
                        0% { transform: translateY(-15px) scale(0.85); opacity: 0; }
                        30% { opacity: 1; }
                        70% { opacity: 1; }
                        100% { transform: translateY(15px) scale(0.85); opacity: 0; }
                    }
                    @keyframes drop-flow-b {
                        0% { transform: translateY(-20px) scale(0.85); opacity: 0; }
                        30% { opacity: 1; }
                        70% { opacity: 1; }
                        100% { transform: translateY(20px) scale(0.85); opacity: 0; }
                    }
                    @keyframes drop-flow-g {
                        0% { transform: translateY(-12px) scale(0.85); opacity: 0; }
                        30% { opacity: 1; }
                        70% { opacity: 1; }
                        100% { transform: translateY(22px) scale(0.85); opacity: 0; }
                    }
                    @keyframes wave-pulse {
                        0% { transform: scale(0.85); opacity: 0.2; }
                        50% { transform: scale(1); opacity: 0.8; }
                        100% { transform: scale(1.15); opacity: 0.2; }
                    }

                    /* Load balancer routing signal */
                    @keyframes route-signal {
                        0% { transform: translate(0, 0); opacity: 1; }
                        30% { transform: translate(-10px, 16px); opacity: 0.9; }
                        60% { transform: translate(-10px, 16px); opacity: 0; }
                        100% { transform: translate(-10px, 16px); opacity: 0; }
                    }

                    /* Quota console charts bar rise */
                    @keyframes chart-bar-1 { 0% { height: 10px; y: 60px; } 100% { height: 35px; y: 35px; } }
                    @keyframes chart-bar-2 { 0% { height: 5px; y: 65px; } 100% { height: 45px; y: 25px; } }
                    @keyframes chart-bar-3 { 0% { height: 15px; y: 55px; } 100% { height: 40px; y: 30px; } }

                    /* High performance gateway speed lines */
                    @keyframes speed-line-1 {
                        0% { transform: translateX(-40px); opacity: 0; }
                        10% { opacity: 1; }
                        90% { opacity: 1; }
                        100% { transform: translateX(100px); opacity: 0; }
                    }
                    @keyframes speed-line-2 {
                        0% { transform: translateX(-60px); opacity: 0; }
                        10% { opacity: 1; }
                        90% { opacity: 1; }
                        100% { transform: translateX(80px); opacity: 0; }
                    }
                    @keyframes speed-line-3 {
                        0% { transform: translateX(-30px); opacity: 0; }
                        10% { opacity: 1; }
                        90% { opacity: 1; }
                        100% { transform: translateX(110px); opacity: 0; }
                    }

                    /* Developer Guide & FAQ */
                    .guide-section {
                        margin-top: 120px;
                        margin-bottom: 100px;
                        position: relative;
                        z-index: 25;
                        padding: 0 24px;
                        max-width: 1200px;
                        margin-left: auto;
                        margin-right: auto;
                    }

                    .guide-container {
                        background: var(--card-bg);
                        border: 1px solid var(--border);
                        border-radius: 24px;
                        padding: 40px;
                        display: grid;
                        grid-template-columns: 1.1fr 0.9fr;
                        gap: 40px;
                        backdrop-filter: blur(12px);
                        -webkit-backdrop-filter: blur(12px);
                        box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                    }

                    .guide-info {
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    }

                    .guide-badge {
                        background: rgba(41, 141, 255, 0.08);
                        border: 1px solid rgba(var(--accent-rgb), 0.15);
                        color: var(--accent);
                        font-size: 12px;
                        font-weight: 600;
                        text-transform: uppercase;
                        padding: 4px 12px;
                        border-radius: 6px;
                        width: fit-content;
                        margin-bottom: 16px;
                        letter-spacing: 0.5px;
                    }

                    .guide-info h3 {
                        font-family: 'Outfit', sans-serif;
                        font-size: 30px;
                        font-weight: 700;
                        margin-bottom: 16px;
                        color: #ffffff;
                    }

                    .guide-info p {
                        font-size: 15px;
                        color: var(--text-secondary);
                        line-height: 1.6;
                        margin-bottom: 28px;
                    }

                    .guide-tabs {
                        display: flex;
                        gap: 12px;
                        border-bottom: 1px solid var(--border);
                        margin-bottom: 20px;
                    }

                    .guide-tab {
                        background: transparent;
                        border: none;
                        color: var(--text-secondary);
                        font-weight: 600;
                        font-size: 14px;
                        cursor: pointer;
                        padding: 8px 16px;
                        border-bottom: 2px solid transparent;
                        transition: all 0.2s;
                        outline: none;
                    }

                    .guide-tab.active {
                        color: var(--accent);
                        border-bottom-color: var(--accent);
                    }

                    .guide-tab:hover:not(.active) {
                        color: var(--text-primary);
                    }

                    .console-container {
                        background: #070913;
                        border-radius: 16px;
                        border: 1px solid var(--border);
                        overflow: hidden;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                        display: flex;
                        flex-direction: column;
                        min-height: 300px;
                    }

                    .console-header {
                        background: #0c0e1e;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                        padding: 12px 18px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                    }

                    .console-dots {
                        display: flex;
                        gap: 6px;
                    }

                    .console-dot {
                        width: 10px;
                        height: 10px;
                        border-radius: 50%;
                    }

                    .console-dot-r { background: #ef4444; }
                    .console-dot-y { background: #f59e0b; }
                    .console-dot-g { background: #10b981; }

                    .console-lang {
                        font-size: 11px;
                        font-weight: 600;
                        color: #64748b;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }

                    .console-body {
                        padding: 20px;
                        flex-grow: 1;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        position: relative;
                    }

                    .guide-content {
                        display: none;
                        margin: 0;
                    }

                    .guide-content.active {
                        display: block;
                    }

                    .guide-content pre {
                        margin: 0;
                        font-family: 'Fira Code', 'Courier New', Courier, monospace;
                        font-size: 13px;
                        line-height: 1.6;
                        overflow-x: auto;
                        color: #e2e8f0;
                    }

                    .console-copy-btn {
                        position: absolute;
                        bottom: 16px;
                        right: 16px;
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.08);
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-size: 12px;
                        font-weight: 500;
                        color: #94a3b8;
                        cursor: pointer;
                        transition: all 0.2s;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }

                    .console-copy-btn:hover {
                        background: rgba(255,255,255,0.1);
                        color: #ffffff;
                        border-color: rgba(var(--accent-rgb), 0.2);
                    }

                    .faq-section {
                        margin-bottom: 40px;
                        position: relative;
                        z-index: 25;
                        padding: 0 24px;
                        max-width: 800px;
                        margin-left: auto;
                        margin-right: auto;
                    }

                    .section-title {
                        font-family: 'Outfit', sans-serif;
                        font-size: 38px;
                        font-weight: 700;
                        text-align: center;
                        margin-bottom: 16px;
                        letter-spacing: -0.5px;
                        color: #ffffff;
                    }

                    .section-subtitle {
                        text-align: center;
                        font-size: 16px;
                        color: var(--text-secondary);
                        max-width: 600px;
                        margin: 0 auto 52px auto;
                        line-height: 1.5;
                    }

                    .faq-list {
                        display: flex;
                        flex-direction: column;
                        gap: 16px;
                    }

                    .faq-item {
                        background: var(--card-bg);
                        border: 1px solid var(--border);
                        border-radius: 16px;
                        overflow: hidden;
                        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                        cursor: pointer;
                        backdrop-filter: blur(12px);
                        -webkit-backdrop-filter: blur(12px);
                    }

                    .faq-item:hover {
                        border-color: var(--card-hover-border);
                        box-shadow: 0 4px 20px var(--glow-color);
                    }

                    .faq-question {
                        padding: 20px 24px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        font-weight: 600;
                        font-size: 16px;
                        color: var(--text-primary);
                        user-select: none;
                    }

                    .faq-icon {
                        font-size: 14px;
                        color: var(--text-secondary);
                        transition: transform 0.3s ease;
                    }

                    .faq-item.active .faq-icon {
                        transform: rotate(180deg);
                        color: var(--accent);
                    }

                    .faq-answer {
                        max-height: 0;
                        overflow: hidden;
                        padding: 0 24px;
                        color: var(--text-secondary);
                        font-size: 14px;
                        line-height: 1.6;
                        transition: max-height 0.35s cubic-bezier(0.16, 1, 0.3, 1), padding 0.35s cubic-bezier(0.16, 1, 0.3, 1);
                    }

                    .faq-item.active .faq-answer {
                        max-height: 250px;
                        padding-bottom: 24px;
                    }

                    .landing-bottom-spacer {
                        height: 60px;
                    }

                    /* ===== sui.io noise grain layer ===== */
                    #aetherverse-landing::before {
                        content: "";
                        position: absolute;
                        inset: 0;
                        z-index: 1;
                        opacity: 0.045;
                        pointer-events: none;
                        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
                    }

                    /* ===== Staggered text reveal ===== */
                    .reveal-text {
                        display: inline-flex;
                        flex-wrap: wrap;
                        justify-content: center;
                        row-gap: 8px;
                        column-gap: 24px;
                    }
                    .reveal-text span {
                        display: inline-block;
                        opacity: 0;
                        filter: blur(16px);
                        transform: translateY(24px) scale(0.94);
                        animation: reveal-blur-word 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                    }
                    @keyframes reveal-blur-word {
                        to {
                            opacity: 1;
                            filter: blur(0px);
                            transform: translateY(0) scale(1);
                        }
                    }

                    /* ===== Spotlight text gradient (.sharp follows --text-x/y) ===== */
                    .sharp {
                        background-color: #298dff;
                        -webkit-background-clip: text;
                        background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-image: radial-gradient(
                            circle at var(--text-x) var(--text-y),
                            #ffffff 0%,
                            #ffffff 44%,
                            #298dff 85%,
                            rgba(41,141,255,0.1) 95%
                        );
                        background-size: 100% 100%;
                        background-repeat: no-repeat;
                        transform: translateZ(0);
                        backface-visibility: hidden;
                        will-change: background-image;
                    }

                    /* Spotlight backdrop blur masks from sui.io */
                    .gradient-blur {
                        position: absolute;
                        inset: 0;
                        pointer-events: none;
                        z-index: 5;
                        contain: layout style paint;
                        transform: translateZ(0);
                    }

                    .gradient-blur > div {
                        position: absolute;
                        inset: 0;
                        transform: translate3d(0, 0, 0);
                        backface-visibility: hidden;
                        pointer-events: none;
                    }

                    .gradient-blur > div:nth-of-type(1) {
                        backdrop-filter: blur(2.8px);
                        -webkit-backdrop-filter: blur(2.8px);
                        mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 14%, black 20%);
                        -webkit-mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 14%, black 20%);
                    }

                    .gradient-blur > div:nth-of-type(2) {
                        backdrop-filter: blur(4px);
                        -webkit-backdrop-filter: blur(4px);
                        mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 16%, black 38%);
                        -webkit-mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 16%, black 38%);
                    }

                    .gradient-blur > div:nth-of-type(3) {
                        backdrop-filter: blur(7px);
                        -webkit-backdrop-filter: blur(7px);
                        mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 18%, black 50%);
                        -webkit-mask: radial-gradient(circle at var(--mouse-x) var(--mouse-y), transparent 0%, transparent 18%, black 50%);
                    }

                    @media (max-width: 1024px) {
                        .guide-container {
                            grid-template-columns: 1fr;
                        }
                    }
                </style>

                <!-- 100% Raw extracted Webflow layout from sui.io --><style>#aetherverse-landing .home-hero_marquee-ltem{display:flex;align-items:center;justify-content:center;min-width:200px;padding:0 24px}#aetherverse-landing .av-marquee-text{display:inline-flex;align-items:center;font-family:"Inter",sans-serif;font-size:clamp(16px,2.2vw,22px);font-weight:600;letter-spacing:.02em;color:#fff;white-space:nowrap;opacity:.82}#aetherverse-landing .home-carousel.cusotm_gap{padding-top:0}#aetherverse-landing .hero_heading{font-family:"Outfit","Inter",sans-serif}</style>
                <div home-trigger="" class="seqtrigger"><div class="gradient_background"><div class="blue_overlay z_index10"></div><div inner-fixed-load="" class="hero_overlay"><div inner-fixed-load-background="" class="background_intro"></div><div class="stage"><div class="w-embed"><style>
.stage { container-type: inline-size; }
.ball.lightblue { filter: blur(clamp(60px, 12cqw, 172px)); }
.ball.blue      { filter: blur(clamp(60px, 12cqw, 172px)); }
.ball.black     { filter: blur(clamp(80px, 16cqw, 230px)); }
</style></div><div class="ball lightblue"></div><div class="ball blue"></div><div class="ball black"></div><div class="cutout"></div></div><canvas id="noise" class="noise _100svh"></canvas></div><section class="hero-section"><div class="intro_holder"><div class="intro_map"><div class="line_progress"><div class="current_percent"><div class="percent_wrapper"><div class="block-12 bg-primary-blue"></div><div class="ts-16px color-white padding-bottom">0%</div></div></div><div class="line_current"><img src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/6901316af5849175ac89f762_Frame%202147267312%20(1).avif" loading="eager" alt="" class="image-9"/><div class="black_overlay"></div></div></div></div></div><div class="hero_first_section"><div class="gradient-blur"><div></div><div></div><div></div></div><div class="text-layers"><div class="first_section_content"><h1 class="hero_heading absolute sharp mobileonly">AetherVerse</h1><h1 class="hero_heading absolute sharp desktoponly">AetherVerse</h1></div></div></div><div class="first_section_content_2 subhead-block"><span data-split="lines" class="ts-21px color-white text-center hero-custom-break mob_15px">好友共享的 API 负载均衡网关</span><div class="cta-wrapper width_auto"><a id="w-node-ea6c916b-f8f4-5e35-fc7f-a7ca22081870-4b72e4d1" global="textStagger" href="#dev-guide" target="_self" class="cta-button"><span>查看接入文档</span></a><a global="textStagger" href="\${isLogged ? '/panel' : '/login'}" target="_self" class="cta-button is--alternative"><span>立即开始</span></a></div></div></section><section starting-section="" class="home-carousel cusotm_gap"><div class="padding-global"><div data-split="" class="w-layout-vflex vx-center"><div class="mob-land_mw-420 mob_mw-320"><div global="revealTextLines" class="home-carousel-heading">一个号池，九大模型，好友之间无限共享</div></div></div></div></section></div><section starting-section="" class="home-carousel"><div data-carousel="" data-carousel-speed="75" data-carousel-duplicate="2" class="carousel"><div data-carousel-track="" class="carousel__track"><div data-carousel-item="" class="carousel__item"><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">DeepSeek</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">GLM · 智谱</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">Kimi · Moonshot</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">MiniMax</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">混元 Hunyuan</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">CodeBuddy</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">OpenAI 兼容</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">Claude 兼容</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">流式输出</span></div><div class="home-hero_marquee-ltem marquee-item_mob"><span class="av-marquee-text">自动签到</span></div></div></div></div></section><div class="stickyblink"><section class="blink_wrap"><div reveal-gradient="" class="padding-global"><div class="container-1400"><div global-stickyBlink="" class="w-layout-vflex home-trust_layout"><div class="w-layout-vflex gap-12 mobilegap-24"><span class="gray_span">额度，重新定义于共享</span><div global="initHighlight" class="reveal-lines"><span class="custom-span block">AetherVerse 让好友的账号、额度与模型能力被真正共享、</span><div class="custom-span">智能调度，</div><span class="custom-span mobilelineforce">自动续费。结果是？</span><div class="blinkexpander"><div class="custom-span custom no_margin"><div class="icon_expander no_padding"><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9bc8af3e280effd3c61_00%20-%20Products%2C%20apps.json" class="mw-78 background-blue"></div></div><div global-highlight="" class="higlight_wrapper"><span global-highlight-charspace="" class="custom-span invert no-margin">更稳的可用性</span></div></div></div><span class="custom-span breaker_padding">，</span><div class="blinkexpander second_part"><div class="custom-span custom"><div class="icon_expander no_padding"><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9bc5b5c145c44a7d59a_00%20-%20Verified%20user%2C%20user-trust.json" class="mw-78 background-blue"></div></div><div global-highlight="" class="higlight_wrapper"><span global-highlight-char="" class="custom-span invert">真实的额度透明</span></div></div></div><span class="custom-span lineforce margin-top">以及</span><div class="blinkexpander margintop"><div class="custom-span custom"><div class="icon_expander no_padding"><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9bc5f8c97ae78984db4_01%20-%20Sharing%2C%20Shared%20value.json" class="mw-78 background-blue"></div></div><div global-highlight="" class="higlight_wrapper"><span global-highlight-char="" class="custom-span invert no-margin custom-padding">好友间共享的价值</span></div></div><span class="custom-span breaker_padding fontfix">，</span></div><span class="custom-span">而非被消耗。</span></div></div></div></div></div></div></section></div><section class="home-selection"><div class="padding-global"><div class="container-1400"><div class="sui_is_wrapper"><span class="ts-12px mono color-black">[ → ]</span><span id="w-node-_016f7ca4-85d5-1eba-3268-00ae6cf93442-4b72e4d1" class="gray_span">AetherVerse 是</span></div></div></div><div class="home-background"><div class="home-tabs_layout"><div class="svghidden w-embed"><svg xmlns="http://www.w3.org/2000/svg" width="100%" height="8" viewBox="0 0 1401 8" fill="none">
<path d="M4.10547 3.73438H1400.3" stroke="#4B515B" stroke-width="2" stroke-dasharray="2 10"/>
<rect x="0.722656" y="0.335938" width="6.79492" height="6.79492" fill="#298DFF"/>
<rect x="1393.51" y="0.335938" width="6.79492" height="6.79492" fill="#298DFF"/>
</svg></div><div back-to-lenis="" class="padding-global custom_padding"><div class="container-1400"><div class="tabs_layout_wrapper"><div class="tabs_layout_cover"><div class="f_grid_2"><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c5a-4b72e4d1" class="tabs_num"></div><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c5e-4b72e4d1" class="tabs_wrapper first_section"><div class="tabs_content"><div class="content_devider"><h3 global="scrumble" class="h3-60px eventsnone">号池自拥，额度随用</h3><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9b91b0a0a387004ab00_00%20-%20Hand.json" class="mw-64 background-blue"></div></div></div></div></div><div class="f_grid_2"><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c68-4b72e4d1" class="tabs_num"></div><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c6c-4b72e4d1" class="tabs_wrapper"><svg width="100%" height="3" viewBox="0 0 1175 3" class="svgdotted"><path d="M0.308594 1.6875H1174.69" stroke="#A1A7B2" stroke-width="2" stroke-dasharray="2 10"></path></svg><div class="tabs_content"><div class="content_devider"><h3 global="scrumble" class="h3-60px eventsnone">额度透明，账单可查</h3><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9bc5b5c145c44a7d59a_00%20-%20Verified%20user%2C%20user-trust.json" class="mw-64 background-blue"></div></div></div></div></div><div class="f_grid_2"><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c76-4b72e4d1" class="tabs_num"></div><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c7a-4b72e4d1" class="tabs_wrapper"><svg width="100%" height="3" viewBox="0 0 1175 3" class="svgdotted"><path d="M0.308594 1.6875H1174.69" stroke="#A1A7B2" stroke-width="2" stroke-dasharray="2 10"></path></svg><div class="tabs_content"><div class="content_devider"><h3 global="scrumble" class="h3-60px eventsnone">开箱即用，多端兼容</h3><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9b77277e0127a8f48a1_00%20-%20Briefcase%2C%20business.json" class="mw-64 background-blue"></div></div></div></div></div><div class="f_grid_2"><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c84-4b72e4d1" class="tabs_num"></div><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c88-4b72e4d1" class="tabs_wrapper"><svg width="100%" height="3" viewBox="0 0 1175 3" class="svgdotted"><path d="M0.308594 1.6875H1174.69" stroke="#A1A7B2" stroke-width="2" stroke-dasharray="2 10"></path></svg><div class="tabs_content"><div class="content_devider"><h3 global="scrumble" class="h3-60px eventsnone">可组合，可扩展</h3><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9bc5d7c9250f0fd7ccb_00%20-%20Scale.json" class="mw-64 background-blue"></div></div></div></div></div><div class="f_grid_2"><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c92-4b72e4d1" class="tabs_num"></div><div id="w-node-_2574a280-e9bd-6bcc-32cd-ba85d7024c96-4b72e4d1" class="tabs_wrapper custom"><svg width="100%" height="3" viewBox="0 0 1175 3" class="svgdotted"><path d="M0.308594 1.6875H1174.69" stroke="#A1A7B2" stroke-width="2" stroke-dasharray="2 10"></path></svg><div class="tabs_content"><div class="content_devider"><h3 global="scrumble" class="h3-60px eventsnone">高性能，零妥协</h3><div global="lottieReveal" global-src="https://cdn.prod.website-files.com/68e8e0120513ba12c5cd12e0/692ea9ba093fdf59aed4712b_00%20-%20Performance.json" class="mw-64 background-blue"></div></div></div></div></div></div></div></div></div></div></div></section></div>

                <!-- API Base Endpoint Copy Card -->
                <div class="endpoint-container-wrap">
                    <div class="endpoint-container">
                        <span class="endpoint-dot-green"></span>
                        <span class="endpoint-label-text">API Endpoint</span>
                        <span class="url-base">${window.location.origin}</span>
                        <button id="copy-endpoint-btn" class="btn-copy" onclick="aetherverseCopyText('${window.location.origin}', 'copy-endpoint-btn')">
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Code Console & Integration Guide -->
                <div id="dev-guide" class="guide-section">
                    <div class="guide-container">
                        <div class="guide-info">
                            <div class="guide-badge">Developer Guide</div>
                            <h3>极速接入大模型能力</h3>
                            <p>
                                AetherVerse 完全兼容 OpenAI 标准 API 规范，只需更改 Base URL 与 API Key，即可将现有项目无缝迁移至具备智能调度能力的网关服务中。
                            </p>
                            <div class="guide-tabs">
                                <button class="guide-tab active" data-tab="curl" onclick="aetherverseSwitchTab('curl')">cURL</button>
                                <button class="guide-tab" data-tab="python" onclick="aetherverseSwitchTab('python')">Python</button>
                                <button class="guide-tab" data-tab="nodejs" onclick="aetherverseSwitchTab('nodejs')">Node.js</button>
                            </div>
                        </div>

                        <div class="console-container">
                            <div class="console-header">
                                <div class="console-dots">
                                    <div class="console-dot console-dot-r"></div>
                                    <div class="console-dot console-dot-y"></div>
                                    <div class="console-dot console-dot-g"></div>
                                </div>
                                <div class="console-lang">Request Terminal</div>
                            </div>
                            <div class="console-body">
                                <!-- cURL content -->
                                <div id="guide-curl" class="guide-content active">
                                    <pre><span style="color: #64748b;"># 更改 Base URL 即可直接发起请求</span>
curl ${window.location.origin}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer sk-your-api-key" \\
  -d '{
    "model": "deepseek-reasoning",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'</pre>
                                    <button class="console-copy-btn" onclick="aetherverseCopyText('curl ' + window.location.origin + '/v1/chat/completions \\\\n  -H "Content-Type: application/json" \\\\n  -H "Authorization: Bearer sk-your-api-key" \\\\n  -d \'{\\\\n    "model": "deepseek-reasoning",\\\\n    "messages": [{"role": "user", "content": "你好"}],\\\\n    "stream": true\\\\n  }\'', 'copy-code-curl')">
                                        <span id="copy-code-curl">Copy Code</span>
                                    </button>
                                </div>

                                <!-- Python content -->
                                <div id="guide-python" class="guide-content">
                                    <pre><span style="color: #64748b;"># pip install openai</span>
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-api-key",
    base_url="${window.location.origin}/v1"
)

response = client.chat.completions.create(
    model="deepseek-reasoning",
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)</pre>
                                    <button class="console-copy-btn" onclick="aetherverseCopyText('from openai import OpenAI\\\\n\\\\nclient = OpenAI(\\\\n    api_key="sk-your-api-key",\\\\n    base_url=\'' + window.location.origin + '/v1\'\\\\n)\\\\n\\\\nresponse = client.chat.completions.create(\\\\n    model="deepseek-reasoning",\\\\n    messages=[{"role": "user", "content": "你好"}],\\\\n    stream=True\\\\n)', 'copy-code-python')">
                                        <span id="copy-code-python">Copy Code</span>
                                    </button>
                                </div>

                                <!-- Node.js content -->
                                <div id="guide-nodejs" class="guide-content">
                                    <pre><span style="color: #64748b;">// npm install openai</span>
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: "sk-your-api-key",
  baseURL: "${window.location.origin}/v1"
});

const stream = await openai.chat.completions.create({
  model: "deepseek-reasoning",
  messages: [{ role: "user", content: "你好" }],
  stream: true,
});</pre>
                                    <button class="console-copy-btn" onclick="aetherverseCopyText('import OpenAI from "openai";\\\\n\\\\nconst openai = new OpenAI({\\\\n  apiKey: "sk-your-api-key",\\\\n  baseURL: \'' + window.location.origin + '/v1\'\\\\n});\\\\n\\\\nconst stream = await openai.chat.completions.create({\\\\n  model: "deepseek-reasoning",\\\\n  messages: [{ role: "user", content: "你好" }],\\\\n  stream: true,\\\\n});', 'copy-code-node')">
                                        <span id="copy-code-node">Copy Code</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- FAQ Section -->
                <div class="faq-section">
                    <h2 class="section-title">常见问题解答 FAQ</h2>
                    <p class="section-subtitle">关于 AetherVerse API 网关服务的一些常见使用疑虑解答。</p>
                    
                    <div class="faq-list">
                        <div class="faq-item active" onclick="aetherverseToggleFaq(0)">
                            <div class="faq-question">
                                <span>如何快速注册并获取免费额度？</span>
                                <span class="faq-icon">▼</span>
                            </div>
                            <div class="faq-answer">
                                系统面向所有新注册用户默认赠送初始体验额度。您可以前往控制台直接创建一个接口 Key 并调用内置模型进行测试。
                            </div>
                        </div>
                        
                        <div class="faq-item" onclick="aetherverseToggleFaq(1)">
                            <div class="faq-question">
                                <span>如何参与微信账号绑定共享，免费刷新接口额度？</span>
                                <span class="faq-icon">▼</span>
                            </div>
                            <div class="faq-answer">
                                登录系统后，点击左侧菜单的<strong>“CodeBuddy 控制台”</strong>，您可以通过扫码或输入 API Key 绑定 WorkBuddy 账号，将您的免费额度接入公共共享池。系统会自动帮大家签到和刷新额度。绑定账号越多，可用资源越稳定！
                            </div>
                        </div>
                        
                        <div class="faq-item" onclick="aetherverseToggleFaq(2)">
                            <div class="faq-question">
                                <span>支持哪些模型，是否有额度计费限制？</span>
                                <span class="faq-icon">▼</span>
                            </div>
                            <div class="faq-answer">
                                目前支持 DeepSeek (pro/flash)、智谱 (5.2/5.1/5v)、Kimi (2.7-code/2.6)、腾讯混元、MiniMax。后台会精确统计每次调用消耗的实际 Token 数量（含输入、输出及缓存命中率），并换算成额度从您的令牌中扣除。
                            </div>
                        </div>
                        
                        <div class="faq-item" onclick="aetherverseToggleFaq(3)">
                            <div class="faq-question">
                                <span>偶尔报错“渠道已关闭”或“额度不足”怎么办？</span>
                                <span class="faq-icon">▼</span>
                            </div>
                            <div class="faq-answer">
                                偶尔报错通常是公共池中某个子账号的当天免费额度被瞬间跑满，或者该账号由于微信断连正在被系统清理。系统检测到后会自动切换轮询到其他可用渠道，您只需要在客户端中<strong>重试一次</strong>即可成功。
                            </div>
                        </div>

                        <div class="faq-item" onclick="aetherverseToggleFaq(4)">
                            <div class="faq-question">
                                <span>如何保证我的共享微信账号安全？</span>
                                <span class="faq-icon">▼</span>
                            </div>
                            <div class="faq-answer">
                                系统的“微信自动打卡”仅调用 WorkBuddy 的开放桌面通道与 API 进行每日一次的自动打卡。系统不会以任何形式收集或读取您的私人聊天记录，请放心使用。
                            </div>
                        </div>
                    </div>
                </div>
                <div class="landing-bottom-spacer"></div>
            `;
        });
    }

    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;
    let isIdle = true;
    let angle = 0;
    let spotlightRafId = null;

    // Gated, leak-free spotlight requestAnimationFrame loop
    function updateSpotlight() {
        if (document.hidden) { spotlightRafId = null; return; }
        if (!document.body.classList.contains('landing-active')) { spotlightRafId = null; return; }
        const landing = document.getElementById('aetherverse-landing');
        const blurEl = landing ? landing.querySelector('.gradient-blur') : null;
        if (!landing || !blurEl) { spotlightRafId = null; return; }
        
        const cs = getComputedStyle(blurEl);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) {
            spotlightRafId = null;
            return;
        }

        const rect = blurEl.getBoundingClientRect();
        if (isIdle) {
            angle += 0.012;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            targetX = centerX + Math.cos(angle) * 150;
            targetY = centerY + Math.sin(angle) * 80;
        }

        mouseX += (targetX - mouseX) * 0.08;
        mouseY += (targetY - mouseY) * 0.08;

        landing.style.setProperty('--mouse-x', `${mouseX}px`);
        landing.style.setProperty('--mouse-y', `${mouseY}px`);

        const heroSection = landing.querySelector('.hero_first_section');
        if (heroSection) {
            const heroRect = heroSection.getBoundingClientRect();
            const textX = heroRect.width ? ((mouseX + rect.left - heroRect.left) / heroRect.width) * 100 : 50;
            const textY = heroRect.height ? ((mouseY + rect.top - heroRect.top) / heroRect.height) * 100 : 50;
            landing.style.setProperty('--text-x', `${textX}%`);
            landing.style.setProperty('--text-y', `${textY}%`);
        }
        spotlightRafId = requestAnimationFrame(updateSpotlight);
    }

    function startSpotlight() {
        if (spotlightRafId !== null) return;                       // already running
        if (!document.body.classList.contains('landing-active')) return;
        spotlightRafId = requestAnimationFrame(updateSpotlight);
    }

    function stopSpotlight() {
        if (spotlightRafId !== null) {
            cancelAnimationFrame(spotlightRafId);
            spotlightRafId = null;
        }
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) stopSpotlight();
        else startSpotlight();
    });

    document.addEventListener('mousemove', (e) => {
        if (!document.body.classList.contains('landing-active')) return;
        const blurEl = document.querySelector('#aetherverse-landing .gradient-blur');
        if (blurEl) {
            const rect = blurEl.getBoundingClientRect();
            isIdle = false;
            targetX = e.clientX - rect.left;
            targetY = e.clientY - rect.top;
        }
    });

    document.addEventListener('mouseleave', () => {
        isIdle = true;
    });

    window.__gsapReady = false;
    // Slater calls window.onWeglotReady (Weglot translation lib) which we don't ship;
    // stub it so Slater's init doesn't throw.
    if (typeof window.onWeglotReady !== 'function') {
        window.onWeglotReady = function() {};
    }
    function startAetherverseGsapLoading() {
        if (window.__gsapReady) {
            loadSlater();
            return;
        }
        
        var base = 'https://cdn.prod.website-files.com/gsap/3.15.0/';
        var files = [
          'gsap.min.js',
          'ScrollTrigger.min.js',
          'SplitText.min.js',
          'CustomEase.min.js',
          'InertiaPlugin.min.js',
          'Observer.min.js',
          'Draggable.min.js',
          'DrawSVGPlugin.min.js',
          'ScrambleTextPlugin.min.js',
          'MorphSVGPlugin.min.js',
          'Flip.min.js'
        ];
        var loaded = 0;
        files.forEach(function(file) {
          let existing = document.querySelector(`script[src*="${file}"]`);
          if (existing) {
             if (++loaded === files.length) {
                window.__gsapReady = true;
                loadSlater();
             }
             return;
          }
          var s = document.createElement('script');
          s.src = base + file;
          s.className = 'aetherverse-gsap-script';
          s.onload = function() {
            if (++loaded === files.length) {
              gsap.registerPlugin(
                ScrollTrigger, SplitText, CustomEase, InertiaPlugin,
                Observer, Draggable, DrawSVGPlugin, ScrambleTextPlugin,
                MorphSVGPlugin, Flip
              );
              window.__gsapReady = true;
              loadSlater();
            }
          };
          document.head.appendChild(s);
        });
    }

    function loadSlater() {
        let oldSlater = document.getElementById('aetherverse-slater');
        if (oldSlater) oldSlater.remove();

        // sui.io drives smooth-scroll via Lenis, which intercepts wheel/touch
        // (preventDefault) and translates them into a virtual rAF-driven scroll.
        // Inside our embedded landing the document scrolls NATIVELY, so that
        // interception just swallows the mouse wheel — the page won't scroll
        // (programmatic scroll still works, confirming the wheel is being eaten),
        // and Lenis's rAF loop leaks CPU/GPU even after leaving the page.
        // Replace window.Lenis with an inert stub BEFORE Slater runs, so its
        // `new Lenis()` is a no-op: no wheel/touch listeners, no preventDefault,
        // no rAF. GSAP ScrollTrigger still animates because it listens to native
        // scroll on window. scrollTo() delegates to native smooth scroll so
        // Slater's in-page anchor scrolls keep working.
        if (!window.__aetherverseLenisStubbed) {
            window.__aetherverseLenisStubbed = true;
            function LenisStub(opts) {
                this.options = opts || {};
                this.isStopped = false; this.isSmooth = false;
                this.isScrolling = false; this.velocity = 0;
                this.scroll = 0; this.animatedScroll = 0; this.limit = 0; this.time = 0;
                this.targetScroll = 0; this.actualScroll = 0; this.direction = 0;
                this.rootElement = window; this.wrapperEl = window; this.contentEl = document.documentElement;
                // Wrap the instance in a Proxy so ANY method Slater calls that we
                // didn't explicitly define becomes a safe no-op (returning the
                // instance for chaining) instead of throwing.
                const self = this;
                return new Proxy(self, {
                    get(target, prop) {
                        if (prop in target) return target[prop];
                        if (typeof prop === 'string') {
                            return function () { return self; }; // chainable no-op
                        }
                        return undefined;
                    }
                });
            }
            const noopChain = function (self) { return function () { return self; }; };
            LenisStub.prototype.on = noopChain(this);
            LenisStub.prototype.off = noopChain(this);
            LenisStub.prototype.emit = noopChain(this);
            LenisStub.prototype.destroy = noopChain(this);
            LenisStub.prototype.stop = function () { this.isStopped = true; return this; };
            LenisStub.prototype.start = function () { this.isStopped = false; return this; };
            LenisStub.prototype.setScroll = noopChain(this);
            LenisStub.prototype.onVirtualScroll = noopChain(this);
            LenisStub.prototype.notify = noopChain(this);
            LenisStub.prototype.reset = noopChain(this);
            LenisStub.prototype.raf = function (t) { this.time = t; return this; }; // no rAF added
            LenisStub.prototype.scrollTo = function (target, o) {
                o = o || {};
                let y = 0;
                if (typeof target === 'number') y = target;
                else if (typeof target === 'string') {
                    const el = document.querySelector(target);
                    if (el) y = el.getBoundingClientRect().top + window.scrollY;
                } else if (target && typeof target.getBoundingClientRect === 'function') {
                    y = target.getBoundingClientRect().top + window.scrollY;
                } else if (target && typeof target === 'object' && typeof target.offsetTop === 'number') {
                    y = target.offsetTop;
                }
                try { window.scrollTo({ top: Math.max(0, y), behavior: o.immediate ? 'auto' : 'smooth' }); } catch (e) { window.scrollTo(0, Math.max(0, y)); }
                return this;
            };
            window.Lenis = LenisStub;
        }

        injectSlater();
    }

    function injectSlater() {
        var src = "https://assets.slater.app/slater/17378.js?v=" + Date.now();
        var s = document.createElement('script');
        s.id = 'aetherverse-slater';
        s.src = src;
        s.type = 'module';
        document.head.appendChild(s);
    }

    function unloadAetherverseGsap() {
        let slater = document.getElementById('aetherverse-slater');
        if (slater) slater.remove();
        let lenis = document.getElementById('aetherverse-lenis');
        if (lenis) lenis.remove();
        // Kill all active ScrollTriggers + any in-flight tweens so their rAF
        // callbacks stop firing after leaving the landing page.
        try {
            if (window.ScrollTrigger) {
                ScrollTrigger.getAll().forEach(t => t.kill());
            }
            if (window.gsap) {
                gsap.killTweensOf("*");
                gsap.globalTimeline.clear();
            }
        } catch (e) {}
        stopSpotlight();
    }

    function styleHeader(isLandingActive) {
        const headerElements = document.querySelectorAll('.semi-layout-header, .ant-layout-header, header, .semi-navigation, .semi-navigation-header, .ant-menu-horizontal, .ant-layout-header .ant-menu');
        headerElements.forEach(el => {
            if (isLandingActive) {
                el.style.setProperty('background', 'transparent', 'important');
                el.style.setProperty('background-color', 'transparent', 'important');
                el.style.setProperty('border-bottom', '1px solid rgba(255, 255, 255, 0.08)', 'important');
                el.style.setProperty('box-shadow', 'none', 'important');
                el.style.setProperty('backdrop-filter', 'blur(20px)', 'important');
                el.style.setProperty('-webkit-backdrop-filter', 'blur(20px)', 'important');
            } else {
                el.style.removeProperty('background');
                el.style.removeProperty('background-color');
                el.style.removeProperty('border-bottom');
                el.style.removeProperty('box-shadow');
                el.style.removeProperty('backdrop-filter');
                el.style.removeProperty('-webkit-backdrop-filter');
            }
        });

        const textElements = document.querySelectorAll('.semi-layout-header *, .semi-navigation *, .ant-layout-header *, header *');
        textElements.forEach(el => {
            if (el.closest('.semi-portal') || el.closest('.ant-select-dropdown') || el.closest('.ant-dropdown')) {
                return;
            }
            if (isLandingActive) {
                el.style.setProperty('color', '#ffffff', 'important');
            } else {
                el.style.removeProperty('color');
            }
        });

        const svgElements = document.querySelectorAll('.semi-layout-header svg, .semi-navigation svg, header svg, .ant-layout-header svg');
        svgElements.forEach(el => {
            if (isLandingActive) {
                el.style.setProperty('fill', '#ffffff', 'important');
                el.style.setProperty('color', '#ffffff', 'important');
            } else {
                el.style.removeProperty('fill');
                el.style.removeProperty('color');
            }
        });
        
        const layoutElements = document.querySelectorAll('.semi-layout, .ant-layout, body');
        const radialGradient = 'radial-gradient(circle at 50% -20%, rgba(41, 141, 255, 0.28) 0%, rgba(41, 141, 255, 0) 50%), radial-gradient(circle at 50% 40%, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0) 60%), radial-gradient(circle at 50% -50px, #0f172a 0%, #030712 100%)';
        layoutElements.forEach(el => {
            if (isLandingActive) {
                el.style.setProperty('background', radialGradient, 'important');
                el.style.setProperty('background-color', '#030712', 'important');
            } else {
                el.style.removeProperty('background');
                el.style.removeProperty('background-color');
            }
        });
    }

    function setupScrollTimeline() {
        const cards = document.querySelectorAll('.colum_card_main');
        const scrollHandler = () => {
            const viewportHeight = window.innerHeight;
            cards.forEach(card => {
                const rect = card.getBoundingClientRect();
                if (rect.top < viewportHeight * 0.88) {
                    card.classList.add('reveal');
                }
            });
        };
        window.addEventListener('scroll', scrollHandler);
        scrollHandler();
    }

    function handleRouting() {
        const isLanding = window.location.pathname === '/';
        
        // Dynamic import of sui.io stylesheet to avoid pollution on admin dashboard
        let suiCssLink = document.getElementById('sui-theme-css');
        if (isLanding) {
            if (!suiCssLink) {
                suiCssLink = document.createElement('link');
                suiCssLink.id = 'sui-theme-css';
                suiCssLink.rel = 'stylesheet';
                suiCssLink.href = window.location.protocol + '//' + window.location.hostname + ':8000/sui-sandbox.css';
                document.head.appendChild(suiCssLink);
                
                // Load GSAP and Slater JS on landing page mount
                startAetherverseGsapLoading();
            }
        } else {
            if (suiCssLink) {
                suiCssLink.remove();
                unloadAetherverseGsap();
            }
        }
        
        const contentArea = document.querySelector('.semi-layout-content, .ant-layout-content, main');
        styleHeader(isLanding);
        
        if (contentArea && contentArea.parentNode) {
            let landingEl = document.getElementById('aetherverse-landing');
            
            if (isLanding) {
                if (!document.body.classList.contains('landing-active')) {
                    document.body.classList.add('landing-active');
                }

                if (!landingEl || landingEl.parentNode !== contentArea.parentNode) {
                    if (landingEl) {
                        landingEl.remove();
                    }
                    landingEl = document.createElement('div');
                    landingEl.id = 'aetherverse-landing';
                    contentArea.parentNode.appendChild(landingEl);
                    renderLandingPage(landingEl);
                    setupScrollTimeline();
                } else {
                    landingEl.style.display = 'block';
                }
                startSpotlight();
            } else {
                if (document.body.classList.contains('landing-active')) {
                    document.body.classList.remove('landing-active');
                }
                if (landingEl) {
                    landingEl.remove();
                }
                stopSpotlight();
            }
        }
    }

    // Set routing checker interval to handle dynamically routed SPA path transitions instantly
    setInterval(handleRouting, 150);

    // Global listener for click events inside header nav items to scroll smoothly
    document.addEventListener('click', (e) => {
        const targetLink = e.target.closest('#aetherverse-landing a[href^="#"], #aetherverse-landing .btn-hero-secondary[href^="#"]');
        if (targetLink) {
            e.preventDefault();
            const targetId = targetLink.getAttribute('href');
            const targetEl = document.querySelector(targetId);
            if (targetEl) {
                targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }, true);

    // ----------------------------------------------------
    // Existing Admin Panel Insertion Code
    // ----------------------------------------------------
    setInterval(init, 1000);
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Intercept pushState & replaceState to hide our iframe
    const originalPushState = history.pushState;
    history.pushState = function() {
        hidePanel();
        originalPushState.apply(this, arguments);
        setTimeout(() => {
            init();
            handleRouting();
        }, 100);
    };
    
    const originalReplaceState = history.replaceState;
    history.replaceState = function() {
        hidePanel();
        originalReplaceState.apply(this, arguments);
        setTimeout(() => {
            init();
            handleRouting();
        }, 100);
    };
    
    window.addEventListener('popstate', () => {
        hidePanel();
        handleRouting();
    });
    
    window.addEventListener('hashchange', () => {
        hidePanel();
        handleRouting();
    });

    // Global click listener to detect navigation away from checkin
    document.addEventListener('click', (e) => {
        const isCheckinClick = e.target.closest('#checkin-menu-item, #checkin-menu-link, #checkin-link');
        if (!isCheckinClick) {
            const isNavLink = e.target.closest('a, .semi-navigation-item, .ant-menu-item');
            if (isNavLink) {
                hidePanel();
            }
        }
    }, true);
})();
