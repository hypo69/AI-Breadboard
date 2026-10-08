# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: AI-Breadboard - UI Capture Tool
# =============================================================================
# Description:
#   Автоматический обход веб-интерфейса и сохранение скриншотов в PNG.
#   Позволяет агентам и разработчикам автоматически исследовать веб-приложения,
#   обнаруживать элементы навигации, переходить по ним и сохранять визуальное состояние
#   каждого таба/страницы в PNG с формированием manifest.json.
#
# Usage Examples:
#   py tools/capture_ui.py http://127.0.0.1:8001/tc --wait 10000
#   py manage_tools.py ui capture http://127.0.0.1:8001/tc --wait 10000 --debug
#
# File: tools/capture_ui.py
# Project: ai-breadboard
# Package: tools
# Author: hypo69
# Copyright: © 2026 hypo69
# Updated: 2026-10-08 13:00:00
# =============================================================================

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)


DEFAULT_OUTPUT_DIR = Path('assets/webgui')
DEFAULT_WAIT_MS = 800


def build_parser() -> argparse.ArgumentParser:
    """Создается парсер аргументов командной строки для UI Capture Tool.

    :returns: Настроенный парсер аргументов.
    """
    parser = argparse.ArgumentParser(
        description='Автоматический обход веб-интерфейса AI Breadboard и сохранение состояний в PNG.'
    )

    parser.add_argument(
        'url',
        help='URL веб-интерфейса для захвата.',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help='Каталог для сохранения результатов и скриншотов.',
    )

    parser.add_argument(
        '--wait',
        type=int,
        default=DEFAULT_WAIT_MS,
        help='Время ожидания стабилизации страницы после навигации в миллисекундах.',
    )

    parser.add_argument(
        '--full-page',
        action='store_true',
        help='Сохраняется вся страница целиком, а не только текущий viewport.',
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включается видимый режим браузера Chromium и подробный отладочный вывод.',
    )

    return parser


def debug(
    message: str,
    enabled: bool,
) -> None:
    """Выводится диагностическое отладочное сообщение.

    :param message: Текст диагностического сообщения.
    :param enabled: Признак активного DEBUG-режима.
    """
    if enabled:
        print(f'[DEBUG] {message}')


def sanitize_filename(
    value: str,
    fallback: str,
) -> str:
    """Создается безопасное имя файла из произвольной строки.

    :param value: Исходное имя или заголовок.
    :param fallback: Резервное имя при пустом значении.
    :returns: Безопасное имя файла без расширения.
    """
    value = value.strip() or fallback

    value = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        '_',
        value,
    )

    value = re.sub(
        r'\s+',
        '_',
        value,
    )

    value = re.sub(
        r'_+',
        '_',
        value,
    )

    value = value.strip('._ ')

    return value[:150] or fallback


def get_url_hash(
    url: str,
) -> str:
    """Извлекается hash-фрагмент из URL.

    :param url: Полный URL адрес.
    :returns: Значение hash без символа ``#``.
    """
    return urlparse(url).fragment.strip()


def get_screenshot_name(
    page: Page,
    fallback: str,
) -> str:
    """Определяется имя файла скриншота по текущему URL и hash-состоянию.

    :param page: Объект страницы Playwright.
    :param fallback: Имя при отсутствии hash.
    :returns: Имя PNG файла без расширения.
    """
    fragment = get_url_hash(page.url)

    if fragment:
        return sanitize_filename(
            fragment,
            fallback,
        )

    return sanitize_filename(
        fallback,
        'page',
    )


async def wait_for_page(
    page: Page,
    wait_ms: int,
    debug_enabled: bool,
) -> None:
    """Ожидается стабилизация и загрузка DOM страницы.

    :param page: Объект страницы Playwright.
    :param wait_ms: Дополнительная пауза в миллисекундах.
    :param debug_enabled: Включен ли отладочный режим.
    """
    debug(
        'Ожидание загрузки DOM...',
        debug_enabled,
    )

    try:
        await page.wait_for_load_state(
            'domcontentloaded',
            timeout=10000,
        )
    except Exception:
        debug(
            'domcontentloaded не получен в установленный timeout.',
            debug_enabled,
        )

    debug(
        f'Ожидание дополнительных {wait_ms} мс...',
        debug_enabled,
    )

    await page.wait_for_timeout(wait_ms)


