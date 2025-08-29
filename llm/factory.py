"""LLM Factory Module.

This module handles model configuration and factory creation for different LLM 
providers, supporting multiple model types and deployment configurations.

Classes:
    ModelConfig: Configuration container for specific models
    LLMFactory: Factory for creating LLM provider instances
"""

import os
from typing import Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI
from .provider import LLMProvider
import config.config_loader as config_loader


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
        
        # Azure OpenAI models
        if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
            configs["o4-mini"] = ModelConfig(
                name="o4-mini",
                provider_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name="o4-mini"
            )
            
            configs["gpt-4o"] = ModelConfig(
                name="gpt-4o",
                provider_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name="gpt-4o"
            )
            
            configs["gpt-4o-mini"] = ModelConfig(
                name="gpt-4o-mini",
                provider_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name="gpt-4o-mini"
            )
            
            configs["o3"] = ModelConfig(
                name="o3",
                provider_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name="o3"
            )
        
            configs["gpt-5"] = ModelConfig(
                name="gpt-5",
                provider_type="azure",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                deployment_name="gpt-5"
            )
        
        # OpenRouter models
        if os.getenv("OPENROUTER_API_KEY"):
            configs["qwen-3-32b"] = ModelConfig(
                name="qwen-3-32b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwen3-32b"
            )
            
            configs["qwen3-30b-a3b-instruct-2507"] = ModelConfig(
                name="qwen3-30b-a3b-instruct-2507",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwen3-30b-a3b-instruct-2507"
            )
            
            configs["qwen3-235b-a22b-thinking-2507"] = ModelConfig(
                name="qwen3-235b-a22b-thinking-2507",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwen3-235b-a22b-thinking-2507"
            )

            configs["qwen3-235b-a22b-2507"] = ModelConfig(
                name="qwen3-235b-a22b-2507",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwen3-235b-a22b-2507"
            )
            
            configs["gpt-oss-20b"] = ModelConfig(
                name="gpt-oss-20b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="openai/gpt-oss-20b"
            )
            
            configs["gpt-oss-120b"] = ModelConfig(
                name="gpt-oss-120b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="openai/gpt-oss-120b"
            )
            
            configs["kimi-k2"] = ModelConfig(
                name="kimi-k2",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="moonshotai/kimi-k2"
            )
            
            configs["minimax-m1"] = ModelConfig(
                name="minimax-m1",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="minimax/minimax-m1"
            )
            
            configs["nova-micro-v1"] = ModelConfig(
                name="nova-micro-v1",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="amazon/nova-micro-v1"
            )
            
            configs["grok-3-mini"] = ModelConfig(
                name="grok-3-mini",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="x-ai/grok-3-mini"
            )
            
            configs["gemini-2.5-flash-lite"] = ModelConfig(
                name="gemini-2.5-flash-lite",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="google/gemini-2.5-flash-lite"
            )
            
            configs["gpt-5-mini-openrouter"] = ModelConfig(
                name="gpt-5-mini-openrouter",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="openai/gpt-5-mini"
            )
            
            configs["gpt-5-nano"] = ModelConfig(
                name="gpt-5-nano",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="openai/gpt-5-nano"
            )
            
            configs["deepseek-r1-0528"] = ModelConfig(
                name="deepseek-r1-0528",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="deepseek/deepseek-r1-0528"
            )
            
            configs["deepseek-r1-0528-qwen3-8b"] = ModelConfig(
                name="deepseek-r1-0528-qwen3-8b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="deepseek/deepseek-r1-0528-qwen3-8b"
            )
            
            configs["ernie-4.5-21b-a3b"] = ModelConfig(
                name="ernie-4.5-21b-a3b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="baidu/ernie-4.5-21b-a3b"
            )
            
            configs["glm-4.5-air"] = ModelConfig(
                name="glm-4.5-air",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="z-ai/glm-4.5-air"
            )
            
            configs["mistral-small-3.2-24b-instruct"] = ModelConfig(
                name="mistral-small-3.2-24b-instruct",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="mistralai/mistral-small-3.2-24b-instruct"
            )
            
            configs["gemma-3-27b-it"] = ModelConfig(
                name="gemma-3-27b-it",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="google/gemma-3-27b-it"
            )
            
            configs["qwq-32b"] = ModelConfig(
                name="qwq-32b",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="qwen/qwq-32b"
            )
            
            configs["glm-4.5"] = ModelConfig(
                name="glm-4.5",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="z-ai/glm-4.5"
            )
            
            configs["claude-sonnet-4"] = ModelConfig(
                name="claude-sonnet-4",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="anthropic/claude-sonnet-4"
            )
            
            configs["gemini-2.5-pro"] = ModelConfig(
                name="gemini-2.5-pro",
                provider_type="openrouter",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                model_name="google/gemini-2.5-pro"
            )
        
        # Llama models
        llama_models = [
            ("llama-4-maverick", "LLAMA_4_MAVERICK"),
            ("llama-3-2-90b", "LLAMA_3_2_90B"),
            ("llama-3-3-70b", "LLAMA_3_3_70B"),
            ("llama-3-1-70b-instruct", "LLAMA_3_1_70B_INSTRUCT"),
            ("llama-3-1-70b-dev", "LLAMA_3_1_70B_DEV"),
            ("llama-3-1-8b", "LLAMA_3_1_8B")
        ]
        
        for model_name, env_prefix in llama_models:
            api_key = os.getenv(f"{env_prefix}_API_KEY")
            if api_key:
                configs[model_name] = ModelConfig(
                    name=model_name,
                    provider_type="openai_compatible",
                    api_key=api_key,
                    base_url=os.getenv(f"{env_prefix}_BASE_URL"),
                    model_name=os.getenv(f"{env_prefix}_MODEL")
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
        
        if model_config.provider_type == "azure":
            client = AsyncAzureOpenAI(
                azure_endpoint=model_config.config["endpoint"],
                api_key=model_config.config["api_key"],
                api_version=config_loader.get_azure_api_version()
            )
            return LLMProvider(
                client=client,
                deployment_name=model_config.config["deployment_name"],
                provider_type="azure"
            )
            
        elif model_config.provider_type == "openai_compatible":
            client = AsyncOpenAI(
                api_key=model_config.config["api_key"],
                base_url=model_config.config["base_url"]
            )
            return LLMProvider(
                client=client,
                deployment_name=model_config.config["model_name"],
                provider_type="openai_compatible"
            )
        elif model_config.provider_type == "openrouter":
            client = AsyncOpenAI(
                api_key=model_config.config["api_key"],
                base_url=model_config.config["base_url"]
            )
            return LLMProvider(
                client=client,
                deployment_name=model_config.config["model_name"],
                provider_type="openrouter"
            )
        else:
            raise ValueError(f"Unsupported provider type: {model_config.provider_type}")