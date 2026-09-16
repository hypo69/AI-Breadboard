<?php
declare(strict_types=1);

/**
 * Скрипт автоматического применения SQL-схемы (миграций) к удаленной базе данных Helpdesk
 */

require_once __DIR__ . '/Database.php';

echo "=== Helpdesk Database Migration Runner (PHP 8) ===\n";

try {
     = \Helpdesk\Database::getConnection();
    echo "[+] Успешное подключение к базе данных MySQL.\n";

     = __DIR__ . '/schema.sql';
    if (!file_exists()) {
        throw new RuntimeException("Файл схемы schema.sql не найден по пути: ");
    }

     = file_get_contents();
    if (!) {
        throw new RuntimeException("Файл схемы schema.sql пуст.");
    }

    echo "[*] Применение схемы таблиц...\n";
    ->exec();
    echo "[✓] Структура базы данных Helpdesk успешно создана и инициализирована!\n";

} catch (\Throwable ) {
    echo "[X] Ошибка при миграции базы данных: " . ->getMessage() . "\n";
    exit(1);
}
