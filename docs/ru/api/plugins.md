# Плагины

## BasePlugin

Базовый класс для всех плагинов. Определяет жизненный цикл, конфигурацию, действия и инструменты для LLM.

::: plugins.base.BasePlugin
    options:
      members:
        - __init__
        - start
        - stop
        - health_check
        - get_config_fields
        - update_config
        - get_actions
        - execute_action
        - get_tools
        - handle
        - get_title
        - get_description
        - get_manifest

---

## TelegramBotPlugin

::: plugins.telegram_bot.plugin.TelegramBotPlugin

---

## GoogleWorkspacePlugin

::: plugins.google_workspace.plugin.GoogleWorkspacePlugin

---

## UserStoragePlugin

::: plugins.user_storage.plugin.UserStoragePlugin

---

## TelegramChannelRAGPlugin

::: plugins.telegram_channel_rag.plugin.TelegramChannelRAGPlugin

---

## NewsfeedPlugin

::: plugins.news_feed.plugin.NewsFeedPlugin

---

## LogAnalyzerPlugin

::: plugins.log_analyzer.plugin.LogAnalyzerPlugin

---

## InvoiceProcessorPlugin

::: plugins.invoice_processor.plugin.InvoiceProcessorPlugin

---

## IFTTTPlugin

::: plugins.ifttt.plugin.IFTTTPlugin

---

## WhatsAppPlugin

::: plugins.whatsapp.plugin.WhatsAppPlugin

