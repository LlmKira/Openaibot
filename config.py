from dynaconf import Dynaconf

# 禁止机密从此文件中泄露

provider_settings = Dynaconf(
    envvar_prefix="LLMKIRA",
    settings_files=['config_dir/provider.toml'],
)

llm_settings = Dynaconf(
    envvar_prefix="LLMKIRA",
    settings_files=['config_dir/llm.toml'],
)
