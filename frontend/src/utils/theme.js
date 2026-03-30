const THEME_KEY = 'app-theme'

export function applyTheme(theme) {
    const html = document.documentElement

    if (theme === 'dark') {
        html.classList.add('app-dark')
    } else {
        html.classList.remove('app-dark')
    }

    localStorage.setItem(THEME_KEY, theme)
}

export function getSavedTheme() {
    return localStorage.getItem(THEME_KEY) || 'light'
}

export function initTheme() {
    const savedTheme = getSavedTheme()
    applyTheme(savedTheme)
}

export function toggleTheme() {
    const currentTheme = getSavedTheme()
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark'
    applyTheme(nextTheme)
    return nextTheme
}