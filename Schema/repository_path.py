#!/usr/bin/python3
#coding:utf-8

from pathlib import Path
import toml
import pprint

# path.tomlに定義したパスを簡単に呼び出せるように
class ProjectPath:
    root = Path()
    paths = dict()

    @classmethod
    def load(cls):
        with open('path.toml', 'r') as f:
            paths_toml = toml.load(f)
        paths_toml = paths_toml['tool']['path']
        cls.root = Path(paths_toml['root'])
        for key, path in paths_toml['relative'].items():
            cls.paths[key] = Path(path)

    @classmethod
    def absolute(cls, key) -> Path:
        return cls.root / cls.paths[key]

ProjectPath.load()

if __name__ == "__main__":
    print('root: %s' % ProjectPath.root)
    pprint.pprint(ProjectPath.paths)
