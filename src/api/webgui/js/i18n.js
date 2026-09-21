/**
 * i18n.js — Internationalization module
 * 
 * Uses i18next (loaded via CDN in index.html).
 * 
 * HTML attribute conventions:
 *   data-i18n="key"             — sets element innerHTML
 *   data-i18n-placeholder="key" — sets input/textarea placeholder
 *   data-i18n-title="key"       — sets title attribute
 * 
 * Selected language is saved to localStorage.
 * On load: reads language from localStorage, falls back to browser lang, then 'en'.
 */

const SUPPORTED = ['en', 'ru', 'he'];

let i18nInitialized = false;

let eventsBound = false;

function setupLanguageEvents() {
    if (eventsBound) return;
    eventsBound = true;
    document.addEventListener('change', (e) => {
        if (e.target && e.target.classList.contains('lang-selector')) {
            switchLang(e.target.value);
        }
    });
}

/**
 * Initialize i18next and apply translations to the DOM.
 * Called once from main.js after DOMContentLoaded.
 * @param {string} lang - language code (may be empty)
 */
export async function initI18n(lang) {
    // If lang is explicitly set — use it.
    // If empty/null — detect from localStorage, browser, fall back to 'en'.
    const resolved = SUPPORTED.includes(lang) ? lang : detectLang();

    // Always load English as fallback bundle
    const [mainRes, enRes] = await Promise.all([
        loadLocale(resolved),
        resolved !== 'en' ? loadLocale('en') : Promise.resolve(null),
    ]);

    await i18next.init({
        lng: resolved,
        fallbackLng: 'en',
        resources: { [resolved]: { translation: mainRes } },
        interpolation: { escapeValue: false },
    });

    if (enRes) {
        i18next.addResourceBundle('en', 'translation', enRes, true, true);
    }

    document.documentElement.setAttribute('lang', resolved);
    document.documentElement.setAttribute('dir', resolved === 'he' ? 'rtl' : 'ltr');

    applyTranslations();
    syncSelectors(resolved);
    setupLanguageEvents();
    i18nInitialized = true;
}

/**
 * Switch language, re-apply all translations, save to localStorage.
 * @param {string} lang
 */
export async function switchLang(lang) {
    if (!SUPPORTED.includes(lang)) return;

    // Lazy-load locale bundle if not yet loaded
    if (!i18next.hasResourceBundle(lang, 'translation')) {
        const res = await loadLocale(lang);
        i18next.addResourceBundle(lang, 'translation', res, true, true);
    }

    await i18next.changeLanguage(lang);

    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('dir', lang === 'he' ? 'rtl' : 'ltr');

    applyTranslations();
    syncSelectors(lang);

    // Persist to localStorage
    localStorage.setItem('app_language', lang);

    // Dispatch global event for listeners across tabs/components
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

/**
 * Walk the DOM and update all elements with data-i18n* attributes.
 * Safe to call multiple times — idempotent.
 */
export function applyTranslations() {
    // Text / HTML content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.innerHTML = val;
    });

    // Input / textarea placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.placeholder = val;
    });

    // Tooltip / title attribute
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.title = val;
    });
}

async function loadLocale(lang, bundle = 'main') {
    const pathName = window.location.pathname;
    let paths = [];
    
    if (pathName.includes('/user_tts')) {
        paths = [
            `/html/locales/${lang}.json`,
            `/html/user_tts/locales/user_${lang}.json`
        ];
    } else {
        paths = [
            `/html/locales/${lang}.json`,
            `/html/locales/user_${lang}.json`
        ];
    }
    
    for (const path of paths) {
        try {
            const cacheBustUrl = `${path}?v=${Date.now()}`;
            const r = await fetch(cacheBustUrl);
            if (r.ok) return await r.json();
        } catch (e) {
            console.log(`[i18n] Try next path: ${path}`);
        }
    }
    console.error(`[i18n] Failed to load locale: ${lang}`);
    return {};
}

function detectLang() {
    // Check localStorage first
    const saved = localStorage.getItem('app_language');
    if (SUPPORTED.includes(saved)) return saved;
    
    // Fall back to browser language
    const browser = (navigator.language || 'en').split('-')[0];
    return SUPPORTED.includes(browser) ? browser : 'en';
}

/**
 * Sync all language selector elements to the current language.
 */
function syncSelectors(lang) {
    document.querySelectorAll('.lang-selector').forEach(sel => {
        sel.value = lang;
    });
}

/**
 * Get current language
 */
export function getCurrentLang() {
    return i18next?.language || detectLang();
}