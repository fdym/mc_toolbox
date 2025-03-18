# -*- coding: utf-8 -*-
#
#  source.py
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
Declare multiple sources.
'''
from collections import namedtuple
from html.parser import HTMLParser
from typing import List, Tuple, Any, Optional
from xml.etree import ElementTree as ET
import json

import requests

from .cache import CacheManager
from .exception import (
    MinecraftVersionNotFound,
    # LiteLoaderVersionNotFound,
    OptiFineVersionNotFound,
)

__all__ = [
    'cache',
    'VanillaLatestNamedTuple',
    'VanillaVersionsNamedTuple',
    'VanillaNamedTuple',
    'ForgeNamedTuple',
    'FabricNamedTuple',
    'QuiltNamedTuple',
    'NeoforgeNamedTuple',
    'OptiFineNamedTuple',
    'Source',
    'OfficialSource',
    'BMCLAPISource',
]

VanillaLatestNamedTuple = namedtuple('VanillaLatestNamedTuple', ['release', 'snapshot'])
VanillaVersionsNamedTuple = namedtuple('VanillaVersionsNamedTuple', ['name', 'type', 'url'])
VanillaNamedTuple = namedtuple('VanillaNamedTuple', ['latest', 'versions'])
ForgeNamedTuple = namedtuple('ForgeNamedTuple', ['mcversion', 'name'])
FabricNamedTuple = namedtuple('FabricNamedTuple', ['name', 'is_stable'])
QuiltNamedTuple = namedtuple('QuiltNamedTuple', ['name', 'is_stable'])
NeoforgeNamedTuple = namedtuple('NeoforgeNamed', ['name', 'url'])
OptiFineNamedTuple = namedtuple('OptiFineNamedTuple', ['mcversion', 'name', 'url', 'forge', 'is_pre'])

cache = CacheManager(max_size=50)

class Source:
    source_name = ''

    # vanilla_base_url = ''

    def get_vanilla_list(self) -> VanillaNamedTuple[VanillaLatestNamedTuple[str, str], List[VanillaVersionsNamedTuple[str, str, str]]]:
        '''
        Get a list of vanilla Minecraft.
        Return a VanillaNamedTuple with VanillaLatestNamedTuple 
        and a list containing VanillaVersions NamedTuple.
        '''

    def get_vanilla_json_url(self, mcversion: str) -> str:
        '''
        Get the URL of the client.json for vanilla Minecraft.

        :param mcversion: minecraft version
        '''

    def get_vanilla_client_url(self, mcversion: str) -> str:
        '''
        Get the URL of the client for vanilla Minecraft.

        :param mcversion: minecraft version
        '''

    forge_base_url = ''

    is_after_1_5_1 = staticmethod(lambda version: not (int(version.split('.')[1]) < 5 or version.endswith(('1.5', '1.5.1'))))

    def get_forge_list(self, mcversion: str) -> List[ForgeNamedTuple[str, str]]:
        '''
        Get the list of Forge.
        '''

    def get_forge_url(self, mcversion: str, forge_version: str) -> str:
        '''
        Get the URL of Forge.

        :param mcversion: minecraft version
        :param forge_version: forge version
        '''

    fabric_base_url = ''
    fabric_meta_base_url = ''

    def get_fabric_list(self) -> List[FabricNamedTuple[str, bool]]:
        '''
        Get the list of Fabric.
        '''

    def get_fabric_supported_vanilla_version_list(self) -> List[FabricNamedTuple[str, bool]]:
        '''
        Get a list of Minecraft supported by Fabric.
        '''

    def get_fabric_installer_list(self) -> List[FabricNamedTuple[str, bool]]:
        '''
        Get the list of Fabric Installer.
        '''

    def get_fabric_url(self, installer_version: str) -> str:
        '''
        Get the URL of Fabric Installer.

        :param installer_version: installer version
        '''

    quilt_base_url = ''
    quilt_meta_base_url = ''

    def get_quilt_list(self) -> List[QuiltNamedTuple[str, bool]]:
        '''
        Get the list of Quilt.
        '''

    def get_quilt_supported_vanilla_version_list(self) -> List[QuiltNamedTuple[str, bool]]:
        '''
        Get a list of Minecraft supported by Quilt.
        '''

    def get_quilt_installer_list(self) -> List[QuiltNamedTuple[str, bool]]:
        '''
        Get the list of Quilt Installer.
        '''

    def get_quilt_url(self, installer_version: str) -> str:
        '''
        Get the URL of Quilt Installer.

        :param installer_version: installer version
        '''

    # def get_liteloader_list(self) -> List[str]:
    #     pass

    # def get_liteloader_url(self, mcversion: str) -> str:
    #     pass

    neoforge_base_url = ''

    def get_neoforge_list(self) -> List[NeoforgeNamedTuple[str, str]]:
        '''
        Get the list of Neoforge.
        '''

    def get_neoforge_url(self, mcversion: str, neoforge_version: str) -> str:
        '''
        Get the URL of NeoForge.

        :param mcversion: minecraft version
        :param neoforge_version: neoforge version
        '''

    optifine_base_url = ''

    def get_optifine_list(self) -> List[OptiFineNamedTuple[str, str, str, Optional[str], bool]]:
        '''
        Get the list of OptiFine.
        '''

    def get_optifine_url(self, mcversion: str, name: str) -> str:
        '''
        Get the URL of OptiFine.

        :param mcversion: minecraft version
        :param name: optifine version name
        '''

class OfficialSource(Source):
    source_name = 'official'
    cache = CacheManager(max_size=10)

    @cache.cache('official_vanilla_list')
    def get_vanilla_list(self) -> VanillaNamedTuple[VanillaLatestNamedTuple[str, str], List[VanillaVersionsNamedTuple[str, str, str]]]:
        response = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest.json')
        manifest = json.loads(response.text)
        result_latest = VanillaLatestNamedTuple(manifest['latest']['release'], manifest['latest']['snapshot'])
        result_versions = []
        for i in manifest['versions']:
            result_versions.append(VanillaVersionsNamedTuple(i['id'], i['type'], i['url']))
        return VanillaNamedTuple(result_latest, result_versions)

    def get_vanilla_json_url(self, mcversion: str) -> str:
        vanilla_list = self.get_vanilla_list()
        url = ''
        for version in vanilla_list.versions:
            if version.name == mcversion:
                url = version.url
                break
        if not url:
            raise MinecraftVersionNotFound(f'Minecraft does not have a version named "{mcversion}".')
        return url

    def get_vanilla_client_url(self, mcversion: str) -> str:
        url = self.get_vanilla_json_url(mcversion)
        response = requests.get(url)
        return json.loads(response.text)['downloads']['client']['url']

    forge_base_url = 'https://maven.minecraftforge.net/'

    @cache.cache('official_forge_list')
    def get_forge_list(self) -> List[ForgeNamedTuple[str, str]]:
        xml = requests.get(f'{self.forge_base_url}net/minecraftforge/forge/maven-metadata.xml').text
        root = ET.fromstring(xml)
        result = []
        for version in root.find('versioning').find('versions'):
            splited_str = version.text.split('-', 1)
            if self.is_after_1_5_1(splited_str[0]):
                result.append(ForgeNamedTuple(splited_str[0], splited_str[1]))
        return result

    def get_forge_url(self, mcversion: str, forge_version: str) -> str:
        version = f'{mcversion}-{forge_version}'
        return f'{self.forge_base_url}net/minecraftforge/forge/{version}/forge-{version}-installer.jar'

    fabric_base_url = 'https://maven.fabricmc.net/'
    fabric_meta_base_url = 'https://meta.fabricmc.net/v2/'

    @cache.cache('official_fabric_list')
    def get_fabric_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/loader').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    @cache.cache('official_fabric_supported_vanilla_version_list')
    def get_fabric_supported_vanilla_version_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/game').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    @cache.cache('official_installer_list')
    def get_fabric_installer_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/installer').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    get_fabric_url = lambda self, installer_version: f'{self.fabric_base_url}net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar'

    quilt_base_url = 'https://maven.quiltmc.org/repository/release/'
    quilt_meta_base_url = 'https://meta.quiltmc.org/v3/'

    @cache.cache('official_quilt_list')
    def get_quilt_list(self) -> List[QuiltNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.quilt_meta_base_url}versions/loader').text)
        result = []
        for version in versions:
            result.append(QuiltNamedTuple(version['version'], 'beta' not in version['version']))
        return result

    @cache.cache('official_quilt_supported_vanilla_version_list')
    def get_quilt_supported_vanilla_version_list(self) -> List[QuiltNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.quilt_meta_base_url}versions/game').text)
        result = []
        for version in versions:
            result.append(QuiltNamedTuple(version['version'], version['stable']))
        return result

    @cache.cache('official_quilt_installer_list')
    def get_quilt_installer_list(self) -> List[str]:
        versions = json.loads(requests.get(f'{self.quilt_meta_base_url}versions/installer').text)
        result = []
        for version in versions:
            result.append(version['version'])
        return result

    get_quilt_url = lambda self, installer_version: f'{self.quilt_base_url}org/quiltmc/quilt-installer/{installer_version}/quilt-installer-{installer_version}.jar'

    # get_liteloader_list = lambda self: [
    #     '1.12.2',
    #     '1.12.1',
    #     '1.12',
    #     '1.11.2',
    #     '1.11',
    #     '1.10.2',
    #     '1.10',
    #     '1.9.4',
    #     '1.9',
    #     '1.8.9',
    #     '1.8',
    #     '1.7.10',
    # ]

    # def get_liteloader_url(self, mcversion: str) -> str:
    #     if mcversion not in self.get_liteloader_list():
    #         raise LiteLoaderVersionNotFound(f'LiteLoader does not have a version named "{mcversion}".')
    #     version_to_url = {
    #         '1.12.2': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.12.2/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.12.2-00-SNAPSHOT.jar',
    #         '1.12.1': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.12.1/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.12.1-00-SNAPSHOT.jar',
    #         '1.12': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.12/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.12-00-SNAPSHOT.jar',
    #         '1.11.2': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.11.2/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.11.2-00-SNAPSHOT.jar',
    #         '1.11': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.11/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.11-00-SNAPSHOT.jar',
    #         '1.10.2': 'http://dl.liteloader.com/redist/1.10.2/liteloader-installer-1.10.2-00.jar',
    #         '1.10': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.10/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.10-00-SNAPSHOT.jar',
    #         '1.9.4': 'http://dl.liteloader.com/redist/1.9.4/liteloader-installer-1.9.4-00.jar',
    #         '1.9': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.9/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.9.0-00-SNAPSHOT.jar',
    #         '1.8.9': 'http://jenkins.liteloader.com/job/LiteLoaderInstaller%201.8.9/lastSuccessfulBuild/artifact/build/libs/liteloader-installer-1.8.9-00-SNAPSHOT.jar',
    #         '1.8': 'http://dl.liteloader.com/redist/1.8.0/liteloader-installer-1.8.0-00.jar',
    #         '1.7.10': 'http://dl.liteloader.com/redist/1.7.10/liteloader-installer-1.7.10-04.jar',
    #     }
    #     return version_to_url[mcversion]

    neoforge_base_url = 'https://maven.neoforged.net/releases/'

    @cache.cache('official_neoforge_list')
    def get_neoforge_list(self) -> List[NeoforgeNamedTuple[str, str]]:
        xml_1_20_1 = requests.get(f'{self.neoforge_base_url}net/neoforged/forge/maven-metadata.xml').text
        xml = requests.get(f'{self.neoforge_base_url}net/neoforged/neoforge/maven-metadata.xml').text
        root_1_20_1 = ET.fromstring(xml_1_20_1)
        root = ET.fromstring(xml)
        result = []
        
        for version in root_1_20_1.find('versioning').find('versions'):
            if '1.20.1-' not in version.text:
                name = f'1.20.1-{version.text}'
            else:
                name = version.text
            url = f'{self.neoforge_base_url}net/neoforged/forge/{name}/forge-{name}-installer.jar'
            result.append(NeoforgeNamedTuple(name, url))

        for version in root.find('versioning').find('versions'):
            name = version.text
            url = f'{self.neoforge_base_url}net/neoforged/neoforge/{name}/neoforge-{name}-installer.jar'
            result.append(NeoforgeNamedTuple(name, url))

        return result

    def get_neoforge_url(self, mcversion: str, neoforge_version: str) -> str:
        if mcversion == '1.20.1':
            return f'{self.neoforge_base_url}net/neoforged/forge/{neoforge_version}/forge-{neoforge_version}-installer.jar'
        else:
            return f'{self.neoforge_base_url}net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar'

    class _getOptifineUrl(HTMLParser):
        def __init__(self, *, convert_charrefs=True):
            self.convert_charrefs = convert_charrefs
            self.url = ''
            self.reset()

        def handle_starttag(self, tag: str, attrs: List[Tuple[str, Any]]):
            attrs_dict = dict(attrs)
            if attrs_dict.get('onclick', '') == 'onDownload()' and tag == 'a':
                self.url = attrs_dict['href']

    optifine_base_url = 'https://optifine.net/'

    @cache.cache('official_optifine_list')
    def get_optifine_list(self) -> List[OptiFineNamedTuple[str, str, str, Optional[str], bool]]:
        response = requests.get('https://bmclapi2.bangbang93.com/optifine/versionList')
        manifest = json.loads(response.text)
        result = []
        for version in manifest:
            version: dict
            mcversion = version['mcversion']
            name = '{_type}_{patch}'.format(_type=version['type'], patch=version['patch'])
            url = '{base_url}adloadx?f={filename}'.format(base_url=self.optifine_base_url, filename=version['filename'])
            _forge = version.get('forge', 'Forge N/A')
            forge = None if _forge == 'Forge N/A' else _forge.lstrip('Forge ')
            is_pre = 'pre' in version['patch']
            result.append(OptiFineNamedTuple(mcversion, name, url, forge, is_pre))
        return result

    def get_optifine_url(self, mcversion: str, name: str) -> str:
        optifine_list = self.get_optifine_list()
        url = ''
        for version in optifine_list:
            if version.mcversion == mcversion and version.name == name:
                url = version.url
                break
        if not url:
            raise OptiFineVersionNotFound(f'OptiFine does not have a version named "{mcversion}_{name}".')
        html = requests.get(url).text
        parser = self._getOptifineUrl()
        parser.feed(html)
        return f'{self.optifine_base_url}{parser.url}'

    get_vanilla_list.__doc__ = Source.get_vanilla_list.__doc__
    get_vanilla_json_url.__doc__ = Source.get_vanilla_json_url.__doc__
    get_vanilla_client_url.__doc__ = Source.get_vanilla_client_url.__doc__
    get_forge_list.__doc__ = Source.get_forge_list.__doc__
    get_forge_url.__doc__ = Source.get_forge_url.__doc__
    get_fabric_list.__doc__ = Source.get_fabric_list.__doc__
    get_fabric_supported_vanilla_version_list.__doc__ = Source.get_fabric_supported_vanilla_version_list.__doc__
    get_fabric_installer_list.__doc__ = Source.get_fabric_installer_list.__doc__
    get_fabric_url.__doc__ = Source.get_fabric_url.__doc__
    get_quilt_list.__doc__ = Source.get_quilt_list.__doc__
    get_quilt_supported_vanilla_version_list.__doc__ = Source.get_quilt_supported_vanilla_version_list.__doc__
    get_quilt_installer_list.__doc__ = Source.get_quilt_installer_list.__doc__
    get_quilt_url.__doc__ = Source.get_quilt_url.__doc__
    get_neoforge_list.__doc__ = Source.get_neoforge_list.__doc__
    get_neoforge_url.__doc__ = Source.get_neoforge_url.__doc__
    get_optifine_list.__doc__ = Source.get_optifine_list.__doc__
    get_optifine_url.__doc__ = Source.get_optifine_url.__doc__

class BMCLAPISource(Source):
    source_name = 'bmclapi'
    cache = CacheManager(max_size=10)

    @cache.cache('bmclapi_vanilla_list')
    def get_vanilla_list(self) -> VanillaNamedTuple[VanillaLatestNamedTuple[str, str], List[VanillaVersionsNamedTuple[str, str, str]]]:
        response = requests.get('https://bmclapi2.bangbang93.com/mc/game/version_manifest.json')
        manifest = json.loads(response.text)
        result_latest = VanillaLatestNamedTuple(manifest['latest']['release'], manifest['latest']['snapshot'])
        result_versions = []
        for i in manifest['versions']:
            result_versions.append(VanillaVersionsNamedTuple(i['id'], i['type'], i['url']))
        return VanillaNamedTuple(result_latest, result_versions)

    def get_vanilla_json_url(self, mcversion: str) -> str:
        return f'https://bmclapi2.bangbang93.com/version/{mcversion}/json'

    def get_vanilla_client_url(self, mcversion: str) -> str:
        return f'https://bmclapi2.bangbang93.com/version/{mcversion}/client'

    forge_base_url = 'https://bmclapi2.bangbang93.com/maven/'

    def get_forge_list(self) -> List[ForgeNamedTuple[str, str]]:
        return OfficialSource().get_forge_list()

    def get_forge_url(self, mcversion: str, forge_version: str) -> str:
        version = f'{mcversion}-{forge_version}'
        return f'{self.forge_base_url}net/minecraftforge/forge/{version}/forge-{version}-installer.jar'

    fabric_base_url = 'https://bmclapi2.bangbang93.com/maven/'
    fabric_meta_base_url = 'https://bmclapi2.bangbang93.com/fabric-meta/v2/'

    @cache.cache('bmclapi_fabric_list')
    def get_fabric_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/loader').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    @cache.cache('bmclapi_fabric_supported_vanilla_version_list')
    def get_fabric_supported_vanilla_version_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/game').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    @cache.cache('bmclapi_installer_list')
    def get_fabric_installer_list(self) -> List[FabricNamedTuple[str, bool]]:
        versions = json.loads(requests.get(f'{self.fabric_meta_base_url}versions/installer').text)
        result = []
        for version in versions:
            result.append(FabricNamedTuple(version['version'], version['stable']))
        return result

    get_fabric_url = lambda self, installer_version: f'{self.fabric_base_url}net/fabricmc/fabric-installer/{installer_version}/fabric-installer-{installer_version}.jar'

    # BMCLAPI: Due to issues with the upstream API, it is temporarily unavailable.
    # quilt_base_url = 'https://maven.quiltmc.org/repository/release/'
    # quilt_meta_base_url = 'https://meta.quiltmc.org/v3/'

    def get_quilt_list(self) -> List[QuiltNamedTuple[str, bool]]:
        return OfficialSource().get_quilt_list()

    def get_quilt_supported_vanilla_version_list(self) -> List[QuiltNamedTuple[str, bool]]:
        return OfficialSource().get_quilt_supported_vanilla_version_list()

    def get_quilt_installer_list(self) -> List[str]:
        return OfficialSource().get_quilt_installer_list()

    get_quilt_url = lambda self, installer_version: f'{self.quilt_base_url}org/quiltmc/quilt-installer/{installer_version}/quilt-installer-{installer_version}.jar'

    neoforge_base_url = 'https://bmclapi2.bangbang93.com/maven/'

    @cache.cache('bmclapi_neoforge_list')
    def get_neoforge_list(self) -> List[NeoforgeNamedTuple[str, str]]:
        xml_1_20_1 = requests.get(f'{self.neoforge_base_url}net/neoforged/forge/maven-metadata.xml').text
        xml = requests.get(f'{self.neoforge_base_url}net/neoforged/neoforge/maven-metadata.xml').text
        root_1_20_1 = ET.fromstring(xml_1_20_1)
        root = ET.fromstring(xml)
        result = []
        
        for version in root_1_20_1.find('versioning').find('versions'):
            if '1.20.1-' not in version.text:
                name = f'1.20.1-{version.text}'
            else:
                name = version.text
            url = f'{self.neoforge_base_url}net/neoforged/forge/{name}/forge-{name}-installer.jar'
            result.append(NeoforgeNamedTuple(name, url))

        for version in root.find('versioning').find('versions'):
            name = version.text
            url = f'{self.neoforge_base_url}net/neoforged/neoforge/{name}/neoforge-{name}-installer.jar'
            result.append(NeoforgeNamedTuple(name, url))

        return result

    def get_neoforge_url(self, mcversion: str, neoforge_version: str) -> str:
        if mcversion == '1.20.1':
            return f'{self.neoforge_base_url}net/neoforged/forge/{neoforge_version}/forge-{neoforge_version}-installer.jar'
        else:
            return f'{self.neoforge_base_url}net/neoforged/neoforge/{neoforge_version}/neoforge-{neoforge_version}-installer.jar'

    optifine_base_url = 'https://bmclapi2.bangbang93.com/optifine/'

    @cache.cache('bmclapi_optifine_list')
    def get_optifine_list(self) -> List[OptiFineNamedTuple[str, str, str, Optional[str], bool]]:
        response = requests.get(f'{self.optifine_base_url}versionList')
        manifest = json.loads(response.text)
        result = []
        for version in manifest:
            version: dict
            mcversion = version['mcversion']
            name = '{_type}_{patch}'.format(_type=version['type'], patch=version['patch'])
            # url = '{base_url}adloadx?f={filename}'.format(base_url=self.optifine_base_url, filename=version['filename'])
            url = '{base_url}{mcversion}/{_type}/{patch}'.format(
                base_url=self.optifine_base_url,
                mcversion=mcversion,
                _type=version['type'],
                patch=version['patch']
            )
            _forge = version.get('forge', 'Forge N/A')
            forge = None if _forge == 'Forge N/A' else _forge.lstrip('Forge ')
            is_pre = 'pre' in version['patch']
            result.append(OptiFineNamedTuple(mcversion, name, url, forge, is_pre))
        return result

    def get_optifine_url(self, mcversion: str, name: str) -> str:
        optifine_list = self.get_optifine_list()
        url = ''
        for version in optifine_list:
            if version.mcversion == mcversion and version.name == name:
                url = version.url
                break
        if not url:
            raise OptiFineVersionNotFound(f'OptiFine does not have a version named "{mcversion}_{name}".')
        return url

    get_vanilla_list.__doc__ = Source.get_vanilla_list.__doc__
    get_vanilla_json_url.__doc__ = Source.get_vanilla_json_url.__doc__
    get_vanilla_client_url.__doc__ = Source.get_vanilla_client_url.__doc__
    get_forge_list.__doc__ = Source.get_forge_list.__doc__
    get_forge_url.__doc__ = Source.get_forge_url.__doc__
    get_fabric_list.__doc__ = Source.get_fabric_list.__doc__
    get_fabric_supported_vanilla_version_list.__doc__ = Source.get_fabric_supported_vanilla_version_list.__doc__
    get_fabric_installer_list.__doc__ = Source.get_fabric_installer_list.__doc__
    get_fabric_url.__doc__ = Source.get_fabric_url.__doc__
    get_quilt_list.__doc__ = Source.get_quilt_list.__doc__
    get_quilt_supported_vanilla_version_list.__doc__ = Source.get_quilt_supported_vanilla_version_list.__doc__
    get_quilt_installer_list.__doc__ = Source.get_quilt_installer_list.__doc__
    get_quilt_url.__doc__ = Source.get_quilt_url.__doc__
    get_neoforge_list.__doc__ = Source.get_neoforge_list.__doc__
    get_neoforge_url.__doc__ = Source.get_neoforge_url.__doc__
    get_optifine_list.__doc__ = Source.get_optifine_list.__doc__
    get_optifine_url.__doc__ = Source.get_optifine_url.__doc__
