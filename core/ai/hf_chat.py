# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Получение директории кэша моделей HuggingFace.
# =============================================================================
# Description:
#   Клиент для локальных моделей HuggingFace.
#
# File: hf_chat.py
# Project: ai-breadboard
# Package: core.ai
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List

from core.logger.logger import logger

def _get_models_dir() -> Path:
    """Получение директории кэша моделей HuggingFace."""
    raw = os.environ.get("HF_MODELS_DIR", "")
    if raw and not raw.startswith("${"):
        return Path(raw).expanduser()
    return Path.home() / ".cache" / "huggingface" / "hub"

HF_MODELS_DIR = _get_models_dir()
HF_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"

# Локальный кэш загруженных в память моделей: {model_id: {"pipeline": pipe, "tokenizer": tokenizer}}
_loaded_models: Dict[str, Dict[str, Any]] = {}

def _check_transformers() -> bool:
    """Check наличия библиотеки transformers."""
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False

def _check_huggingface_hub() -> bool:
    """Check наличия библиотеки huggingface_hub."""
    try:
        import huggingface_hub  # noqa: F401
        return True
    except ImportError:
        return False

class HFClient:
    """Клиент управления локальными моделями HuggingFace."""

    def download_model(
        self,
        model_id: str,
        token: str = "",
        progress_callback: Callable[[Dict[str, Any]], None] = lambda _: 0,
    ) -> Dict[str, Any]:
        """Скачивание модели через snapshot_download."""
        if not _check_huggingface_hub():
            return {"success": False, "error": "huggingface_hub не установлен"}

        from huggingface_hub import snapshot_download

        hf_token: str = token or os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACE_TOKEN", "")
        save_dir: Path = HF_MODELS_DIR / model_id.replace("/", "--")
        save_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[HFClient] Скачивание модели {model_id} -> {save_dir}")

        try:
            path = snapshot_download(
                repo_id=model_id,
                local_dir=str(save_dir),
                token=hf_token or "",
                ignore_patterns=["*.msgpack", "*.h5", "flax_model*", "tf_model*"],
            )
            logger.info(f"[HFClient] Модель {model_id} successfully скачана: {path}")
            return {"success": True, "model_id": model_id, "path": path}
        except Exception as e:
            err = str(e)
            logger.error(f"[HFClient] Error скачивания {model_id}: {err}")
            return {"success": False, "error": err}

    def load_model(self, model_id: str, device: str = "auto") -> Dict[str, Any]:
        """Loading модели в память (RAM / VRAM) для инференса."""
        if not _check_transformers():
            return {"success": False, "error": "transformers не установлен"}

        if model_id in _loaded_models:
            return {"success": True, "model_id": model_id, "status": "already_loaded"}

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            local_path: str = ""
            local_files_only: bool = False

            try:
                from huggingface_hub import snapshot_download as _sd
                local_path = _sd(
                    repo_id=model_id,
                    local_files_only=True,
                    cache_dir=str(HF_CACHE_DIR),
                )
                local_files_only = True
            except Exception:
                pass

            if not local_path:
                dir_name = f"models--{model_id.replace('/', '--')}"
                for base in (HF_MODELS_DIR, HF_CACHE_DIR):
                    candidate = base / dir_name / "snapshots"
                    if candidate.exists():
                        dirs = [s for s in candidate.iterdir() if s.is_dir()]
                        if dirs:
                            local_path = str(sorted(dirs)[-1])
                            local_files_only = True
                            break

            model_path = local_path or model_id
            hf_token: str = "" if local_files_only else (os.getenv("HF_TOKEN", "") or os.getenv("HUGGINGFACE_TOKEN", ""))

            logger.info(f"[HFClient] Loading весов {model_id} из {model_path}")

            torch_dtype: torch.dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                token=hf_token or "",
                local_files_only=local_files_only,
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                device_map=device,
                token=hf_token or "",
                local_files_only=local_files_only,
            )

            pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
            _loaded_models[model_id] = {"pipeline": pipe, "tokenizer": tokenizer}

            actual_device = str(next(model.parameters()).device)
            logger.info(f"[HFClient] Модель {model_id} загружена на устройство: {actual_device}")
            return {"success": True, "model_id": model_id, "device": actual_device}

        except Exception as e:
            logger.error(f"[HFClient] Error при загрузке модели {model_id}: {e}")
            return {"success": False, "error": str(e)}

    def unload_model(self, model_id: str) -> Dict[str, Any]:
        """Выгрузка модели из памяти и освобождение RAM/VRAM."""
        if model_id not in _loaded_models:
            return {"success": False, "error": f"Модель {model_id} не загружена"}
        try:
            import gc
            import torch
            del _loaded_models[model_id]
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info(f"[HFClient] Модель {model_id} выгружена из памяти")
            return {"success": True, "model_id": model_id}
        except Exception as e:
            logger.error(f"[HFClient] Error при выгрузке модели {model_id}: {e}")
            return {"success": False, "error": str(e)}

    async def generate(
        self,
        prompt: str,
        model_id: str,
        system_prompt: str = "",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Неблокирующая генерация ответа через загруженную модель."""
        if model_id not in _loaded_models:
            loop = asyncio.get_running_loop()
            load_res = await loop.run_in_executor(None, self.load_model, model_id)
            if not load_res.get("success"):
                return {"success": False, "error": f"Не удалось загрузить модель: {load_res.get('error', '')}"}

        try:
            pipe = _loaded_models[model_id]["pipeline"]
            tokenizer = _loaded_models[model_id]["tokenizer"]

            if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
                messages: List[Dict[str, str]] = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                formatted_prompt = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            else:
                formatted_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

            def _inference() -> str:
                outputs = pipe(
                    formatted_prompt,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=pipe.tokenizer.eos_token_id,
                    return_full_text=False,
                )
                return outputs[0]["generated_text"]

            loop = asyncio.get_running_loop()
            content = await loop.run_in_executor(None, _inference)
            return {"success": True, "content": content, "model": model_id}

        except Exception as e:
            logger.error(f"[HFClient] Error инференса модели {model_id}: {e}")
            return {"success": False, "error": str(e)}

    def list_downloaded(self) -> List[Dict[str, Any]]:
        """Получение списка моделей в локальном кэше HuggingFace."""
        try:
            from huggingface_hub import scan_cache_dir
            results: List[Dict[str, Any]] = []
            seen: set[str] = set()

            for cache_dir in {HF_MODELS_DIR, HF_CACHE_DIR}:
                if not cache_dir.exists():
                    continue
                try:
                    cache_info = scan_cache_dir(cache_dir=str(cache_dir))
                except Exception:
                    continue

                for repo in cache_info.repos:
                    if repo.repo_id in seen:
                        continue
                    seen.add(repo.repo_id)

                    path: str = str(cache_dir)
                    try:
                        revisions = sorted(repo.revisions, key=lambda r: r.last_modified, reverse=True)
                        if revisions and revisions[0].snapshot_path:
                            path = str(revisions[0].snapshot_path)
                    except Exception:
                        pass

                    results.append({
                        "id": repo.repo_id,
                        "path": path,
                        "loaded": repo.repo_id in _loaded_models,
                        "size_mb": round(repo.size_on_disk / 1024 / 1024, 1),
                        "source": str(cache_dir),
                    })

            if results:
                return sorted(results, key=lambda x: x["id"])
        except Exception:
            pass

        # Фолбек на файловый поиск
        items: List[Dict[str, Any]] = []
        for base in (HF_MODELS_DIR, HF_CACHE_DIR):
            if not base.exists():
                continue
            for d in base.iterdir():
                if not d.is_dir() or not d.name.startswith("models--"):
                    continue
                model_id: str = d.name[len("models--"):].replace("--", "/", 1)
                items.append({
                    "id": model_id,
                    "path": str(d),
                    "loaded": model_id in _loaded_models,
                    "size_mb": 0.0,
                    "source": str(base),
                })
        return items

    def list_loaded(self) -> List[Dict[str, Any]]:
        """List моделей, удерживаемых в оперативной памяти."""
        return [{"id": k, "status": "loaded"} for k in _loaded_models]

hf_client = HFClient()

class HFChatBase:
    """Обертка чата для локальных моделей HuggingFace."""

    def __init__(self, model_id: str, system_prompt: str = "") -> None:
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.client = hf_client

    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Синхронно-асинхронная генерация единого текстового ответа."""
        res = await self.client.generate(
            prompt=prompt,
            model_id=self.model_id,
            system_prompt=self.system_prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
        )
        if res.get("success"):
            return res.get("content", "")
        raise RuntimeError(f"HuggingFace error: {res.get('error', 'Unknown generation error')}")

    async def generate_content_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Стриминговая генерация (эмуляция генерацией порции контента)."""
        content = await self.generate_content(prompt, temperature=temperature, max_tokens=max_tokens)
        if content:
            yield content
