class AgnoCostModel:
    """
    Agno-specific cost tracking model for LLM API usage.

    This model tracks costs for language model API calls with separate pricing
    for input (prompt) and output (completion) tokens, which is standard for
    modern LLM providers like OpenAI, Anthropic, and others.

    Args:
        model_name: Name of the model (e.g., "claude-3-5-sonnet-20241022", "gpt-4o-mini")
        provider: API provider name (e.g., "anthropic", "openai", "openrouter")
        input_cost_per_million: Cost per 1 million input tokens in USD
        output_cost_per_million: Cost per 1 million output tokens in USD

    Raises:
        ValueError: If cost_per_million values are negative

    Example:
        >>> # Create cost model for Claude Sonnet
        >>> claude_model = AgnoCostModel(
        ...     model_name="claude-3-5-sonnet-20241022",
        ...     provider="anthropic",
        ...     input_cost_per_million=3.00,   # $3.00 per 1M input tokens
        ...     output_cost_per_million=15.00   # $15.00 per 1M output tokens
        ... )
        >>> # Calculate cost for 1000 input tokens and 500 output tokens
        >>> cost = claude_model.calculate_cost(1000, 500)
        >>> print(f"${cost:.6f}")  # $0.010500
        $0.010500
    """
    def __init__(self, model_name: str, provider: str, input_cost_per_million: float, output_cost_per_million: float):
        self.model_name = model_name
        self.provider = provider
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

        if input_cost_per_million < 0 or output_cost_per_million < 0:
            raise ValueError("Cost per million cannot be negative")

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate total cost based on token usage.

        Args:
            prompt_tokens: Number of input/prompt tokens used
            completion_tokens: Number of output/completion tokens used

        Returns:
            Total cost in USD

        Raises:
            ValueError: If token counts are negative

        Example:
            >>> model = AgnoCostModel("gpt-4o-mini", "openai", 0.15, 0.60)
            >>> cost = model.calculate_cost(500, 250)
            >>> print(f"${cost:.6f}")  # $0.000225
            $0.000225
        """
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        input_cost = (prompt_tokens * self.input_cost_per_million) / 1000000
        output_cost = (completion_tokens * self.output_cost_per_million) / 1000000

        return input_cost + output_cost

class AgnoCostCalculator:
    """
    Cost calculator for managing multiple LLM models and tracking costs.

    This calculator maintains a registry of cost models for different LLM providers
    and models, allowing centralized cost calculation across multiple agents and
    API calls.

    Example:
        >>> # Initialize calculator
        >>> calculator = AgnoCostCalculator()
        >>>
        >>> # Register models
        >>> calculator.register_model(
        ...     "claude-3-5-sonnet-20241022",
        ...     "anthropic",
        ...     3.00,   # $3.00 per 1M input tokens
        ...     15.00   # $15.00 per 1M output tokens
        ... )
        >>> calculator.register_model(
        ...     "gpt-4o-mini",
        ...     "openai",
        ...     0.15,   # $0.15 per 1M input tokens
        ...     0.60    # $0.60 per 1M output tokens
        ... )
        >>>
        >>> # Calculate costs for different models
        >>> claude_cost = calculator.calculate_cost("claude-3-5-sonnet-20241022", 1000, 500)
        >>> gpt_cost = calculator.calculate_cost("gpt-4o-mini", 500, 250)
        >>> print(f"Claude cost: ${claude_cost:.6f}, GPT cost: ${gpt_cost:.6f}")
        Claude cost: $0.010500, GPT cost: $0.000225
    """

    def __init__(self):
        """Initialize the calculator with empty model registry."""
        self.models = {}

    def register_model(
        self,
        model_name: str,
        provider: str,
        input_cost_per_million: float,
        output_cost_per_million: float
    ) -> None:
        """
        Register a model with its pricing information.

        Args:
            model_name: Name of the model
            provider: API provider name
            input_cost_per_million: Cost per 1M input tokens in USD
            output_cost_per_million: Cost per 1M output tokens in USD

        Example:
            >>> calculator = AgnoCostCalculator()
            >>> calculator.register_model("claude-haiku-4.5", "anthropic", 0.80, 4.00)
        """
        self.models[model_name] = AgnoCostModel(
            model_name, provider, input_cost_per_million, output_cost_per_million
        )

    def calculate_cost(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for a specific model usage.

        Args:
            model_name: Name of the registered model
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Total cost in USD, or 0.0 if model not registered

        Example:
            >>> calculator = AgnoCostCalculator()
            >>> calculator.register_model("gpt-4o-mini", "openai", 0.15, 0.60)
            >>> cost = calculator.calculate_cost("gpt-4o-mini", 1000, 500)
            >>> print(f"${cost:.6f}")
            $0.000450
        """
        if model_name not in self.models:
            return 0.0
        return self.models[model_name].calculate_cost(prompt_tokens, completion_tokens)
