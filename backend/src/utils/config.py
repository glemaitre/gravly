"""Configuration management utilities for loading environment variables."""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_environment_config(project_root: Optional[Path] = None) -> None:
    """Load environment variables from the appropriate .env file.

    This function looks for environment-specific .env files in the .env folder
    and provides helpful error messages if no configuration is found.

    Parameters
    ----------
    project_root : Path, optional
        Path to the project root directory. If None, will be automatically
        determined from the current file location.

    Raises
    ------
    FileNotFoundError
        If no environment file is found and no examples are available.
    """
    if project_root is None:
        # Default to the project root (4 levels up from this file: config.py -> utils -> src -> backend -> project_root)
        project_root = Path(__file__).parent.parent.parent.parent

    environment = os.getenv("ENVIRONMENT", "local")
    env_file = project_root / ".env" / environment

    if env_file.exists():
        load_dotenv(env_file, override=True)
        logging.info(f"Loaded environment variables from {env_file}")
        return

    # Check if .env folder exists and contains example files
    env_folder = project_root / ".env"
    if env_folder.exists() and env_folder.is_dir():
        example_files = list(env_folder.glob("*.example"))
        if example_files:
            example_list = ", ".join([f.name for f in example_files])
            raise FileNotFoundError(
                f"No environment file found for environment "
                f"'{environment}'. "
                f"Please create a .env file in the .env folder. "
                f"Example files available: {example_list}. "
                f"Copy one of the example files and rename it to match your "
                f"environment."
            )

    raise FileNotFoundError(
        f"No environment file found for environment "
        f"'{environment}' "
        f"and no .env folder with examples found. "
        f"Please create a .env file or set up environment variables."
    )
