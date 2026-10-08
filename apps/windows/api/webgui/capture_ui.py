
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Автоматический обход веб-интерфейса и сохранение PNG.

Скрипт открывает веб-интерфейс, обнаруживает элементы навигации,
последовательно переходит по ним и сохраняет визуальное состояние
каждого таба в PNG.

Если навигация изменяет URL hash, hash используется как имя файла.

Например::

    http://127.0.0.1:8001/tc#tab-processes-load-inspector

сохраняется как::

    assets/webgui/tab-processes-load-inspector.png

Примеры запуска::

    python capture_ui.py http://127.0.0.1:8001/tc

    python capture_ui.py http://127.0.0.1:8001/tc --debug

    python capture_ui.py http://127.0.0.1:8001/tc --debug --full-page
"""

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
    """Создается парсер аргументов командной строки.

    :returns: Настроенный парсер аргументов.
    """

    parser = argparse.ArgumentParser(
        description='Сохраняется визуальное состояние веб-интерфейса в PNG.'
    )

    parser.add_argument(
        'url',
        help='URL веб-интерфейса.',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help='Каталог для сохранения результатов.',
    )

    parser.add_argument(
        '--wait',
        type=int,
        default=DEFAULT_WAIT_MS,
        help='Ожидание после навигации в миллисекундах.',
    )

    parser.add_argument(
        '--full-page',
        action='store_true',
        help='Сохраняется вся страница, а не только viewport.',
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включается видимый Chromium и подробный режим отладки.',
    )

    return parser


def debug(
    message: str,
    enabled: bool,
) -> None:
    """Выводится диагностическое сообщение.

    :param message: Текст диагностического сообщения.
    :param enabled: Признак активного DEBUG-режима.
    """

    if enabled:
        print(f'[DEBUG] {message}')


def sanitize_filename(
    value: str,
    fallback: str,
) -> str:
    """Создается безопасное имя файла.

    :param value: Исходное имя.
    :param fallback: Резервное имя.
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
    """Извлекается hash из URL.

    :param url: Полный URL.
    :returns: Значение hash без символа ``#``.
    """

    return urlparse(url).fragment.strip()


def get_screenshot_name(
    page: Page,
    fallback: str,
) -> str:
    """Определяется имя PNG по текущему URL.

    При наличии hash он используется как идентификатор состояния.

    Например::

        http://127.0.0.1:8001/tc#tab-processes-load-inspector

    преобразуется в::

        tab-processes-load-inspector.png

    :param page: Объект страницы Playwright.
    :param fallback: Имя при отсутствии hash.
    :returns: Имя PNG без расширения.
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
    """Ожидается стабилизация страницы.

    :param page: Объект страницы Playwright.
    :param wait_ms: Дополнительное ожидание.
    :param debug_enabled: Включается диагностический вывод.
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
        f'Ожидание {wait_ms} мс...',
        debug_enabled,
    )

    await page.wait_for_timeout(wait_ms)


async def collect_navigation(
    page: Page,
    debug_enabled: bool,
) -> list[dict[str, str]]:
    """Собираются элементы навигации.

    :param page: Объект страницы Playwright.
    :param debug_enabled: Включается диагностический вывод.
    :returns: Список навигационных элементов.
    """

    selector = (
        'nav a, nav button, '
        '[role="navigation"] a, '
        '[role="navigation"] button, '
        'aside a, aside button, '
        '[role="menu"] a, '
        '[role="menu"] button'
    )

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
        href = str(item.get('href', '')).strip()
        element_id = str(item.get('id', '')).strip()

        key = f'{text}|{href}|{element_id}'

        if key in seen:
            continue

        seen.add(key)

        result.append(
            {
                'index': str(item.get('index', '')),
                'tag': str(item.get('tag', '')),
                'text': text,
                'href': href,
                'id': element_id,
                'className': str(item.get('className', '')),
            }
        )

    debug(
        f'Обнаружено навигационных элементов: {len(result)}',
        debug_enabled,
    )

    return result


