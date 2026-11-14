"""
LLM dispatch layer
==================
Single entry point for every generator in the pipeline:

    from modules.openai_call import convert_with_llm
    text = convert_with_llm(prompt, model_name="openai")

`model_name` is driven by `llm.default_model` in config.yaml. To switch the
whole pipeline to a different LLM, a user only edits config.yaml — no code
changes are required.

Supported `model_name` values and the config section each one reads:

    openai        -> Azure OpenAI (GPT-4o family)    providers.azure_openai_gpt4o
    gpt-5         -> Azure OpenAI (GPT-5)            providers.azure_openai_gpt5
    gpt-5-chat    -> Azure OpenAI (GPT-5-chat)       providers.azure_openai_gpt5_chat
    claude        -> Claude via Google Vertex AI     providers.vertex_claude
    gemini        -> Google Gemini (Generative AI)   providers.google_gemini
    openai-direct -> OpenAI / OpenAI-compatible API  providers.openai_direct

Design notes
------------
* LAZY INITIALISATION — every provider client is built the first time its
  model is actually selected, then cached. Importing this module therefore
  NEVER touches a provider whose credentials are blank. A deployment that
  fills in only ONE provider's credentials can import and run this module
  without the other providers' SDKs or credentials being installed/present.
* LAZY IMPORTS — provider SDKs are imported inside their own branch, so a
  missing optional SDK (e.g. google-generativeai) never breaks import; it
  only errors if that provider is selected.
* CLEAR ERRORS — if a selected provider is missing required config values,
  a RuntimeError names the exact keys to fill, rather than silently
  returning a bad result.
"""

import json

import config_loader


# ── Lazy client cache ────────────────────────────────────────────────
_CLIENTS: dict = {}


def _cfg(section: str) -> dict:
    """Fetch a providers.* config section as a dict (never None)."""
    return config_loader.get_section(section) or {}


def _require(cfg: dict, keys, provider: str, section: str) -> None:
    """Raise a clear, actionable error if any required config key is blank."""
    missing = [k for k in keys if not str(cfg.get(k) or "").strip()]
    if missing:
        raise RuntimeError(
            f"LLM provider '{provider}' is selected (llm.default_model) but "
            f"config.yaml is missing required value(s): {', '.join(missing)}. "
            f"Fill them under 'providers.{section}' in config.yaml."
        )


# ── Provider client getters (lazy + cached) ──────────────────────────

def _get_azure_openai(section: str, required, provider: str):
    """Build/cache an AzureOpenAI client for the given providers.* section."""
    if section not in _CLIENTS:
        cfg = _cfg(section)
        _require(cfg, required, provider, section)
        from openai import AzureOpenAI  # lazy import (after config check)
        # Accept both `azure_endpoint` and `endpoint`, and both `api_key`
        # and `subscription_key`, so the existing config keys keep working.
        endpoint = cfg.get("azure_endpoint") or cfg.get("endpoint")
        api_key = cfg.get("api_key") or cfg.get("subscription_key")
        client = AzureOpenAI(
            api_key=api_key,
            api_version=cfg.get("api_version"),
            azure_endpoint=endpoint,
        )
        _CLIENTS[section] = (client, cfg)
    return _CLIENTS[section]


def _get_claude():
    """Build/cache the Anthropic Claude (Vertex AI) client."""
    if "vertex_claude" not in _CLIENTS:
        cfg = _cfg("providers.vertex_claude")
        _require(
            cfg,
            ["project_id", "location", "model_id", "client_email", "private_key"],
            "claude",
            "vertex_claude",
        )
        from anthropic import AnthropicVertex  # lazy import (after config check)
        from google.oauth2 import service_account  # lazy import
        private_key = str(cfg.get("private_key", "")).replace("\\n", "\n")
        service_account_info = {
            "type": "service_account",
            "project_id": cfg.get("project_id"),
            "client_email": cfg.get("client_email"),
            "private_key": private_key,
            "token_uri": cfg.get("token_uri"),
        }
        for opt in ("private_key_id", "client_id"):
            if cfg.get(opt):
                service_account_info[opt] = cfg.get(opt)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = AnthropicVertex(
            project_id=cfg.get("project_id"),
            region=cfg.get("location"),
            credentials=credentials,
        )
        _CLIENTS["vertex_claude"] = (client, cfg)
    return _CLIENTS["vertex_claude"]


def _get_gemini():
    """Configure/cache the Google Gemini model."""
    if "google_gemini" not in _CLIENTS:
        cfg = _cfg("providers.google_gemini")
        _require(cfg, ["api_key", "model_id"], "gemini", "google_gemini")
        import google.generativeai as genai  # lazy import (after config check)
        genai.configure(api_key=cfg.get("api_key"))
        model = genai.GenerativeModel(cfg.get("model_id"))
        _CLIENTS["google_gemini"] = (model, cfg)
    return _CLIENTS["google_gemini"]


