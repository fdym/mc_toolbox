# -*- coding: utf-8 -*-
#
#  versions.py
#  
#  Copyright 2025 fdym
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
'''
Definition of a game folder.
'''
from collections import namedtuple
from os import listdir
from os.path import join, exists
from typing import List, Union
import json

from .exception import MinecraftVersionNotFound

__all__ = [
    'VersionJSONNamedTuple',
    'GameDir',
]

VersionJSONNamedTuple = namedtuple('VersionJSONNamespace', [
    'libraries_json', 'game_args_json', 'jvm_args_json', 'mainclass',
])

class GameDir:
    '''
    A game folder.

    :param game_dir: the path to this game folder
    '''
    def __init__(self, game_dir: str):
        self.game_dir = game_dir

    def get_versions(self) -> List[str]:
        try:
            return listdir(join(self.game_dir, 'versions'))
        except:
            return []

    def get_ids(self) -> List[str]:
        result = []
        for version in self.get_versions():
            with open(join(self.game_dir, 'versions', version, version + '.json'), encoding='utf-8') as f:
                result.append(json.loads(f.read())['id'])
        return result

    def get_version_json(self, version: str) -> VersionJSONNamedTuple[List[dict], Union[str, List[str]], List[Union[str, dict]], str]:
        '''
        Obtain some of the information in the version JSON of a specified Minecraft version.

        :param version: Minecraft version

        This function returns a `mc_toolbox.versions.VersionJSONNamedTuple`, which is a great way to fill in `mc_toolbox.launch.get_launch_script`.
        `mc_toolbox.exception.MinecraftVersionNotFound` is thrown when the version does not exist.
        '''
        if not exists(join(self.game_dir, 'versions', version)):
            raise MinecraftVersionNotFound(f'"{self.game_dir}" does not have a version named "{version}".')
        with open(join(self.game_dir, 'versions', version, version + '.json'), encoding='utf-8') as f:
            j: dict = json.loads(f.read())
        if j.get('inheritsFrom', None):
            if j['inheritsFrom'] not in self.get_ids():
                raise MinecraftVersionNotFound('"{game_dir}" does not have a version with ID "{id}".'.format(game_dir=self.game_dir, id=j['inheritsFrom']))
            with open(join(self.game_dir, 'versions', j['inheritsFrom'], j['inheritsFrom'] + '.json'), encoding='utf-8') as f2:
                other_json: dict = json.loads(f2.read())
            j['libraries'].extend(other_json['libraries'])
            if j.get('arguments', {}).get('game', None):
                j['arguments']['game'].extend(other_json['arguments']['game'])
            if j.get('arguments', {}).get('jvm', None):
                j['arguments']['jvm'].extend(other_json['arguments']['jvm'])
            other_json.update(j)
            j = other_json.copy()
        return VersionJSONNamedTuple(
            j['libraries'],
            j.get('minecraftArguments', None) if j.get('minecraftArguments', None) else j['arguments']['game'],
            j.get('arguments', {}).get('jvm', None),
            j['mainClass'],
        )
