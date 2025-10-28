from datetime import date


def define_env(env):
    current_year = str(date.today().year)
    env.variables["current_year"] = current_year
    env.conf["copyright"] = f"Copyright © {current_year}, Envers Team"