def _get_openai_direct():
    """Build/cache a standard OpenAI (or OpenAI-compatible) client."""
    if "openai_direct" not in _CLIENTS:
        cfg = _cfg("providers.openai_direct")
        _require(cfg, ["api_key", "model"], "openai-direct", "openai_direct")
        from openai import OpenAI  # lazy import (after config check)
        base_url = str(cfg.get("base_url") or "").strip() or None
        client = OpenAI(api_key=cfg.get("api_key"), base_url=base_url)
        _CLIENTS["openai_direct"] = (client, cfg)
    return _CLIENTS["openai_direct"]


# ── Public dispatch ───────────────────────────────────────────────────

def convert_with_llm(prompt_llm, model_name="openai"):
    """Route a prompt to the configured LLM backend and return its text.

    Configuration errors (blank required config) raise a clear RuntimeError.
    Runtime/API errors are caught and reported, returning 'NA' (unchanged
    behaviour) so a single failed call does not abort the whole pipeline.
    """
    model_name = (model_name or "openai").strip()

    # ── Azure OpenAI — GPT-4o (model_name == "openai") ────────────────
    if model_name == "openai":
        print("Calling LLM with model OpenAI", "INFO")
        try:
            client, cfg = _get_azure_openai(
                "providers.azure_openai_gpt4o",
                ["api_key", "azure_endpoint", "engine"],
                "openai",
            )
            completion = client.chat.completions.create(
                model=cfg.get("engine"),
                messages=[{"role": "user", "content": prompt_llm}],
                temperature=0,
            )
            completion_json = json.loads(completion.model_dump_json(indent=2))
            response = completion_json["choices"][0]["message"]["content"]
        except RuntimeError:
            raise
        except Exception as e:
            response = "NA"
            print(f"OpenAI Error: {e}")
        return response

    # ── Claude via Vertex AI (model_name == "claude") ─────────────────
    elif model_name == "claude":
        print("Calling LLM with model Claude", "INFO")
        try:
            client, cfg = _get_claude()
            message = client.messages.create(
                max_tokens=16384,
                messages=[{"role": "user", "content": prompt_llm}],
                model=cfg.get("model_id"),
                temperature=0.01,
            )
            response = message.content[0].text
        except RuntimeError:
            raise
        except Exception as e:
            response = "NA"
            print(f"Claude Error: {e}")
            import traceback
            traceback.print_exc()
        return response

    # ── Azure OpenAI — GPT-5-chat (model_name == "gpt-5-chat") ────────
    elif model_name == "gpt-5-chat":
        print("Calling LLM with model GPT-5-Chat", "INFO")
        try:
            client, cfg = _get_azure_openai(
                "providers.azure_openai_gpt5_chat",
                ["subscription_key", "endpoint"],
                "gpt-5-chat",
            )
            deployment = (
                cfg.get("deployment") or cfg.get("model_name") or "gpt-5-chat"
            )
            completion = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt_llm}],
                temperature=0,
            )
            completion_json = json.loads(completion.model_dump_json(indent=2))
            response = completion_json["choices"][0]["message"]["content"]
        except RuntimeError:
            raise
        except Exception as e:
            response = ""
            print(f"GPT-5-Chat Error: {e}")
        return response

    # ── Azure OpenAI — GPT-5 (model_name == "gpt-5") ──────────────────
    elif model_name == "gpt-5":
        print("Calling LLM with model GPT-5", "INFO")
        try:
            client, cfg = _get_azure_openai(
                "providers.azure_openai_gpt5",
                ["api_key", "azure_endpoint"],
                "gpt-5",
            )
            deployment = cfg.get("engine") or "gpt-5"
            completion = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": prompt_llm}],
                # NOTE: GPT-5 does not accept a temperature override here.
            )
            completion_json = json.loads(completion.model_dump_json(indent=2))
            response = completion_json["choices"][0]["message"]["content"]
        except RuntimeError:
            raise
        except Exception as e:
            response = "NA"
            print(f"GPT-5 Error: {e}")
        return response

    # ── Google Gemini (model_name == "gemini") ────────────────────────
    elif model_name == "gemini":
        print("Calling LLM with model Gemini", "INFO")
        try:
            model, cfg = _get_gemini()
            result = model.generate_content(
                prompt_llm,
                generation_config={"temperature": 0},
            )
            response = result.text
        except RuntimeError:
            raise
        except Exception as e:
            response = "NA"
            print(f"Gemini Error: {e}")
        return response

    # ── OpenAI / OpenAI-compatible direct API (model_name == "openai-direct") ─
    elif model_name == "openai-direct":
        print("Calling LLM with model OpenAI (direct)", "INFO")
        try:
            client, cfg = _get_openai_direct()
            completion = client.chat.completions.create(
                model=cfg.get("model"),
                messages=[{"role": "user", "content": prompt_llm}],
                temperature=0,
            )
            completion_json = json.loads(completion.model_dump_json(indent=2))
            response = completion_json["choices"][0]["message"]["content"]
        except RuntimeError:
            raise
        except Exception as e:
            response = "NA"
            print(f"OpenAI (direct) Error: {e}")
        return response

    else:
        return "Unsupported model"
