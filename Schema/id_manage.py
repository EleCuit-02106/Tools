#!/usr/bin/python3
#coding:utf-8

import sys
import toml

class IdInfo:
    def __init__(self, name:str, begin:int, end:int):
        self.name = name
        self.begin = begin
        self.end = end

    def in_range(self, id:int) -> bool:
        return self.begin <= id and id <= self.end

    @classmethod
    def createFromToml(cls, toml) :
        return IdInfo(
            toml['name'],
            toml['begin'],
            toml['end'])


class IdManager:
    ID_TOML = 'KANJI-asset/schema/master/id.toml'

    def __init__(self):
        self.dict_toml = self.load()

    def load(self):
        return toml.load(open(IdManager.ID_TOML))

    def search_id_by_int(self, id:int):
        for value in self.dict_toml['id'].values():
            if value['begin'] <= id and id <= value['end']:
                return value['name']
        return None

    def search_id_by_name(self, name:str) -> IdInfo:
        for value in self.dict_toml['id'].values():
            if value['name'] == name:
                return IdInfo.createFromToml(value)
        return None

def search_id_by_int(id:int):
    id_mgr = IdManager()
    result = id_mgr.search_id_by_int(id)
    if result == None:
        print('Not Found %d' % id)
    else:
        print('%d is within %s' % (id, result))

def search_id_by_name(name:str):
    id_mgr = IdManager()
    result = id_mgr.search_id_by_name(name)
    if result == None:
        print('Not Found %s' % name)
    else:
        print('%sID is exist (range:%d-%d)' % (name, result.begin, result.end))

if __name__ == "__main__":
    args = sys.argv
    if args[1].isdigit():
        search_id_by_int(int(args[1]))
    else:
        search_id_by_name(args[1])

