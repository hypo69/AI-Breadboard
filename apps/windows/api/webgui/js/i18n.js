/**
 * =============================================================================
 * Process Name: Windows Js - I18N Script
 * =============================================================================
 * Description:
 *   Клиентский модуль интернационализации (i18n) и региональных настроек (BCP 47).
 *   Поддерживает нормализацию тегов language-REGION (например ru-RU, he-IL, uk-UA, en-US),
 *   автоматическое определение из URL query параметров (?region=ru-ru, ?locale=ru-RU,
 *   ?language-region=ru-RU, ?lang=ru), переключение языков и синхронизацию DOM.
 *
 * Usage Examples:
 *   HTML Integration:
 *     <script src="/windows/api/webgui/js/i18n.js?v=20261006_v10" type="module"></script>
 *
 *   JavaScript Import:
 *     import { initI18n, switchLocale, switchLang, normalizeLocaleTag, getCurrentLocale } from '/windows/api/webgui/js/i18n.js';
 *
 * File: i18n.js
 * Project: ai-breadboard
 * Package: windows/api/webgui/js
 * Author: hypo69
 * Copyright: © 2026 hypo69
 * Updated: 2026-10-06 22:15:00
 * =============================================================================
 */

/**
 * i18n.js — Модуль интернационализации и локалей BCP 47
 * 
 * Конвенции разметки HTML:
 *   data-i18n="key"             — устанавливает innerHTML элемента
 *   data-i18n-placeholder="key" — устанавливает placeholder для input/textarea
 *   data-i18n-title="key"       — устанавливает атрибут title
 * 
 * Приоритет выбора языка/локали:
 *   1. Параметры URL query: ?region=ru-ru | ?locale=ru-RU | ?language-region=ru-RU | ?lang=ru
 *   2. Сохранённое значение в localStorage ('app_locale' / 'app_language')
 *   3. Язык браузера (navigator.language)
 *   4. Дефолтная локаль ('en-US')
 */

export const DEFAULT_LOCALE = 'en-US';
export const SUPPORTED_LOCALES = ['en-US', 'ru-RU', 'he-IL', 'uk-UA'];
export const SUPPORTED_LANGS = ['en', 'ru', 'he', 'uk'];
export const SUPPORTED = SUPPORTED_LANGS; // Обратная совместимость

export const DEFAULT_REGIONS = {
    en: 'US',
    ru: 'RU',
    he: 'IL',
    uk: 'UA',
    de: 'DE',
    fr: 'FR',
    es: 'ES',
    pt: 'BR',
    zh: 'CN',
    ja: 'JP',
    ko: 'KR',
    ar: 'SA'
};

let i18nInitialized = false;
let eventsBound = false;
let currentActiveLocale = DEFAULT_LOCALE;

/**
 * Нормализует языковой/региональный тег в стандарт BCP 47 (language-REGION)
 * и извлекает базовый язык и регион.
 * 
 * Формат:
 *   language-REGION
 *   language — ISO 639-1 (2 строчные буквы: ru, he, uk, en...)
 *   REGION   — ISO 3166-1 alpha-2 (2 заглавные буквы: RU, IL, UA, US...)
 * 
 * Примеры:
 *   "ru-ru"    -> { locale: "ru-RU", lang: "ru", region: "RU" }
 *   "ru_ru"    -> { locale: "ru-RU", lang: "ru", region: "RU" }
 *   "he-il"    -> { locale: "he-IL", lang: "he", region: "IL" }
 *   "uk-ua"    -> { locale: "uk-UA", lang: "uk", region: "UA" }
 *   "en-us"    -> { locale: "en-US", lang: "en", region: "US" }
 *   "ru"       -> { locale: "ru-RU", lang: "ru", region: "RU" }
 *   "`ru-ru`"  -> { locale: "ru-RU", lang: "ru", region: "RU" }
 * 
 * @param {string} tag - Исходный тег локали или языка
 * @returns {{ locale: string, lang: string, region: string }}
 */