async def collect_navigation(
    page: Page,
    debug_enabled: bool,
) -> list[dict[str, str]]:
    """Собираются интерактивные элементы навигации со страницы (вкладки Test Computer /tc).

    :param page: Объект страницы Playwright.
    :param debug_enabled: Включен ли отладочный режим.
    :returns: Список словарей с описанием навигационных элементов.
    """
    # Открытие бокового меню offcanvas для доступа к вкладкам /tc
    try:
        drawer_btn = page.locator('#apps-drawer-toggle-btn, .left-drawer-tab-trigger').first
        if await drawer_btn.count() > 0:
            debug('Открытие боковой панели навигации AI Breadboard...', debug_enabled)
            await drawer_btn.click(timeout=2000)
            await page.wait_for_timeout(800)
    except Exception as exc:
        debug(f'Не удалось автоматически открыть боковое меню: {exc}', debug_enabled)

    # Ожидание рендеринга элементов вкладок
    try:
        await page.wait_for_selector('#appsNavTabs button, .list-group-item, [data-tab]', timeout=5000)
    except Exception:
        pass

    selector = '#appsNavTabs button, .list-group-item, [data-tab]'

    items = await page.locator(selector).evaluate_all(
        """
        elements => elements.map((element, index) => ({
            index: String(index),
            tag: element.tagName.toLowerCase(),
            text: (
                element.innerText ||
                element.textContent ||
                element.getAttribute('aria-label') ||
                ''
            ).trim(),
            href: element.href || '',
            id: element.id || '',
            tab: element.getAttribute('data-tab') || '',
            className: typeof element.className === 'string'
                ? element.className
                : ''
        }))
        """
    )

    result: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in items:
        text = str(item.get('text', '')).strip()
        tab_attr = str(item.get('tab', '')).strip()
        element_id = str(item.get('id', '')).strip()

        if not text and not tab_attr and not element_id:
            continue

        key = f'{text}|{tab_attr}|{element_id}'
        if key in seen:
            continue
        seen.add(key)

        result.append(
            {
                'index': str(item.get('index', '')),
                'tag': str(item.get('tag', '')),
                'text': text,
                'tab': tab_attr,
                'id': element_id,
                'className': str(item.get('className', '')),
            }
        )

    debug(
        f'Обнаружено уникальных вкладок навигации: {len(result)}',
        debug_enabled,
    )

    return result


async def save_screenshot(
    page: Page,
    output_path: Path,
    full_page: bool,
    debug_enabled: bool,
) -> None:
    """Сохраняется скриншот текущего состояния страницы в PNG.

    :param page: Объект страницы Playwright.
    :param output_path: Путь к сохраняемому файлу.
    :param full_page: Сохранять ли всю страницу целиком.
    :param debug_enabled: Включен ли отладочный режим.
    """
    debug(
        f'Создается скриншот: {output_path}',
        debug_enabled,
    )

    await page.screenshot(
        path=str(output_path),
        full_page=full_page,
        animations='disabled',
    )


async def navigate_to_item(
    page: Page,
    item: dict[str, str],
    wait_ms: int,
    debug_enabled: bool,
) -> bool:
    """Выполняется переход по указанному навигационному элементу (вкладке).

    :param page: Объект страницы Playwright.
    :param item: Словарь с описанием элемента.
    :param wait_ms: Время ожидания после клика.
    :param debug_enabled: Включен ли отладочный режим.
    :returns: True при успешном переходе.
    """
    # Открываем боковое меню offcanvas, если оно закрыто
    try:
        drawer_btn = page.locator('#apps-drawer-toggle-btn, .left-drawer-tab-trigger').first
        if await drawer_btn.count() > 0:
            await drawer_btn.click(timeout=2000)
            await page.wait_for_timeout(600)
    except Exception as exc:
        debug(f'Не удалось открыть боковое меню перед кликом: {exc}', debug_enabled)

    text = item.get('text', '').strip()
    tab_attr = item.get('tab', '').strip()
    element_id = item.get('id', '').strip()

    locator = None
    if tab_attr:
        locator = page.locator(f'[data-tab="{tab_attr}"]')
    elif element_id:
        locator = page.locator(f'#{element_id}')
    elif text:
        locator = page.locator('#appsNavTabs button, .list-group-item').filter(has_text=text).first

    if not locator or await locator.count() == 0:
        index = int(item.get('index', '0'))
        locator = page.locator('#appsNavTabs button, .list-group-item').nth(index)

    try:
        debug(
            f'Клик по вкладке: text={text!r}, tab={tab_attr!r}',
            debug_enabled,
        )

        await locator.scroll_into_view_if_needed()
        await locator.click(timeout=5000)

        await wait_for_page(
            page,
            wait_ms,
            debug_enabled,
        )

        return True

    except Exception as exc:
        debug(
            f'Ошибка клика по вкладке: {exc}',
            debug_enabled,
        )

        return False


