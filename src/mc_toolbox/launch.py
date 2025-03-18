# -*- coding: utf-8 -*-
#
#  launch.py
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
This library provides functions for concatenating Minecraft startup parameters.

Note: More than half of the content in natives.json is contributed by Glavo.
The purpose of natives.json is to provide more architecture and more OS support for Minecraft.
natives.json was originally created by Glavo and HMCL project author Jackhuang for the HMCL project.
So please support the Jackhuang, Glavo, and HMCL projects!
'''
from os.path import join, dirname
from string import Template
from typing import Any, List, Union, Tuple, Literal, Optional
import json
import re

from .cache import CacheManager
from .download import HttpProxy, SocksProxy, NoProxy
from .java import Java
from .utils import (
    get_system_version,
    get_platform, Platform,
    get_architecture, Arch,
    VANILLA,
)

cache = CacheManager(max_size=5, ttl=600)

@cache.cache('natives_json')
def get_natives_json() -> dict:
    with open(join(dirname(__file__), 'natives.json'), encoding='utf-8') as f:
        return json.loads(f.read())

def rule_check(json) -> bool:
    '''
    Check whether the current running environment meets the rules of some content in client.json (such as whether it is a Mac OS system).
    For more information on the rules, please refer to https://minecraft.wiki/client.json
    
    :param json: rules (as you can see, rules are in JSON format)
    '''
    allow = {}
    disallow = {}
    for i in json:
        if i['action'] == 'allow':
            allow = i.copy()
            allow.pop('action')
        else:
            disallow = i.copy()
            disallow.pop('action')

        os_map = {
            'windows': Platform.WINDOWS,
            'macos': Platform.MACOS,
            'osx': Platform.MACOS,
            'linux': Platform.LINUX,
            'unknown': get_platform(), # any
        }
        arch_map = {
            'x64': Arch.X64,
            'x86': Arch.X86,
            'arm64': Arch.ARM64,
            'arm': Arch.ARM_HF,
            'unknown': get_architecture(), # any 
        }

    if allow:
        if allow.get('os', None):
            if allow['os'].get('name', None):
                if get_platform() != os_map[allow['os']['name']]:
                    return False
            if allow['os'].get('arch', None):
                if get_architecture() != arch_map[allow['os']['arch']]:
                    return False
            if allow['os'].get('version', None):
                if (
                    get_platform() != Platform.LINUX
                    and not re.findall(disallow['os']['version'], get_system_version())
                ):
                    return False
                
        return True

    if disallow:
        # rules (example) : Windows x64 ^10\.
        # system (example) : Windows x64 6.1 
        _disallow_os = False
        _disallow_arch = False
        _disallow_version = False
        if disallow.get('os', None):
            if disallow['os'].get('name', None):
                if get_platform() != os_map[disallow['os']['name']]:
                    _disallow_os = True # do nothing (in this example)
            if disallow['os'].get('arch', None):
                if get_architecture() != arch_map[disallow['os']['arch']]:
                    _disallow_arch = True # do nothing (in this example)
            if disallow['os'].get('version', None) and get_platform():
                if (
                    get_platform() != Platform.LINUX
                    and not re.findall(disallow['os']['version'], get_system_version())
                ):
                    _disallow_version = True # _disallow_version = True (in this xample) 

        return _disallow_os or _disallow_arch or _disallow_version # return True (in this example)

def get_classpath(libraries_json: List[dict], libraries_dir: str, client_jar: str):
    '''
    Get the classpath.

    :param libraries_json: record a list of game dependency libraries, which can be found in the "libraries" key of client.json
    :param libraries_dir: the directory where the game dependency library is located, such as/home/computer/.minecraft/libraries/
    :param client_jar: the path of the game's main file
    '''
    with open(join(dirname(__file__), 'natives.json'), encoding='utf-8') as f:
        _natives_json: dict = get_natives_json()
    classpath_list = []
    natives_json = {}

    if get_platform() == Platform.LINUX:
        if get_architecture() == Arch.ARM64:
            natives_json = _natives_json['linux-arm64']
        elif get_architecture() == Arch.ARM_HF:
            natives_json = _natives_json['linux-arm32']
    elif get_platform() == Platform.WINDOWS:
        if get_architecture() == Arch.X64:
            natives_json = _natives_json['windows-x86_64']
        elif get_architecture() == Arch.X86:
            natives_json = _natives_json['windows-x86']
        elif get_architecture() == Arch.ARM64:
            natives_json = _natives_json['windows-arm64']
    elif get_platform() == Platform.MACOS:
        if get_architecture() == Arch.ARM64:
            natives_json = _natives_json['osx-arm64']
        
    for library_json in libraries_json:
        natives_filter = list(filter(lambda k: (
            library_json.get('downloads', None)
            and library_json['downloads'].get('classifiers', None)
            and (library_json['name'] + ':natives') in k
        ), natives_json.keys()))
        if natives_filter:
            if natives_json[natives_filter[0]]:
                libraries_json.append(natives_json[natives_filter[0]])
                library_json['downloads'].pop('classifiers', None)
                library_json.pop('extract', None)
                library_json.pop('natives', None)
            else: # null
                continue
        if natives_json.get(library_json['name'], None):
            library_json = natives_json[library_json['name']]
        if (library_json.get('url', None) # fabric
            or (
                library_json.get('downloads', None) 
                and library_json['downloads'].get('artifact', None) # vanilla
            ) or not (
                library_json.get('downloads', None) 
                and library_json['downloads'].get('classifiers', None) # forge
            )
        ):
            if ((not library_json.get('rules', None) )
                or (
                    library_json.get('rules', None) 
                    and rule_check(library_json['rules'])
                )
            ):
                _path = [libraries_dir]
                _path.extend(library_json['name'].split(':')[0].split('.'))
                _path.append(library_json['name'].split(':')[1])
                _path.append(library_json['name'].split(':')[2])
                _path_extra = None
                # such as net.fdymcreep.example:example:1.0:natives
                if len(library_json['name'].split(':')) >= 4:
                    _path_extra = library_json['name'].split(':')[3]
                _path.append(library_json['name'].split(':')[1]
                    + '-'
                    + library_json['name'].split(':')[2]
                    + (f'-{_path_extra}' if _path_extra else '')
                    + '.jar'
                )
                classpath_list.append(join(_path[0], *_path[1:]))

    classpath_list.append(client_jar)
    return (';' if get_platform() == Platform.WINDOWS else ':').join(classpath_list)

class LaunchOption:
    '''
    A class used to represent the vast majority of startup parameters.

    :param username: username
    :param token: user token, if using offline login, should be left blank
    :param uuid: uuid
    :param user_type: user login type, which can be MSA or legacy
    :param version_name: version name
    :param game_dir: the path to the game directory (such as/home/computer/.minecraft/)
    :param assets_index_name: resource index file name
    :param assets_dir: the path of the resource directory (such as/home/computer/.minecraft/assets/)
    :param libraries_dir: the path to the game dependency library directory (such as/home/computer/.minecraft/libraries/)
    :param client_jar: the path of the game's main file
    :param version_type: version type, displayed in the bottom right corner of the game interface, defaults to Minecraft
    :param profile_name: default to Minecraft
    :param demo: boolean value indicating whether to launch the demo version (default is False)
    :param screen_type: this parameter can be a tuple representing the window size, consisting of strings "fullscreen" and None (indicating do not manual setting). The default value is a tuple containing 854 and 480
    :param server: The server that will be accessed after starting the game, such as 142.8.5.7:4285
    :param quickplay_multiplayer: Specify the server to connect to when using QuickPlay Multiplayer, such as 142.8.5.7:4285
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    '''
    def __init__(self,
            username: str, token: str, uuid: str, user_type: Literal['msa', 'legacy'],
            version_name: str,
            game_dir: str, assets_index_name: str, assets_dir: str, libraries_dir: str, client_jar: str,

            version_type: str = VANILLA, profile_name = 'Minecraft',
            demo: bool = False, 
            screen_type: Union[Tuple[int, int], Literal['fullscreen'], None] = (854, 480),
            server: Optional[str] = None, quickplay_multiplayer: Optional[str] = None,
            proxies: Union[HttpProxy, SocksProxy, NoProxy] = NoProxy(),
    ):
        self.username = username
        self.token = token
        self.uuid = uuid
        self.user_type = user_type
        self.version_name = version_name
        self.game_dir = game_dir
        self.assets_index_name = assets_index_name
        self.assets_dir = assets_dir
        self.libraries_dir = libraries_dir
        self.client_jar = client_jar
        self.version_type = version_type
        self.profile_name = profile_name
        self.demo = demo
        self.screen_type = screen_type
        self.server = server
        self.quickplay_multiplayer = quickplay_multiplayer
        self.proxies = proxies

def get_game_args(option: LaunchOption, args_json: Union[str, List[str]]) -> str:
    '''
    Get game parameters.

    :param option: a LaunchOption
    :param args_json: a string or list describing the format of game parameters

    Regarding args_json: In Minecraft 1.12.2 and earlier versions, args_json should be passed the value represented by the minecraftArguments key in client.json.
    After Minecraft version 1.12.2, args_json should be passed the value of the arguments.game key in client.json.
    '''
    result = ''
    if isinstance(args_json, list):
        result_list = []
        for i in args_json:
            if isinstance(i, str):
                result_list.append(i)
        result = ' '.join(result_list)
    else:
        result = args_json

    if option.demo:
        result += ' --demo'
    if isinstance(option.screen_type, tuple):
        result += f' --width {option.screen_type[0]} --height {option.screen_type[1]}'
    elif option.screen_type != None:
        result += f' --fullscreen'
    if option.server != None:
        server_t = option.server.split(':')
        result += f' --server {server_t[0]}'
        result += f' --port {server_t[1] if len(server_t) >= 2 else 25565}'
    if option.quickplay_multiplayer != None:
        quickplay_multiplayer_t = option.quickplay_multiplayer.split(':')
        result += f' --quickPlayMultiplayer {quickplay_multiplayer_t[0]}:{quickplay_multiplayer_t[1] if len(quickplay_multiplayer_t) >= 2 else 25565}'
    if isinstance(option.proxies, SocksProxy):
        proxy_t = option.proxies.netloc.split(':')
        result += f' --proxyHost {proxy_t[0]}'
        result += f' --proxyPort {proxy_t[1]}'
        if option.proxies.username != None:
            result += f' --proxyUser {option.proxies.username}'
            result += f' --proxyPass {option.proxies.password}'
    mapping = {
        'auth_player_name': option.username,
        'auth_session': option.token,
        'auth_access_token': option.token,
        'auth_uuid': option.uuid,
        'version_name': option.version_name,
        'profile_name': option.profile_name,
        'version_type': option.version_type,
        'game_directory': option.game_dir,
        'user_type': option.user_type,
        'assets_index_name': option.assets_index_name,
        'assets_root': option.assets_dir,
        'game_assets': option.assets_dir,
        'user_properties': '{}',
        'library_directory': option.libraries_dir,
        'classpath_separator': (';' if get_platform() == Platform.WINDOWS else ':'),
        'primary_jar': option.client_jar,
    }
    template = Template(result)
    return template.safe_substitute(mapping)

def get_jvm_args(
        java: Java,
        log4j_config_path: str, client_jar: str, natives_path: str,
        args_json: Optional[List[Union[str, dict]]] = None, memory: int = 1024,
        proxies: Union[HttpProxy, SocksProxy, NoProxy] = NoProxy()
) -> str:
    '''
    Get JVM parameters.

    :param java: an instance of the mc_toolbox.java.Java class
    :param log4j_config: directory for log4j configuration files, left blank to indicate not using log4j
    :param client_jar: the path of the game's main file
    :param natives_path: the storage path of the game's native dependency library
    :param args_json: if it is after Minecraft version 1.12.2, you need to fill in the value represented by the arguments.jvm key in client. json. Otherwise, fill in None (default value is None)
    :param memory: maximum memory in MB
    :param proxies: HTTP/SOCKS proxy object, default value is an instance of NoProxy (indicating not using a proxy)
    '''
    result_list = []

    if isinstance(proxies, HttpProxy):
        proxies_t = proxies.netloc.split(':')
        result_list.append(f'-Dhttp.proxyHost= {proxies_t[0]}')
        result_list.append(f'-Dhttp.proxyPort= {proxies_t[1]}')
        if proxies.https:
            result_list.append(f'-Dhttps.proxyHost= {proxies_t[0]}')
            result_list.append(f'-Dhttps.proxyPort= {proxies_t[1]}')
    elif isinstance(proxies, SocksProxy):
        proxies_t = proxies.netloc.split(':')
        result_list.append(f'-DsocksProxyHost= {proxies_t[0]}')
        result_list.append(f'-DsocksProxyPort= {proxies_t[1]}')

    result_list.append(f'-Xmx{memory}M "-Dfile.encoding=UTF-8"')
    if java.major_version < 19:
        result_list.append('"-Dstdout.encoding=UTF-8" "-Dstderr.encoding=UTF-8"')
    else:
        result_list.append('"-Dstdout.encoding=UTF-8" "-Dstderr.encoding=UTF-8"')

    # log4j
    # fix CVE-2021-44228
    if log4j_config_path:
        result_list.extend([
            '"-Djava.rmi.server.useCodebaseOnly=true"',
            '"-Dcom.sun.jndi.rmi.object.trustURLCodebase=false"',
            '"-Dcom.sun.jndi.cosnaming.object.trustURLCodebase=false"',
            '"-Dlog4j2.formatMsgNoLookups=true"',
            f'"-Dlog4j.configurationFile={log4j_config_path}"',
        ])

    result_list.append(f'"-Dminecraft.client.jar={client_jar}"')
    if get_platform() == Platform.MACOS:
        result_list.append('"-Xdock:name=Minecraft"')

    # G1GC
    result_list.append('-XX:+UnlockExperimentalVMOptions')
    result_list.append('-XX:+UseG1GC')
    result_list.append('"-XX:G1NewSizePercent=20"')
    result_list.append('"-XX:G1ReservePercent=20"')
    result_list.append('"-XX:MaxGCPauseMillis=50"')
    result_list.append('"-XX:MaxGCPauseMillis=50"')
    result_list.append('"-XX:G1HeapRegionSize=32M"')

    result_list.append('-XX:-UseAdaptiveSizePolicy')
    result_list.append('-XX:-OmitStackTraceInFastThrow')
    result_list.append('-XX:-DontCompileHugeMethods')
    if java.major_version == 16:
        result_list.append('"--illegal-access=premit"')
    result_list.append('"-Dfml.ignoreInvalidMinecraftCertificates=true"')
    result_list.append('"-Dfml.ignorePatchDiscrepancies=true"')
    result_list.append('"-Dsodium.checks.issue2561=false"')

    if args_json != None:
        for arg in args_json:
            if (
                isinstance(arg, dict) 
                and rule_check(arg['rules'])
            ):
                result_list.extend(list(map(
                    lambda x: f'"{x}"' if '=' in x else x,
                    arg['value']
                )))
            else:
                result_list.append(Template(arg).safe_substitute(natives_directory=natives_path))
    else:
        if get_platform() == Platform.MACOS:
            result_list.append('-XstartOnFirstThread')
        if get_platform() == Platform.WINDOWS:
            result_list.append('"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"')
            if re.findall(r'^10\.', get_system_version()):
                result_list.append('"-Dos.name=Windows 10"')
                result_list.append('"-Dos.version=10.0"')
        if java.arch == Arch.X86 or java.arch == Arch.ARM_HF:
            result_list.append('-Xss1M')
        result_list.extend([
            f'"-Djava.library.path={natives_path}"',
            '"-Dminecraft.launcher.brand=${launcher_name}"',
            '"-Dminecraft.launcher.version=${launcher_version}"',
            '-classpath',
            '${classpath}',
        ])

    return ' '.join(result_list)

def get_launch_script(
        java: Java, option: LaunchOption, mainclass: str,
        libraries_json: List[dict], game_args_json: Union[str, List[str]],
        log4j_config_path: str, natives_path: str,
        launcher_name: str, launcher_version: str,

        memory: int = 1024, jvm_args_json: Optional[List[Union[str, dict]]] = None
) -> str:
    '''
    Get the launch script.

    :param java: an instance of the mc_toolbox.java.Java class
    :param option: a LaunchOption
    :param mainclass: main class
    :param libraries_json: record a list of game dependency libraries, which can be found in the "libraries" key of client.json
    :param game_args_json: a string or list describing the format of game parameters
    :param log4j_config: directory for log4j configuration files, left blank to indicate not using log4j
    :param natives_path: the storage path of the game's native dependency library
    :param launcher_name: launcher name
    :param launcher_version: launcher version
    
    Regarding game_args_json: In Minecraft 1.12.2 and earlier versions, game_args_json should be passed the value represented by the minecraftArguments key in client.json.
    After Minecraft version 1.12.2, game_args_json should be passed the value of the arguments.game
    '''
    result = f'"{java.path}" '
    result += get_jvm_args(
        java,
        log4j_config_path,
        option.client_jar,
        natives_path,
        jvm_args_json,
        memory,
        option.proxies
    )
    result += f' {mainclass} '
    result += get_game_args(option, game_args_json)
    return Template(result).safe_substitute(
        launcher_name=launcher_name,
        launcher_version=launcher_version,
        classpath=get_classpath(
            libraries_json,
            option.libraries_dir,
            option.client_jar,
        ),
    )
