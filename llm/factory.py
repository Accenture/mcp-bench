"""LLM Factory Module.

This module handles model configuration and factory creation for different LLM
providers, supporting multiple model types and deployment configurations.

Classes:
    ModelConfig: Configuration container for specific models
    LLMFactory: Factory for creating LLM provider instances
"""

import os
from typing import Dict, Any
from openai import AsyncOpenAI
import google.generativeai as genai
from .provider import LLMProvider


class ModelConfig:
    """Configuration container for a specific model.

    Stores model-specific configuration including provider type,
    API credentials, and deployment details.

    Attributes:
        name: Model name identifier
        provider_type: Type of provider ('azure', 'openai', etc.)
        config: Dictionary of additional configuration parameters

    Example:
        >>> config = ModelConfig("gpt-4o", "azure", api_key="...", endpoint="...")
    """

    def __init__(self, name: str, provider_type: str, **kwargs: Any) -> None:
        """Initialize model configuration.

        Args:
            name: Model name identifier
            provider_type: Type of provider ('azure', 'openai', etc.)
            **kwargs: Additional configuration parameters
        """
        self.name: str = name
        self.provider_type: str = provider_type
        self.config: Dict[str, Any] = kwargs


class LLMFactory:
    """Factory for creating LLM providers for different models.

    This class manages model configurations and creates appropriate
    LLM provider instances based on the model type and configuration.

    Example:
        >>> configs = LLMFactory.get_model_configs()
        >>> provider = await LLMFactory.create_llm_provider(configs["gpt-4o"])
    """

    @staticmethod
    def get_model_configs() -> Dict[str, ModelConfig]:
        """Get all available model configurations from environment variables.

        Scans environment variables to detect available API keys and endpoints,
        then creates ModelConfig instances for each available model.

        Returns:
            Dictionary mapping model names to ModelConfig instances
        """
        configs = {}

        # OpenAI models (using OPENAI_API_KEY)
        if os.getenv("OPENAI_API_KEY"):
            base_url = "https://api.openai.com/v1"
            api_key = os.getenv("OPENAI_API_KEY")

            configs["o4-mini"] = ModelConfig(
                name="o4-mini",
                provider_type="openai",
                api_key=api_key,
                base_url=base_url,
                model_name="o4-mini",
            )

            configs["gpt-4o"] = ModelConfig(
                name="gpt-4o",
                provider_type="openai",
                api_key=api_key,
                base_url=base_url,
                model_name="gpt-4o",
            )

            configs["gpt-4o-mini"] = ModelConfig(
                name="gpt-4o-mini",
                provider_type="openai",
                api_key=api_key,
                base_url=base_url,
                model_name="gpt-4o-mini",
            )

            configs["o3"] = ModelConfig(
                name="o3",
                provider_type="openai",
                api_key=api_key,
                base_url=base_url,
                model_name="o3",
            )

            configs["gpt-5"] = ModelConfig(
                name="gpt-5",
                provider_type="openai",
                api_key=api_key,
                base_url=base_url,
                model_name="gpt-5",
            )

        # Gemini models (using GEMINI_API_KEY)
        if os.getenv("GEMINI_API_KEY"):
            api_key = os.getenv("GEMINI_API_KEY")

            configs["gemini-3-pro-preview"] = ModelConfig(
                name="gemini-3-pro-preview",
                provider_type="gemini",
                api_key=api_key,
                model_name="gemini-3-pro-preview",
            )

            configs["gemini-2.0-flash-exp"] = ModelConfig(
                name="gemini-2.0-flash-exp",
                provider_type="gemini",
                api_key=api_key,
                model_name="gemini-2.0-flash-exp",
            )

            configs["gemini-1.5-pro"] = ModelConfig(
                name="gemini-1.5-pro",
                provider_type="gemini",
                api_key=api_key,
                model_name="gemini-1.5-pro",
            )

            configs["gemini-1.5-flash"] = ModelConfig(
                name="gemini-1.5-flash",
                provider_type="gemini",
                api_key=api_key,
                model_name="gemini-1.5-flash",
            )

            configs["gemini-1.5-flash-8b"] = ModelConfig(
                name="gemini-1.5-flash-8b",
                provider_type="gemini",
                api_key=api_key,
                model_name="gemini-1.5-flash-8b",
            )

        return configs

    @staticmethod
    async def create_llm_provider(model_config: ModelConfig) -> LLMProvider:
        """Create an LLM provider for the given model configuration.

        Creates appropriate client and provider instance based on the
        model configuration's provider type.

        Args:
            model_config: Configuration for the model to create

        Returns:
            Configured LLMProvider instance

        Raises:
            ValueError: If provider type is not supported
        """

        if model_config.provider_type == "openai":
            client = AsyncOpenAI(
                api_key=model_config.config["api_key"],
                base_url=model_config.config["base_url"],
            )
            return LLMProvider(
                client=client,
                deployment_name=model_config.config["model_name"],
                provider_type="openai",
            )
        elif model_config.provider_type == "gemini":
            # Configure Gemini API
            genai.configure(api_key=model_config.config["api_key"])
            # Create a GenerativeModel instance
            client = genai.GenerativeModel(model_config.config["model_name"])
            return LLMProvider(
                client=client,
                deployment_name=model_config.config["model_name"],
                provider_type="gemini",
            )
        else:
            raise ValueError(
                f"Unsupported provider type: {model_config.provider_type}. Supported types: 'openai', 'gemini'."
            )
