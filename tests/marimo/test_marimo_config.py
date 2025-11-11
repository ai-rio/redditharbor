from marimo_notebooks.config import MarimoConfig


def test_marimo_config_initialization():
    config = MarimoConfig()
    assert config.supabase_url is not None
    assert config.supabase_key is not None
    assert config.database_config is not None