async def save_screenshot(
    page: Page,
    output_path: Path,
    full_page: bool,
    debug_enabled: bool,
) -> None:
    """Сохраняется PNG текущего состояния страницы.

    :param page: Объект страницы.
    :param output_path: Путь к PNG.
    :param full_page: Сохраняется ли вся страница.
    :param debug_enabled: Включается диагностический вывод.
    """

    debug(
        f'Создается screenshot: {output_path}',
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
    """Выполняется переход по навигационному элементу.

    :param page: Объект страницы.
    :param item: Описание элемента.
    :param wait_ms: Ожидание после перехода.
    :param debug_enabled: Включается диагностический вывод.
    :returns: ``True`` при успешном переходе.
    """

    href = item.get('href', '').strip()

    if href and href.startswith(
        ('http://', 'https://')
    ):
        debug(
            f'Переход по URL: {href}',
            debug_enabled,
        )

        try:
            await page.goto(
                href,
                wait_until='domcontentloaded',
                timeout=15000,
            )

            await wait_for_page(
                page,
                wait_ms,
                debug_enabled,
            )

            return True

        except Exception as exc:
            debug(
                f'Ошибка перехода по URL: {exc}',
                debug_enabled,
            )

            return False

    index = int(
        item.get('index', '0')
    )

    selector = (
        'nav a, nav button, '
        '[role="navigation"] a, '
        '[role="navigation"] button, '
        'aside a, aside button, '
        '[role="menu"] a, '
        '[role="menu"] button'
    )

    locator = page.locator(
        selector
    ).nth(index)

    try:
        debug(
            f'Click: index={index}, '
            f'text={item.get("text", "")!r}',
            debug_enabled,
        )

        await locator.scroll_into_view_if_needed()

        await locator.click(
            timeout=5000,
        )

        await wait_for_page(
            page,
            wait_ms,
            debug_enabled,
        )

        return True

    except Exception as exc:
        debug(
            f'Ошибка click: {exc}',
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
    """Выполняется полный обход навигации.

    :param url: Начальный URL.
    :param output_dir: Каталог результатов.
    :param wait_ms: Ожидание после переходов.
    :param full_page: Сохраняется ли вся страница.
    :param debug_enabled: Включается DEBUG-режим.
    :returns: Код завершения процесса.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest: dict[str, Any] = {
        'url': url,
        'created_at': datetime.now().astimezone().isoformat(),
        'debug': debug_enabled,
        'full_page': full_page,
        'screenshots': [],
    }

    async with async_playwright() as playwright:
        debug(
            'Запуск Chromium: '
            f'{"headed" if debug_enabled else "headless"}',
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
            f'Открывается URL: {url}',
            debug_enabled,
        )

        try:
            await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=15000,
            )

        except Exception as exc:
            print(
                f'Ошибка открытия страницы: {exc}'
            )

            await browser.close()

            return 1

        await wait_for_page(
            page,
            wait_ms,
            debug_enabled,
        )

        initial_name = get_screenshot_name(
            page,
            'initial',
        )

        initial_path = (
            output_dir /
            f'{initial_name}.png'
        )

        await save_screenshot(
            page,
            initial_path,
            full_page,
            debug_enabled,
        )

        print(
            f'[000] {initial_path}'
        )

        navigation = await collect_navigation(
            page,
            debug_enabled,
        )

        print(
            'Найдено элементов навигации: '
            f'{len(navigation)}'
        )

        for number, item in enumerate(
            navigation,
            start=1,
        ):
            label = (
                item.get('text')
                or item.get('id')
                or f'item_{number}'
            )

            print(
                f'[{number:03d}] {label}'
            )

            try:
                debug(
                    f'Возврат к начальному URL: {url}',
                    debug_enabled,
                )

                await page.goto(
                    url,
                    wait_until='domcontentloaded',
                    timeout=15000,
                )

                await wait_for_page(
                    page,
                    wait_ms,
                    debug_enabled,
                )

                success = await navigate_to_item(
                    page,
                    item,
                    wait_ms,
                    debug_enabled,
                )

                if not success:
                    print(
                        '      -> ОШИБКА перехода'
                    )

                    manifest['screenshots'].append(
                        {
                            'number': number,
                            'label': label,
                            'href': item.get(
                                'href',
                                '',
                            ),
                            'status': (
                                'navigation_error'
                            ),
                        }
                    )

                    continue

                screenshot_name = get_screenshot_name(
                    page,
                    sanitize_filename(
                        label,
                        f'item_{number}',
                    ),
                )

                output_path = (
                    output_dir /
                    f'{screenshot_name}.png'
                )

                await save_screenshot(
                    page,
                    output_path,
                    full_page,
                    debug_enabled,
                )

                print(
                    f'      -> {output_path}'
                )

                manifest['screenshots'].append(
                    {
                        'number': number,
                        'label': label,
                        'tag': item.get(
                            'tag',
                            '',
                        ),
                        'id': item.get(
                            'id',
                            '',
                        ),
                        'href': item.get(
                            'href',
                            '',
                        ),
                        'url_after_navigation': (
                            page.url
                        ),
                        'hash': get_url_hash(
                            page.url
                        ),
                        'file': output_path.name,
                        'status': 'ok',
                    }
                )

            except Exception as exc:
                print(
                    f'      -> ОШИБКА: {exc}'
                )

                manifest['screenshots'].append(
                    {
                        'number': number,
                        'label': label,
                        'tag': item.get(
                            'tag',
                            '',
                        ),
                        'id': item.get(
                            'id',
                            '',
                        ),
                        'href': item.get(
                            'href',
                            '',
                        ),
                        'status': 'error',
                        'error': str(exc),
                    }
                )

        manifest_path = (
            output_dir /
            'manifest.json'
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding='utf-8',
        )

        await browser.close()

    print()
    print('Готово.')
    print(
        f'Скриншоты: {output_dir.resolve()}'
    )
    print(
        f'Manifest:  {manifest_path.resolve()}'
    )

    return 0


async def main() -> int:
    """Запускается приложение.

    :returns: Код завершения процесса.
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
    sys.exit(
        asyncio.run(main())
    )