export function normalizeLocaleTag(tag) {
    if (!tag || typeof tag !== 'string') {
        return { locale: DEFAULT_LOCALE, lang: 'en', region: 'US' };
    }

    // Очистка от кавычек, апострофов, обратных кавычек и пробелов
    let cleaned = tag.trim().replace(/^[`'"]+|[`'"]+$/g, '');

    // Заменяем нижние подчеркивания на дефисы
    cleaned = cleaned.replace(/_/g, '-');

    // Проверяем формат language-REGION (например ru-RU, ru-ru, en-US)
    const match = cleaned.match(/^([a-zA-Z]{2,3})(?:-([a-zA-Z]{2,4}))?$/);
    if (match) {
        const langPart = match[1].toLowerCase();
        let regionPart = match[2] 
            ? match[2].toUpperCase() 
            : (DEFAULT_REGIONS[langPart] || langPart.toUpperCase());
        const locale = `${langPart}-${regionPart}`;
        return { locale, lang: langPart, region: regionPart };
    }

    // Fallback для неизвестных конструкций
    const lower = cleaned.toLowerCase();
    const fallbackLang = SUPPORTED_LANGS.includes(lower) ? lower : 'en';
    const fallbackRegion = DEFAULT_REGIONS[fallbackLang] || 'US';
    return {
        locale: `${fallbackLang}-${fallbackRegion}`,
        lang: fallbackLang,
        region: fallbackRegion
    };
}

/**
 * Извлекает и нормализует локаль/регион из URL query параметров.
 * Поддерживаемые параметры:
 *   - region (например ?region=ru-ru или ?region=ru-RU)
 *   - locale (например ?locale=ru-RU)
 *   - language-region (например ?language-region=ru-RU)
 *   - language_region (например ?language_region=ru_RU)
 *   - lang (например ?lang=ru)
 *   - language (например ?language=ru-RU)
 * 
 * @returns {{ locale: string, lang: string, region: string } | null}
 */
export function getLocaleFromUrl() {
    try {
        if (typeof window === 'undefined' || !window.location || !window.location.search) {
            return null;
        }
        const params = new URLSearchParams(window.location.search);
        const urlParam = params.get('region') || 
                         params.get('locale') || 
                         params.get('language-region') || 
                         params.get('language_region') || 
                         params.get('lang') || 
                         params.get('language');

        if (urlParam) {
            return normalizeLocaleTag(urlParam);
        }
    } catch (e) {
        console.warn('[i18n] Ошибка парсинга параметров URL:', e);
    }
    return null;
}

/**
 * Привязывает обработчик изменений селекторов языка.
 */
function setupLanguageEvents() {
    if (eventsBound) return;
    eventsBound = true;
    document.addEventListener('change', (e) => {
        if (e.target && e.target.classList.contains('lang-selector')) {
            switchLocale(e.target.value);
        }
    });
}

/**
 * Инициализирует i18next и применяет переводы к DOM.
 * @param {string} [langOrLocale] - Язык или локаль (опционально)
 */
export async function initI18n(langOrLocale) {
    let target;
    if (langOrLocale) {
        target = normalizeLocaleTag(langOrLocale);
    } else {
        target = detectLocale();
    }

    const { locale, lang, region } = target;
    currentActiveLocale = locale;

    // Всегда загружаем английский как fallback
    const [mainRes, enRes] = await Promise.all([
        loadLocale(lang),
        lang !== 'en' ? loadLocale('en') : Promise.resolve(null),
    ]);

    if (typeof i18next !== 'undefined') {
        await i18next.init({
            lng: lang,
            fallbackLng: 'en',
            resources: { [lang]: { translation: mainRes } },
            interpolation: { escapeValue: false },
        });

        if (enRes) {
            i18next.addResourceBundle('en', 'translation', enRes, true, true);
        }
    }

    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('data-locale', locale);
    document.documentElement.setAttribute('dir', (lang === 'he' || lang === 'ar') ? 'rtl' : 'ltr');

    applyTranslations();
    syncSelectors(lang, locale);
    setupLanguageEvents();
    i18nInitialized = true;

    // Сохраняем в localStorage
    try {
        localStorage.setItem('app_locale', locale);
        localStorage.setItem('app_language', lang);
    } catch {}

    // Уведомляем систему через события
    window.dispatchEvent(new CustomEvent('localeChanged', { detail: { locale, lang, region } }));
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang, locale, region } }));
}

/**
 * Переключает язык/локаль, перезагружает бандлы при необходимости, сохраняет в localStorage.
 * @param {string} langOrLocale - Код языка или тег BCP 47 (например 'ru', 'ru-RU', 'he-IL')
 */
