import os
import json
import re
from typing import List, Literal, Optional, Tuple
import httpx
from pydantic import BaseModel, Field, model_validator
from typing import Any

class BumpAnalysis(BaseModel):
    bump_type: Literal["major", "minor", "patch", "none"] = Field(
        default="patch",
        description="The SemVer bump level: major, minor, patch, or none"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    commit_message: str = Field(
        default="",
        description="Concise Conventional Commit message (e.g. 'feat: ...' or 'fix: ...') summarizing the code changes"
    )
    reasoning: str = Field(
        default="AI completed SemVer analysis.",
        description="Detailed explanation of why this bump level was chosen based on the diff and commits"
    )
    breaking_changes: List[str] = Field(
        default_factory=list,
        description="List of breaking changes identified, if any"
    )
    key_changes: List[str] = Field(
        default_factory=list,
        description="List of key changes, features, or bug fixes detected"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Check for provider error messages
        if "error" in data:
            err = data["error"]
            err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise ValueError(f"AI Provider error: {err_msg}")

        # Unwrap if inside nested containers: "analysis", "result", "data", "response", "semver"
        for container_key in ["analysis", "result", "data", "response", "semver", "version_bump", "recommendation"]:
            if container_key in data and isinstance(data[container_key], dict):
                inner = data[container_key]
                for k, v in inner.items():
                    data.setdefault(k, v)

        # Normalize bump_type synonyms and aliases
        if "bump_type" not in data or not data["bump_type"]:
            for alt in ["bumpType", "bump", "type", "level", "semver_bump", "version_bump", "action", "recommendation"]:
                if alt in data and isinstance(data[alt], str):
                    data["bump_type"] = data[alt]
                    break

        if "bump_type" in data and isinstance(data["bump_type"], str):
            val = data["bump_type"].lower().strip()
            if "major" in val:
                data["bump_type"] = "major"
            elif "minor" in val:
                data["bump_type"] = "minor"
            elif "patch" in val:
                data["bump_type"] = "patch"
            elif "none" in val:
                data["bump_type"] = "none"
            else:
                data["bump_type"] = "patch"
        else:
            data["bump_type"] = "patch"

        # Normalize reasoning synonyms and aliases
        if "reasoning" not in data or not data["reasoning"]:
            for alt in ["reason", "explanation", "rationale", "description", "details", "summary", "justification", "notes"]:
                if alt in data and data[alt]:
                    data["reasoning"] = str(data[alt])
                    break
        if not data.get("reasoning"):
            data["reasoning"] = "AI analyzed code diff and recommended this SemVer shift."

        # Normalize commit_message synonyms
        if "commit_message" not in data or not data["commit_message"]:
            for alt in ["commitMessage", "commit_msg", "suggested_commit_message", "conventional_commit", "message"]:
                if alt in data and data[alt]:
                    data["commit_message"] = str(data[alt])
                    break

        # Normalize confidence
        if "confidence" not in data:
            for alt in ["confidence_score", "score"]:
                if alt in data:
                    data["confidence"] = data[alt]
                    break
        try:
            conf = float(data.get("confidence", 1.0))
            if conf > 1.0:
                conf = conf / 100.0
            data["confidence"] = max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            data["confidence"] = 0.95

        # Normalize breaking_changes
        if "breaking_changes" not in data:
            for alt in ["breakingChanges", "breaking"]:
                if alt in data:
                    data["breaking_changes"] = data[alt]
                    break
        if isinstance(data.get("breaking_changes"), str):
            data["breaking_changes"] = [data["breaking_changes"]]
        elif not isinstance(data.get("breaking_changes"), list):
            data["breaking_changes"] = []

        # Normalize key_changes
        if "key_changes" not in data:
            for alt in ["keyChanges", "changes"]:
                if alt in data:
                    data["key_changes"] = data[alt]
                    break
        if isinstance(data.get("key_changes"), str):
            data["key_changes"] = [data["key_changes"]]
        elif not isinstance(data.get("key_changes"), list):
            data["key_changes"] = []

        return data

SYSTEM_PROMPT = """You are an expert software engineer and Semantic Versioning (SemVer 2.0.0) analyst.
Your task is to analyze the provided Git commit logs and code diff, and decide whether the next release should be:
- "major": Contains backwards-incompatible API changes, breaking changes, removed public endpoints/functions/classes/parameters, or major breaking redesigns.
- "minor": Adds new functionality or features in a backwards-compatible manner, or introduces new deprecations without removing old APIs.
- "patch": Backwards-compatible bug fixes, minor refactoring, dependency updates, internal optimizations, or documentation changes.
- "none": No functional code or behavior changes warranting a version increment.

Important context on CLI tools & Applications:
- If the project is a CLI tool or application (indicated by CLI arguments, Typer/Click/Argparse, or executable entrypoints), user-facing backwards compatibility is determined primarily by the CLI commands, options, and workflow.
- Internal refactoring or changes to private/internal helper functions within a CLI tool are NOT breaking changes if the CLI command-line behavior remains compatible; classify them as "minor" (if adding new features/options) or "patch" (if refactoring/fixes), NOT "major".

Also formulate a clear, concise Conventional Commit message (e.g., "feat: ...", "fix: ...", "refactor: ...") that accurately summarizes the overall code diff.

Analyze with strict attention to public API contracts, function signatures, and exported variables.
You MUST output valid JSON matching this exact structure:
{
  "bump_type": "major" | "minor" | "patch" | "none",
  "confidence": 0.95,
  "commit_message": "feat(core): concise Conventional Commit message summarizing the changes",
  "reasoning": "Explanation of the decision",
  "breaking_changes": ["detail of breaking change 1", ...],
  "key_changes": ["summary of change 1", ...]
}
Output ONLY the JSON object. Do not wrap in markdown or include additional text.
"""

from shift_this_version import config

def extract_json_from_text(text: str) -> dict:
    """ทำความสะอาดและแปลงข้อความตอบกลับจาก LLM ให้เป็น JSON dict อย่างแม่นยำและทนทาน"""
    if not text or not text.strip():
        raise ValueError("Received empty response from AI model.")

    cleaned = text.strip()

    # 1. ลบ thinking block จาก reasoning models (<think>...</think>)
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", cleaned, flags=re.IGNORECASE).strip()

    # 2. ตรวจหา markdown code fence ```json ... ``` หรือ ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                return parsed[0]
        except Exception:
            pass

    # 3. ลอง parse ข้อความทั้งหมดโดยตรง
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
            return parsed[0]
    except Exception:
        pass

    # 4. หากมีข้อความเกริ่นนำหรือสรุปท้าย ให้หา outermost { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                return parsed[0]
        except Exception:
            # ลองแก้ไข trailing commas
            try:
                fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
                parsed = json.loads(fixed)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

    snippet = cleaned[:200] + ("..." if len(cleaned) > 200 else "")
    raise ValueError(f"Could not parse valid JSON from AI response: {snippet}")

def get_key_for_provider(provider: str, explicit_key: Optional[str] = None) -> Optional[str]:
    """
    ดึง API Key ตามลำดับความสำคัญ:
    1. ส่งผ่าน parameter/flag โดยตรง
    2. ค่าที่บันทึกไว้ใน ~/.shift-this-version/config.json
    3. Tool-specific Environment variable (เช่น SHIFT_GEMINI_API_KEY)
    4. General Environment variable (เช่น GEMINI_API_KEY)
    """
    if explicit_key:
        return explicit_key

    prov = provider.lower()
    # 1. จาก config.json
    configured = config.get_configured_key(prov)
    if configured:
        return configured

    # 2. จาก Environment Variables
    env_names = {
        "gemini": ["SHIFT_GEMINI_API_KEY", "GEMINI_API_KEY"],
        "anthropic": ["SHIFT_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"],
        "openrouter": ["SHIFT_OPENROUTER_API_KEY", "OPENROUTER_API_KEY"],
        "openai": ["SHIFT_OPENAI_API_KEY", "OPENAI_API_KEY"],
        "deepseek": ["SHIFT_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"],
        "groq": ["SHIFT_GROQ_API_KEY", "GROQ_API_KEY"],
        "custom": ["SHIFT_CUSTOM_API_KEY", "CUSTOM_API_KEY"],
    }
    for env_var in env_names.get(prov, []):
        val = os.getenv(env_var)
        if val:
            return val
    return None

def is_ollama_running(host: str = "http://localhost:11434") -> bool:
    """Check if local Ollama daemon is reachable with a fast 1.0s timeout."""
    try:
        with httpx.Client(timeout=1.0) as client:
            resp = client.get(f"{host.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False

def detect_default_provider() -> Tuple[Optional[str], Optional[str]]:
    """ตรวจจับ provider และ key ที่พร้อมใช้งานอัตโนมัติ"""
    # 1. ดูจาก default_provider ใน config.json
    cfg_default = config.get_default_provider()
    if cfg_default:
        key = get_key_for_provider(cfg_default)
        if key or cfg_default in ("ollama", "custom"):
            return cfg_default, key

    # 2. ตรวจเช็คทีละ provider ตามลำดับความนิยม
    for prov in ["gemini", "anthropic", "openrouter", "deepseek", "groq", "openai"]:
        key = get_key_for_provider(prov)
        if key:
            return prov, key

    # 3. ตรวจสอบว่ามี Ollama รันอยู่จริงหรือไม่ ก่อนจะเลือกใช้งาน
    ollama_host = config.get_configured_host("ollama") or os.getenv("OLLAMA_HOST", "http://localhost:11434")
    if is_ollama_running(ollama_host):
        return "ollama", ollama_host

    # 4. หากไม่มี provider หรือ key ที่พร้อมใช้งานเลย คืน None
    return None, None



def call_gemini(diff: str, commits: List[str], api_key: str, model: str = "gemini-2.5-flash") -> BumpAnalysis:
    """เรียก Google Gemini REST API"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{
            "parts": [{
                "text": f"Commits since last release:\n" + "\n".join(commits) + f"\n\nCode Diff:\n{diff}"
            }]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = extract_json_from_text(raw_text)
        return BumpAnalysis(**parsed)

def call_anthropic(diff: str, commits: List[str], api_key: str, model: str = "claude-3-5-haiku-20241022") -> BumpAnalysis:
    """เรียก Anthropic Claude Messages REST API"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    user_content = f"Commits since last release:\n" + "\n".join(commits) + f"\n\nCode Diff:\n{diff}"
    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.0
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["content"][0]["text"]
        parsed = extract_json_from_text(raw_text)
        return BumpAnalysis(**parsed)

def call_openai_compatible(
    diff: str,
    commits: List[str],
    api_key: str,
    base_url: str,
    model: str,
    extra_headers: Optional[dict] = None
) -> BumpAnalysis:
    """เรียก OpenAI-compatible API (รองรับ OpenAI, OpenRouter, DeepSeek, Groq, Custom)"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if extra_headers:
        headers.update(extra_headers)

    url = f"{base_url.rstrip('/')}/chat/completions"
    user_content = f"Commits since last release:\n" + "\n".join(commits) + f"\n\nCode Diff:\n{diff}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        # ถ้า provider ไม่รองรับ response_format ให้ retry โดยเอา response_format ออก
        if resp.status_code == 400 and "response_format" in resp.text.lower():
            payload.pop("response_format", None)
            resp = client.post(url, headers=headers, json=payload)

        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise ValueError(f"AI Provider error: {err_msg}")

        choices = data.get("choices", [])
        if not choices:
            raise ValueError(f"No completion choices returned by AI provider: {data}")

        msg = choices[0].get("message", {})
        raw_text = msg.get("content") or msg.get("reasoning_content") or ""
        parsed = extract_json_from_text(raw_text)
        return BumpAnalysis(**parsed)

def call_ollama(diff: str, commits: List[str], host: str = "http://localhost:11434", model: str = "llama3.2") -> BumpAnalysis:
    """เรียก Ollama Local REST API"""
    url = f"{host.rstrip('/')}/api/chat"
    user_content = f"Commits since last release:\n" + "\n".join(commits) + f"\n\nCode Diff:\n{diff}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.0}
    }
    with httpx.Client(timeout=90.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["message"]["content"]
        parsed = extract_json_from_text(raw_text)
        return BumpAnalysis(**parsed)

def analyze(
    diff: str,
    commits: List[str],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    host: Optional[str] = None
) -> BumpAnalysis:
    """
    ฟังก์ชันหลักสำหรับส่ง Diff ไปให้ AI วิเคราะห์
    รองรับ: gemini, anthropic, openrouter, deepseek, groq, openai, ollama, custom
    """
    if not provider or provider == "auto":
        detected_prov, detected_key = detect_default_provider()
        if not detected_prov:
            raise ValueError(
                "No configured AI provider or active API key found. "
                "Please run 'shift-this-version config' to select an AI provider and enter your API key."
            )
        provider = detected_prov
        if not api_key:
            api_key = detected_key

    provider = provider.lower()
    # ดึงค่า model และ host จาก config หากไม่ได้ระบุผ่าน CLI
    chosen_model = model or config.get_configured_model(provider)
    chosen_host = host or config.get_configured_host(provider)

    # 1. กลุ่ม Direct Cloud Giants
    if provider == "gemini":
        key = get_key_for_provider("gemini", api_key)
        if not key:
            raise ValueError("Gemini API key is not found. Run 'shift-this-version config' or set GEMINI_API_KEY.")
        target_model = chosen_model or "gemini-2.5-flash"
        return call_gemini(diff, commits, api_key=key, model=target_model)

    elif provider == "anthropic":
        key = get_key_for_provider("anthropic", api_key)
        if not key:
            raise ValueError("Anthropic API key is not found. Run 'shift-this-version config' or set ANTHROPIC_API_KEY.")
        target_model = chosen_model or "claude-3-5-haiku-20241022"
        return call_anthropic(diff, commits, api_key=key, model=target_model)

    elif provider == "openai":
        key = get_key_for_provider("openai", api_key)
        if not key:
            raise ValueError("OpenAI API key is not found. Run 'shift-this-version config' or set OPENAI_API_KEY.")
        target_model = chosen_model or "gpt-4o-mini"
        return call_openai_compatible(
            diff, commits, api_key=key,
            base_url="https://api.openai.com/v1",
            model=target_model
        )

    # 2. กลุ่ม High-Speed & Value Powerhouses
    elif provider == "deepseek":
        key = get_key_for_provider("deepseek", api_key)
        if not key:
            raise ValueError("DeepSeek API key is not found. Run 'shift-this-version config' or set DEEPSEEK_API_KEY.")
        target_model = chosen_model or "deepseek-chat"
        return call_openai_compatible(
            diff, commits, api_key=key,
            base_url="https://api.deepseek.com/v1",
            model=target_model
        )

    elif provider == "groq":
        key = get_key_for_provider("groq", api_key)
        if not key:
            raise ValueError("Groq API key is not found. Run 'shift-this-version config' or set GROQ_API_KEY.")
        target_model = chosen_model or "llama-3.3-70b-versatile"
        return call_openai_compatible(
            diff, commits, api_key=key,
            base_url="https://api.groq.com/openai/v1",
            model=target_model
        )

    # 3. กลุ่ม Universal Hub (OpenRouter)
    elif provider == "openrouter":
        key = get_key_for_provider("openrouter", api_key)
        if not key:
            raise ValueError("OpenRouter API key is not found. Run 'shift-this-version config' or set OPENROUTER_API_KEY.")
        target_model = chosen_model or "google/gemini-2.0-flash-001"
        return call_openai_compatible(
            diff, commits, api_key=key,
            base_url="https://openrouter.ai/api/v1",
            model=target_model,
            extra_headers={"HTTP-Referer": "https://github.com/shift-this-version", "X-Title": "shift-this-version"}
        )

    # 4. กลุ่ม Local & Self-Hosted
    elif provider == "ollama":
        target_host = chosen_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        if not is_ollama_running(target_host):
            raise ConnectionError(
                f"Could not connect to Ollama at '{target_host}'. "
                "Please verify that the Ollama service is running, or run 'shift-this-version config' to switch providers."
            )
        target_model = chosen_model or "llama3.2"
        return call_ollama(diff, commits, host=target_host, model=target_model)

    elif provider in ("custom", "localai"):
        base_url = chosen_host or os.getenv("CUSTOM_API_BASE", "http://localhost:1234/v1")
        target_model = chosen_model or "local-model"
        key = get_key_for_provider("custom", api_key) or "not-needed"
        return call_openai_compatible(
            diff, commits, api_key=key,
            base_url=base_url,
            model=target_model
        )

    else:
        raise ValueError(
            f"Unsupported provider: '{provider}'. Choose from: gemini, anthropic, openai, deepseek, groq, openrouter, ollama, custom."
        )

