class AgnoCostModel:
    def __init__(self, model_name, provider, input_cost_per_million, output_cost_per_million):
        self.model_name = model_name
        self.provider = provider
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

        if input_cost_per_million < 0 or output_cost_per_million < 0:
            raise ValueError("Cost per million cannot be negative")

    def calculate_cost(self, prompt_tokens, completion_tokens):
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token counts cannot be negative")

        input_cost = (prompt_tokens * self.input_cost_per_million) / 1000000
        output_cost = (completion_tokens * self.output_cost_per_million) / 1000000

        return input_cost + output_cost

class AgnoCostCalculator:
    def __init__(self):
        self.models = {}

    def register_model(self, model_name, provider, input_cost_per_million, output_cost_per_million):
        self.models[model_name] = AgnoCostModel(model_name, provider, input_cost_per_million, output_cost_per_million)

    def calculate_cost(self, model_name, prompt_tokens, completion_tokens):
        if model_name not in self.models:
            return 0.0
        return self.models[model_name].calculate_cost(prompt_tokens, completion_tokens)