export async function switchLocale(langOrLocale) {
    const { locale, lang, region } = normalizeLocaleTag(langOrLocale);
    currentActiveLocale = locale;

    if (typeof i18next !== 'undefined') {
        if (!i18next.hasResourceBundle(lang, 'translation')) {
            const res = await loadLocale(lang);
            i18next.addResourceBundle(lang, 'translation', res, true, true);
        }
        await i18next.changeLanguage(lang);
    }

    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('data-locale', locale);
    document.documentElement.setAttribute('dir', (lang === 'he' || lang === 'ar') ? 'rtl' : 'ltr');

    applyTranslations();
    syncSelectors(lang, locale);

    try {
        localStorage.setItem('app_locale', locale);
        localStorage.setItem('app_language', lang);
    } catch {}

    // Глобальные события для компонентов и вкладок
    window.dispatchEvent(new CustomEvent('localeChanged', { detail: { locale, lang, region } }));
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang, locale, region } }));
}

// Алиас для обратной совместимости
export const switchLang = switchLocale;

/**
 * Обновляет все элементы с data-i18n* атрибутами в DOM.
 */
export function applyTranslations() {
    if (typeof i18next === 'undefined') return;

    // Контент текста и HTML
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.innerHTML = val;
    });

    // Плейсхолдеры
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.placeholder = val;
    });

    // Тултипы и атрибут title
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (!key) return;
        const val = i18next.t(key);
        if (val && val !== key) el.title = val;
    });
}

/**
 * Загружает JSON-файл локализации.
 * @param {string} lang - Код языка
 * @returns {Promise<Object>}
 */
async function loadLocale(lang) {
    const pathName = typeof window !== 'undefined' ? window.location.pathname : '';
    let paths = [];
    
    if (pathName.includes('/user_tts')) {
        paths = [
            `/html/locales/${lang}.json`,
            `/html/user_tts/locales/user_${lang}.json`,
            `/html/locales/user_${lang}.json`
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
            console.log(`[i18n] Попытка загрузки альтернативного пути: ${path}`);
        }
    }
    console.warn(`[i18n] Локаль ${lang} не найдена на сервере, используется fallback`);
    return {};
}

/**
 * Определяет текущую локаль по приоритетам (URL -> localStorage -> Браузер -> Дефолт).
 * @returns {{ locale: string, lang: string, region: string }}
 */
export function detectLocale() {
    // 1. Проверяем URL параметр
    const fromUrl = getLocaleFromUrl();
    if (fromUrl) {
        try {
            localStorage.setItem('app_locale', fromUrl.locale);
            localStorage.setItem('app_language', fromUrl.lang);
        } catch {}
        return fromUrl;
    }

    // 2. Проверяем localStorage
    try {
        const savedLocale = localStorage.getItem('app_locale');
        if (savedLocale) return normalizeLocaleTag(savedLocale);

        const savedLang = localStorage.getItem('app_language') || localStorage.getItem('language');
        if (savedLang) return normalizeLocaleTag(savedLang);
    } catch {}

    // 3. Проверяем язык браузера
    if (typeof navigator !== 'undefined') {
        const browser = navigator.language || (navigator.languages && navigator.languages[0]) || '';
        if (browser) return normalizeLocaleTag(browser);
    }

    // 4. Дефолтная локаль
    return normalizeLocaleTag(DEFAULT_LOCALE);
}

/**
 * Определяет текущий базовый язык.
 * @returns {string}
 */
export function detectLang() {
    return detectLocale().lang;
}

/**
 * Синхронизирует значения во всех выпадающих списках выбора языка на странице.
 * @param {string} lang
 * @param {string} locale
 */
function syncSelectors(lang, locale) {
    document.querySelectorAll('.lang-selector').forEach(sel => {
        const optLocale = Array.from(sel.options).find(opt => opt.value.toLowerCase() === (locale || '').toLowerCase());
        const optLang = Array.from(sel.options).find(opt => opt.value.toLowerCase() === (lang || '').toLowerCase());
        if (optLocale) {
            sel.value = optLocale.value;
        } else if (optLang) {
            sel.value = optLang.value;
        }
    });
}

/**
 * Получает текущий активный базовый язык.
 * @returns {string}
 */
export function getCurrentLang() {
    return (typeof i18next !== 'undefined' && i18next.language) || detectLang();
}

/**
 * Получает текущую активную локаль в формате BCP 47.
 * @returns {string}
 */
export function getCurrentLocale() {
    return currentActiveLocale || detectLocale().locale;
}