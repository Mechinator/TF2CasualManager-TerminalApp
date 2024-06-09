# -*- coding: utf-8 -*-
import codecs
import json
import os
import sys
import traceback
import re
import platform

__version__ = '1.6.2'


class Map(object):

    def __init__(self, category, mode, data):
        self.category = category
        self.mode = mode
        self.name = data.get('name', '')
        self.bsp = data.get('bsp', '')
        self.group = data.get('group', -1)
        self.bit = data.get('bit', -1)

    def __str__(self):
        return 'Map({})'.format(self.bsp)

    def __repr__(self):
        return 'Map({})'.format(self.bsp)


def load_maps(data):
    maps = dict()
    groups = list()
    for category in data.get('categories'):
        for mode in category.get('modes'):
            for game_map in mode.get('maps'):
                map_data = Map(category['name'], mode['name'], game_map)
                bsp = map_data.bsp
                group = map_data.group
                bit = map_data.bit
                if len(groups) - 1 < group:
                    groups.extend([[] for _ in range(group - len(groups) + 1)])
                if len(groups[group]) - 1 < bit:
                    groups[group].extend([''] * (bit - len(groups[group]) + 1))
                maps[bsp] = map_data
                groups[group][bit] = bsp
    return maps, groups


def int2maps(number, group):
    flags = list(reversed('{:b}'.format(number)))
    maps = list()
    for i, flag in enumerate(flags):
        if not int(flag):
            continue
        game_map = group[i] if - len(group) <= i < len(group) else ''
        if game_map:
            maps.append(game_map)
    return maps


def ints2maps(numbers, groups):
    maps = list()
    for i, number in enumerate(numbers):
        if i >= len(groups):
            break
        maps.extend(int2maps(number, groups[i]))
    return maps


def maps2ints(maps, maps_data):
    groups = list()
    for game_map in maps:
        try:
            m = maps_data[game_map.strip()]
            group = m.group
            bit = m.bit
            if len(groups) - 1 < group:
                groups.extend([[] for _ in range(group - len(groups) + 1)])
            if len(groups[group]) - 1 < bit:
                groups[group].extend(['0'] * (bit - len(groups[group]) + 1))
            groups[group][bit] = '1'
        except KeyError:
            print(f"Warning: Map '{game_map}' not found in map data.")
            continue
    groups = list(map(lambda x: ['0'] if not x else x, groups))
    groups = list(map(lambda x: int(''.join(reversed(x)), 2), groups))
    return groups


def get_path():
    if getattr(sys, 'frozen', False):
        app_path = os.path.dirname(os.path.realpath(sys.executable))
    else:
        app_path = os.path.dirname(os.path.realpath(__file__))
    return app_path


def read_casual(path, groups):
    lines = list()
    try:
        with codecs.open(path, encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return False
    lines = list(map(lambda x: int(x.replace('selected_maps_bits:', '').strip()), lines))
    return ints2maps(lines, groups)


def write_casual(path, maps, maps_data):
    groups = maps2ints(maps, maps_data)
    groups = list(
        map(lambda x: 'selected_maps_bits: {}\r\n'.format(x), groups))
    try:
        with codecs.open(path, 'w', encoding='utf-8') as f:
            f.writelines(groups)
        return True
    except:
        return False


def read_cm(path=None):
    if path is None:
        path = os.path.join(get_path(), 'tf2cm.json')
    if not os.path.isfile(path):
        default_file = ''
        paths = [
            os.path.join(get_path(), r'tf2cm_default.json'),
            os.path.join(get_path(), r'data\tf2cm_default.json')
        ]
        for f in paths:
            if os.path.isfile(f):
                default_file = f
                break
        if not default_file:
            write_cm({'version': 1, 'selections': {}})
        else:
            write_cm(read_cm(f))
        return read_cm()
    with codecs.open(path, encoding='utf-8') as f:
        data = json.loads(f.read())
    return data


def write_cm(data, path=None):
    if path is None:
        path = os.path.join(get_path(), 'tf2cm.json')
    with codecs.open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=None, separators=(',', ':')))


def error(msg):
    print(f"Error: {msg}")


def tf2():
    if platform.system() == 'Windows':
        vdf_pat = re.compile(r'^\s*"\d+"\s*".+"\s*')
        steam = None
        reg_key = r'Software\Valve\Steam'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key) as handle:
                steam = winreg.QueryValueEx(handle, 'SteamPath')[
                    0].replace('/', '\\')
        except:
            return None
        libs = [steam]
        libinfo = os.path.join(steam, r'steamapps\libraryfolders.vdf')
        try:
            with open(libinfo, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if vdf_pat.match(line):
                        libs.append(line.split()[1].strip(
                            '"').replace('\\\\', '\\'))
        except:
            pass
        for lib in libs:
            find_acf = os.path.join(lib, r'steamapps\appmanifest_440.acf')
            if os.path.isfile(find_acf):
                tf_root = os.path.join(lib, r'steamapps\common\Team Fortress 2\tf')
                if os.path.isdir(tf_root):
                    return tf_root
    elif platform.system() == 'Linux':
        steam_path = os.path.expanduser('~/.steam/steam')
        tf_root = os.path.join(steam_path, 'steamapps/common/Team Fortress 2/tf')
        if os.path.isdir(tf_root):
            return tf_root
    return None


def main():
    app_path = get_path()
    data_file = None
    path = [
        os.path.join(app_path, r'data/casual.min.json'),
        os.path.join(app_path, r'data/casual.json')
    ]
    print("Checking for data files in the following paths:")
    for p in path:
        print(p)
        if os.path.isfile(p):
            data_file = p
            break
    if not data_file:
        error('Map selection data file not found.\nPlease re-download TF2CM.')
        sys.exit(1)
    casual = dict()
    try:
        with codecs.open(data_file, encoding='utf-8') as f:
            casual = json.loads(f.read())
    except:
        error('Map selection data file is broken.\nPlease re-download TF2CM.')
        sys.exit(1)
    maps_data, groups = load_maps(casual)

    try:
        cm = read_cm()
    except:
        error(traceback.format_exc())
        sys.exit(1)

    try:
        tf = tf2()
        if not tf:
            error('TF2 is not installed properly...')
            sys.exit(1)
    except:
        error('Error checking TF2 installation')
        sys.exit(1)

    print(f"TF2CM version {__version__}")
    print("Casual mode map selection tool for Team Fortress 2")
    print("Maps loaded successfully.")

    while True:
        print("\n1. List maps")
        print("2. Read casual map selection")
        print("3. Write casual map selection")
        print("4. Exit")
        choice = input("Enter your choice: ")
        if choice == '1':
            for map_bsp, map_obj in maps_data.items():
                print(f"{map_obj.name} ({map_bsp})")
        elif choice == '2':
            casual_path = input("Enter the path to your casual map selection file: ")
            selected_maps = read_casual(casual_path, groups)
            if selected_maps:
                print("Selected maps:")
                for map_name in selected_maps:
                    print(map_name)
            else:
                error("Could not read the casual map selection file.")
        elif choice == '3':
            casual_path = input("Enter the path to save your casual map selection file: ")
            selected_maps = input("Enter the map names to select (comma-separated): ").split(',')
            success = write_casual(casual_path, selected_maps, maps_data)
            if success:
                print("Casual map selection file written successfully.")
            else:
                error("Could not write the casual map selection file.")
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == '__main__':
    main()
