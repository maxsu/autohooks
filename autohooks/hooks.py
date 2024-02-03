# SPDX-FileCopyrightText: 2019-2024 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import re
from pathlib import Path
from typing import Optional

from autohooks.settings import Mode
from autohooks.template import (
    PIPENV_MULTILINE_SHEBANG,
    PIPENV_SHEBANG,
    POETRY_MULTILINE_SHEBANG,
    POETRY_SHEBANG,
    PYTHON3_SHEBANG,
    TEMPLATE_VERSION,
    PreCommitTemplate,
)
from autohooks.utils import get_git_hook_directory_path

VERSION_PATTERN = re.compile("{\s*version\s*=\s*?(\d+)\s*}$", re.MULTILINE)


def default_pre_commit_hook_path():
    return get_git_hook_directory_path() / "pre-commit"


class PreCommitHook(Hook):
    pre_commit_hook_path = default_pre_commit_hook_path()

    def __init__(self, pre_commit_hook_path: Optional[Path] = None) -> None:
        if pre_commit_hook_path:
            self.pre_commit_hook_path = pre_commit_hook_path

    @cached_property
    def pre_commit_hook(self) -> str:
        return self.pre_commit_hook_path.read_text()

    @cached_property
    def pre_commit_hook_path(self):
        return default_pre_commit_hook_path()

    def exists(self) -> bool:
        return self.pre_commit_hook_path.exists()

    def is_autohooks_pre_commit_hook(self) -> bool:
        lines = self.pre_commit_hook.split("\n")
        # seems to be false-positive ...
        return len(lines) > 5 and "autohooks.precommit" in self.pre_commit_hook

    def is_current_autohooks_pre_commit_hook(self) -> bool:
        return self.read_version() == TEMPLATE_VERSION

    def read_mode(self) -> Mode:
        lines = self.pre_commit_hook.split("\n")
        if not lines or not lines[0]:
            return Mode.UNDEFINED

        shebang = lines[0][2:]

        if shebang == PYTHON3_SHEBANG:
            return Mode.PYTHONPATH
        if shebang.startswith(POETRY_SHEBANG):
            return Mode.POETRY
        if shebang == PIPENV_SHEBANG:
            return Mode.PIPENV

        multiline_shebang = "\n".join([shebang] + lines[1:5])

        if multiline_shebang == POETRY_MULTILINE_SHEBANG:
            return Mode.POETRY_MULTILINE
        if multiline_shebang == PIPENV_MULTILINE_SHEBANG:
            return Mode.PIPENV_MULTILINE
        return Mode.UNKNOWN

    def read_version(self) -> int:
        matches = VERSION_PATTERN.search(self.pre_commit_hook)
        if not matches:
            return -1
        return int(matches.group(1))

    def write(self, *, mode: Mode) -> None:
        template = PreCommitTemplate()
        pre_commit_hook = template.render(mode=mode)

        self.pre_commit_hook_path.write_text(pre_commit_hook)
        self.pre_commit_hook_path.chmod(0o775)

        del self.pre_commit_hook  # reset cached_property

    def __str__(self) -> str:
        return str(self.pre_commit_hook_path)
