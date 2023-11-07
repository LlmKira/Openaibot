from dynaconf import Dynaconf

provider_settings = Dynaconf(
    envvar_prefix="LLMKIRA",
    settings_files=['config_dir/provider.toml'],
)

llm_settings = Dynaconf(
    envvar_prefix="LLMKIRA",
    settings_files=['config_dir/llm.toml'],
)
