from collections import namedtuple
from os import listdir
from os.path import join, exists
from typing import List, Union
import json

from .exception import MinecraftVersionNotFound

VersionJSONNamedTuple = namedtuple('VersionJSONNamespace', [
    'libraries_json', 'game_args_json', 'jvm_args_json', 'mainclass',
])

class GameDir:
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
        if not exists(join(self.game_dir, 'versions', version)):
            raise MinecraftVersionNotFound(f'"{self.game_dir}" does not have a version named "{version}".')
        with open(join(self.game_dir, 'versions', version, version + '.json'), encoding='utf-8') as f:
            j: dict = json.loads(f.read())
        if j.get('inheritsFrom', None):
            if j['inheritsFrom'] not in self.get_ids():
                raise MinecraftVersionNotFound('"{game_dir}" does not have a version with ID "{id}".'.format(game_dir=self.game_dir, id=j['inheritsFrom']))
            with open(join(self.game_dir, 'versions', j['inheritsFrom'], j['inheritsFrom'] + '.json'), encoding='utf-8') as f:
                other_json: dict = json.loads(f.read())
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
