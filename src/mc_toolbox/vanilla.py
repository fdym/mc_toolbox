from typing import Any, List, Dict
import re

from .utils import (
    get_true_mac_version,
    get_platform, Platform,
    get_architecture, Arch,   
)

class RuleChecker:
    def __init__(self, json: List[
            Dict[
                str, Dict[
                    str, str
                ]
            ]
        ]):
        self.allow = {}
        self.disallow = {}
        for i in json:
            if i['action'] == 'allow':
                self.allow = i.copy()
                self.allow.pop('action')
            else:
                self.disallow = i.copy()
                self.disallow.pop('action')

    def check(self, content, failure = '') -> Any:
        os_map = {
            'windows': Platform.WINDOWS,
            'macos': Platform.MACOS,
            'osx': Platform.MACOS,
            'linux': Platform.LINUX,
            'unknown': -1,
        }
        arch_map = {
            'x64': Arch.X64,
            'x86': Arch.X86,
            'arm64': Arch.ARM64,
            'arm': Arch.ARM_HF,
            'unknown': -1,
        }

        if self.allow:
            if self.allow.get('os', None):
                if self.allow['os'].get('name', None):
                    if get_platform() != os_map[self.allow['os']['name']]:
                        return failure
                if self.allow['os'].get('arch', None):
                    if get_architecture() != arch_map[self.allow['os']['arch']]:
                        return failure
                if self.allow['os'].get('version', None) and get_platform() == Platform.MACOS:
                    if re.findall(self.allow['os']['version'], get_true_mac_version()):
                        return failure

        if self.disallow:
            if self.disallow.get('os', None):
                if self.disallow['os'].get('name', None):
                    if get_platform() == os_map[self.disallow['os']['name']]:
                        return failure
                if self.disallow['os'].get('arch', None):
                    if get_architecture() == arch_map[self.disallow['os']['arch']]:
                        return failure
                if self.disallow['os'].get('version', None) and get_platform() == Platform.MACOS:
                    if not re.findall(self.disallow['os']['version'], get_true_mac_version()):
                        return failure

        return content
