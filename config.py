from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="LLMKIRA",
    settings_files=['settings.toml', '.secrets.toml'],
)
