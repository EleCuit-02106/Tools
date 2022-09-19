#!/usr/bin/python3
#coding:utf-8

from pathlib import Path
import toml
import pprint

# path.tomlに定義したパスを簡単に呼び出せるように
class KanjiPath:
    root = Path()
    pathes = dict()

    @classmethod
    def load(cls):
        with open('path.toml', 'r') as f:
            pathes_toml = toml.load(f)
        pathes_toml = pathes_toml['tool']['path']
        cls.root = Path(pathes_toml['root'])
        for key, path in pathes_toml['relative'].items():
            cls.pathes[key] = Path(path)

    @classmethod
    def absolute(cls, key) -> Path:
        return cls.root / cls.pathes[key]

KanjiPath.load()

if __name__ == "__main__":
    print('root: %s' % KanjiPath.root)
    pprint.pprint(KanjiPath.pathes)