async def capture_interface(
    url: str,
    output_dir: Path,
    wait_ms: int,
    full_page: bool,
    debug_enabled: bool,
) -> int:
    """Выполняется полный обход интерфейса и сохранение скриншотов.

    :param url: Начальный URL веб-интерфейса.
    :param output_dir: Целевой каталог для результатов.
    :param wait_ms: Пауза после каждого действия.
    :param full_page: Флаг сохранения полной страницы.
    :param debug_enabled: Включен ли отладочный режим.
    :returns: Код возврата (0 - успех, 1 - ошибка).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        'url': url,
        'created_at': datetime.now().astimezone().isoformat(),
        'debug': debug_enabled,
        'full_page': full_page,
        'screenshots': [],
    }

    async with async_playwright() as playwright:
        debug(
            f'Запуск браузера Chromium: {"headed" if debug_enabled else "headless"}',
            debug_enabled,
        )

        browser: Browser = await playwright.chromium.launch(
            headless=not debug_enabled,
            slow_mo=100 if debug_enabled else 0,
        )

        context: BrowserContext = await browser.new_context(
            viewport={
                'width': 1920,
                'height': 1080,
            },
            device_scale_factor=1,
        )

        page = await context.new_page()

        debug(
            f'Открытие начального URL: {url}',
            debug_enabled,
        )

        try:
            await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=15000,
            )
        except Exception as exc:
            print(f'Ошибка открытия страницы {url}: {exc}')
            await browser.close()
            return 1

        await wait_for_page(page, wait_ms, debug_enabled)

        initial_name = get_screenshot_name(page, 'initial')
        initial_path = output_dir / f'{initial_name}.png'

        await save_screenshot(page, initial_path, full_page, debug_enabled)
        print(f'[000] Сохранен начальный скриншот: {initial_path}')

        navigation = await collect_navigation(page, debug_enabled)
        print(f'Обнаружено вкладок для обхода: {len(navigation)}')

        for number, item in enumerate(navigation, start=1):
            label = item.get('text') or item.get('tab') or f'item_{number}'
            print(f'[{number:03d}] Обработка вкладки: {label}')

            try:
                debug(f'Возврат к исходному URL: {url}', debug_enabled)
                await page.goto(
                    url,
                    wait_until='domcontentloaded',
                    timeout=15000,
                )
                await wait_for_page(page, wait_ms, debug_enabled)

                success = await navigate_to_item(page, item, wait_ms, debug_enabled)

                if not success:
                    print('      -> ОШИБКА перехода на вкладку')
                    manifest['screenshots'].append({
                        'number': number,
                        'label': label,
                        'tab': item.get('tab', ''),
                        'status': 'navigation_error',
                    })
                    continue

                screenshot_name = get_screenshot_name(
                    page,
                    sanitize_filename(label, f'item_{number}'),
                )
                output_path = output_dir / f'{screenshot_name}.png'

                await save_screenshot(page, output_path, full_page, debug_enabled)
                print(f'      -> Успешно сохранено: {output_path}')

                manifest['screenshots'].append({
                    'number': number,
                    'label': label,
                    'tag': item.get('tag', ''),
                    'tab': item.get('tab', ''),
                    'id': item.get('id', ''),
                    'url_after_navigation': page.url,
                    'hash': get_url_hash(page.url),
                    'file': output_path.name,
                    'status': 'ok',
                })

            except Exception as exc:
                print(f'      -> ОШИБКА выполнения: {exc}')
                manifest['screenshots'].append({
                    'number': number,
                    'label': label,
                    'tag': item.get('tag', ''),
                    'tab': item.get('tab', ''),
                    'id': item.get('id', ''),
                    'status': 'error',
                    'error': str(exc),
                })

        manifest_path = output_dir / 'manifest.json'
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

        await browser.close()

    print()
    print('Захват интерфейса завершен.')
    print(f'Скриншоты: {output_dir.resolve()}')
    print(f'Манифест:  {manifest_path.resolve()}')

    return 0


async def main() -> int:
    """Точка входа CLI утилиты UI Capture Tool.

    :returns: Код возврата процесса.
    """
    parser = build_parser()
    args = parser.parse_args()

    return await capture_interface(
        url=args.url,
        output_dir=args.output,
        wait_ms=args.wait,
        full_page=args.full_page,
        debug_enabled=args.debug,
    )


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
