"""Typed configuration and 64 GB Apple Silicon model profiles (Track A framework-free)."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProviderKind = Literal["ollama", "lmstudio", "mlx", "cloud"]
ApiStyle = Literal["openai_compat", "ollama_native"]


class ConfigError(ValueError):
    """Base error for invalid or unsafe lab configuration."""


class UnknownProfileError(ConfigError):
    """Raised when a requested model profile name is not defined."""


class CloudProfileNotAllowedError(ConfigError):
    """Raised when a cloud profile is requested without explicit opt-in."""


class HardwareBudget(BaseModel):
    """Apple Silicon unified-memory and co-residency guardrails."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    unified_memory_gb: float = Field(gt=0)
    safe_wired_ceiling_gb: float = Field(gt=0)
    max_loaded_models: int = Field(ge=1)
    coresident_roles: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_ceiling(self) -> HardwareBudget:
        if self.safe_wired_ceiling_gb > self.unified_memory_gb:
            raise ValueError(
                f"safe_wired_ceiling_gb ({self.safe_wired_ceiling_gb}) cannot exceed "
                f"unified_memory_gb ({self.unified_memory_gb})"
            )
        return self


class ModelProfile(BaseModel):
    """Configuration for a single local or explicitly opted-in cloud model profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    provider: ProviderKind
    base_url: str = Field(min_length=1)
    native_base_url: str | None = None
    model: str = Field(min_length=1)
    api_style: ApiStyle = "openai_compat"
    num_ctx: int = Field(ge=512)
    keep_alive: str = "15m"
    temperature: float = Field(ge=0.0, le=2.0)
    est_ram_gb: float = Field(ge=0.0)
    is_cloud: bool = False
    enabled: bool = True

    def api_key_placeholder(self) -> str:
        """Return a safe dummy API key placeholder for local OpenAI-compatible clients."""
        if self.is_cloud or self.provider == "cloud":
            raise CloudProfileNotAllowedError(
                f"Profile '{self.name}' is a cloud profile and has no local placeholder key."
            )
        if self.provider == "ollama":
            return "ollama"
        return "lm-studio"


class CoresidencyReport(BaseModel):
    """Summary of estimated RAM and loaded-model slot usage for a set of profiles."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profiles: tuple[ModelProfile, ...]
    total_est_ram_gb: float
    safe_wired_ceiling_gb: float
    headroom_gb: float
    within_budget: bool
    model_count: int
    max_loaded_models: int
    within_slot_limit: bool

    @property
    def ok(self) -> bool:
        return self.within_budget and self.within_slot_limit


