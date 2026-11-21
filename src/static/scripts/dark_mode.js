(function initDarkMode() {
    const THEME_KEY = 'inkypi-theme';
    const DARK_THEME = 'dark';
    const LIGHT_THEME = 'light';
    function getCurrentTheme() {
        const stored = localStorage.getItem(THEME_KEY);
        if (stored) {
            return stored;
        }
        if (window.matchMedia && window.matchMedia('(предпочитает цветовую схему: темную)').matches) {
            return DARK_THEME;
        }
        return LIGHT_THEME;
    }
    function setTheme(theme) {
        const html = document.documentElement;
        if (theme === DARK_THEME) {
            html.setAttribute('data-theme', DARK_THEME);
        } else {
            html.removeAttribute('data-theme');
        }
        localStorage.setItem(THEME_KEY, theme);
        updateToggleButtonText(theme);
    }
    function updateToggleButtonText(theme) {
        const toggleButton = document.querySelector('.dark-mode-toggle');
        if (toggleButton) {
            const hoverText = theme === DARK_THEME ? 'Переключить режим освещения' : 'Переключить темный режим';
            toggleButton.setAttribute('data-hover-text', hoverText);
        }
    }
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === DARK_THEME ? LIGHT_THEME : DARK_THEME;
        setTheme(newTheme);
    }
    function initialize() {
        const theme = getCurrentTheme();
        setTheme(theme);
        const toggleButton = document.querySelector('.dark-mode-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', function (e) {
                e.preventDefault();
                toggleTheme();
            });
        }
        if (window.matchMedia) {
            window.matchMedia('(предпочитает цветовую схему: темную)').addEventListener('change', (e) => {
                if (!localStorage.getItem(THEME_KEY)) {
                    setTheme(e.matches ? DARK_THEME : LIGHT_THEME);
                }
            });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    window.toggleDarkMode = toggleTheme;
})();