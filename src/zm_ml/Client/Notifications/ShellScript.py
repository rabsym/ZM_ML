import logging
import subprocess
import time
from pathlib import Path
from typing import List, NoReturn, Union, Optional, Tuple, Dict

import numpy as np
import requests
import urllib3.exceptions
from pydantic import BaseModel, Field, AnyUrl

from ..main import get_global_config
from ...Shared.configs import GlobalConfig
from ..Log import CLIENT_LOGGER_NAME
from ..Notifications import CoolDownBase

logger = logging.getLogger(CLIENT_LOGGER_NAME)
g: Optional[GlobalConfig] = None
LP: str = "shell_script:"


class ShellScriptNotification(CoolDownBase):
    _data_dir_str: str = "push/shell_script"

    def __init__(self):
        global g

        g = get_global_config()
        self.config = g.config.notifications.shell_script
        self.data_dir = g.config.system.variable_data_path / self._data_dir_str
        super().__init__()

    def run(self, script_args: Optional[List[str]] = None):
        lp: str = f"{LP}:run:"
        script_path = Path(self.config.script)
        if self.config.enabled:
            if not script_path.is_file():
                raise FileNotFoundError(f"Script file '{script_path.as_posix()}' not found/is not a valid file")
            if not self.config.I_AM_AWARE_OF_THE_DANGER_OF_RUNNING_SHELL_SCRIPTS != "YeS i aM awaRe!":
                raise ValueError("You MUST set I_AM_AWARE_OF_THE_DANGER_OF_RUNNING_SHELL_SCRIPTS to: YeS i aM awaRe!")

            if not script_path.is_absolute():
                script_path = script_path.expanduser().resolve()
            cmd_array = [script_path.as_posix()]
            if script_args:
                logger.debug(f"{lp} Adding script args: {script_args}")
                cmd_array.extend(script_args)
            try:
                x = subprocess.run(cmd_array, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"{lp} Shell script failed with exit code {e.returncode}")
                logger.error(f"{lp} STDOUT: {e.stdout}")
                logger.error(f"{lp} STDERR: {e.stderr}")
                raise e
            logger.debug(f"{lp} STDOUT->{x.stdout}")
            if x.stderr:
                logger.error(f"{lp} STDERR-> {x.stderr}")
        else:
            logger.debug(f"Shell script notification disabled, skipping")

    def send(self, script_args: Optional[List[str]] = None):
        return self.run(script_args=script_args)