class LabConfig(BaseModel):
    """Top-level lab configuration parsed from `models.toml`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    default_profile: str = Field(min_length=1)
    hardware: HardwareBudget
    profiles: dict[str, ModelProfile]
    source_path: Path | None = None

    @model_validator(mode="after")
    def _validate_references(self) -> LabConfig:
        if self.default_profile not in self.profiles:
            raise ValueError(
                f"default_profile '{self.default_profile}' is not present in [profiles]"
            )
        missing_roles = [
            role for role in self.hardware.coresident_roles if role not in self.profiles
        ]
        if missing_roles:
            raise ValueError(
                f"hardware.coresident_roles references unknown profiles: {missing_roles}"
            )
        return self

    def get_profile(self, name: str | None = None, *, allow_cloud: bool = False) -> ModelProfile:
        """Resolve a profile by name (or `HARNESS_LAB_PROFILE` / `default_profile`)."""
        chosen = name or os.environ.get("HARNESS_LAB_PROFILE") or self.default_profile
        profile = self.profiles.get(chosen)
        if profile is None:
            available = ", ".join(sorted(self.profiles))
            raise UnknownProfileError(
                f"Unknown profile '{chosen}'. Available profiles: {available}"
            )
        if profile.is_cloud and (not profile.enabled or not allow_cloud):
            raise CloudProfileNotAllowedError(
                f"Cloud profile '{profile.name}' requires enabled=true in models.toml "
                "and explicit allow_cloud=True opt-in."
            )
        if not profile.enabled:
            raise ConfigError(f"Profile '{profile.name}' is disabled in models.toml.")
        return profile

    def check_coresidency(self, profile_names: Sequence[str] | None = None) -> CoresidencyReport:
        """Sum estimated RAM and slot count for unique co-resident profiles."""
        names = list(profile_names) if profile_names is not None else list(
            self.hardware.coresident_roles
        )
        unique_names = list(dict.fromkeys(names))
        resolved: list[ModelProfile] = []
        for pname in unique_names:
            profile = self.profiles.get(pname)
            if profile is None:
                available = ", ".join(sorted(self.profiles))
                raise UnknownProfileError(
                    f"Unknown profile '{pname}' in co-residency check. Available: {available}"
                )
            resolved.append(profile)

        total_ram = round(sum(p.est_ram_gb for p in resolved), 2)
        ceiling = self.hardware.safe_wired_ceiling_gb
        headroom = round(ceiling - total_ram, 2)
        count = len(resolved)
        return CoresidencyReport(
            profiles=tuple(resolved),
            total_est_ram_gb=total_ram,
            safe_wired_ceiling_gb=ceiling,
            headroom_gb=headroom,
            within_budget=total_ram <= ceiling,
            model_count=count,
            max_loaded_models=self.hardware.max_loaded_models,
            within_slot_limit=count <= self.hardware.max_loaded_models,
        )


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the repository root by searching upwards for `models.toml` or `pyproject.toml`."""
    origin = (start or Path.cwd()).resolve()
    candidates = [origin, *origin.parents]
    for candidate in candidates:
        if (candidate / "models.toml").is_file():
            return candidate
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return origin


def _normalize_openai_base(url: str) -> tuple[str, str]:
    clean = url.strip().rstrip("/")
    if clean.endswith("/v1"):
        return clean, clean[:-3]
    return f"{clean}/v1", clean


def _apply_local_env_overrides(raw_profile: dict[str, object]) -> dict[str, object]:
    updated = dict(raw_profile)
    provider = updated.get("provider")
    if provider == "ollama":
        override = os.environ.get("OLLAMA_BASE_URL")
        if override and override.strip():
            v1_url, native_url = _normalize_openai_base(override)
            updated["base_url"] = v1_url
            updated["native_base_url"] = native_url
    elif provider == "lmstudio":
        override = os.environ.get("LM_STUDIO_BASE_URL")
        if override and override.strip():
            v1_url, _ = _normalize_openai_base(override)
            updated["base_url"] = v1_url
    return updated


def load_config(path: Path | str | None = None) -> LabConfig:
    """Load and validate `models.toml` with safe local runtime URL overrides."""
    config_path = Path(path) if path is not None else find_repo_root() / "models.toml"
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    with config_path.open("rb") as fh:
        raw_data = tomllib.load(fh)

    raw_profiles = raw_data.get("profiles")
    if not isinstance(raw_profiles, dict) or not raw_profiles:
        raise ConfigError(f"No [profiles.*] entries found in {config_path}")

    profiles_payload: dict[str, dict[str, object]] = {}
    for pname, pdata in raw_profiles.items():
        if not isinstance(pdata, dict):
            raise ConfigError(f"Profile '{pname}' must be a TOML table.")
        merged = _apply_local_env_overrides({"name": pname, **pdata})
        profiles_payload[pname] = merged

    payload = {
        "default_profile": raw_data.get("default_profile"),
        "hardware": raw_data.get("hardware"),
        "profiles": profiles_payload,
        "source_path": config_path.resolve(),
    }
    try:
        return LabConfig.model_validate(payload)
    except Exception as exc:
        raise ConfigError(f"Invalid configuration in {config_path}: {exc}") from exc
