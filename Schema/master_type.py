#!/usr/bin/python3
#coding:utf-8

import toml
from repository_path import ProjectPath
from logging import getLogger, basicConfig, DEBUG
logger = getLogger(__name__)
import pprint

class MDField:
    VALID_TYPE_NAMES = ('int', 'float', 'string', 'Vec2', 'Vec3')
    TYPE_DICT = { 'Vec2': 'Vector2', 'Vec3': 'Vector3' }
    HEAVY_OBJECT = ('string', 'Vec2', 'Vec3')

    def __init__(self, name:str, type_attribute:str):
        self.name = name
        type_name, *attributes = type_attribute.split(':')
        self.type_name = type_name
        self.is_id = False
        self.is_primary_key = False
        for attribute in attributes:
            if attribute == 'ID':
                self.is_id = True
            if attribute == 'PKey':
                self.is_primary_key = True
        if not self.is_id:
            if not self.type_name in MDField.VALID_TYPE_NAMES:
                logger.critical('There is invalid type name: %s' % self.type_name)
        self.raw_type, self.pass_type = self.read_types()

    # 型情報はtoml上では属性と一体化したただの文字列なので解析する
    def read_types(self) -> tuple[str, str]:
        # メンバ変数の型
        if self.is_id:
            raw_type = self.type_name + 'ID'
        else:
            if self.type_name in MDField.TYPE_DICT:
                raw_type = MDField.TYPE_DICT[self.type_name]
            else:
                raw_type = self.type_name
        # 引数/返り値の型
        if self.type_name in MDField.HEAVY_OBJECT:
            pass_type = raw_type # TOdO: in/out
        else:
            pass_type = raw_type
        return (raw_type, pass_type)


class MDTypeInfo:
    USING = { 'Vec2': 'UnityEngine', 'Vec3': 'UnityEngine' }

    def __init__(self, namespace:str, data_type_name:str, toml:dict):
        self.namespace = namespace
        self.data_type_name = data_type_name
        self.primary_key = None
        self.types_requires_include = list()
        self.fields = self.read_fields(toml['field'])

    def read_fields(self, field_toml:dict) -> dict:
        fields = dict()
        for name, type_attribute in field_toml.items():
            field = MDField(name, type_attribute)
            fields[name] = field
            if field.is_primary_key:
                if self.primary_key != None:
                    logger.critical('There are multiple primary keys.')
                self.primary_key = field.name
            if field.type_name in MDTypeInfo.USING and not field.type_name in self.types_requires_include:
                self.types_requires_include.append(field.type_name)
        if self.primary_key == None:
            logger.critical('There is no primary key.')
        return fields

    def using_list(self):
        using_list = list()
        for type_name in self.types_requires_include:
            using_list.append(MDTypeInfo.USING[type_name])
        return using_list

    def log(self):
        print('// %s --------------------' % self.data_type_name)
        for field in self.fields.values():
            if field.is_primary_key:
                primary_icon = '*'
            else:
                primary_icon = ' '
            if field.is_id:
                constraint = ' (ID: ranged)'
            else:
                constraint = ''
            print('%s%s %s%s' % (primary_icon, field.type_name, field.name, constraint))
        print('// --------------------')

# masterdata.toml全体を読み込み型情報に変換する
class MDTypeManager:
    ROOT = 'root'
    def __init__(self):
        self.dict_toml = None
        self.dict_info = dict()
        self.dict_info[MDTypeManager.ROOT] = dict()
        self.load()
        self.read(self.dict_toml['masterdata'], '')
        pprint.pprint(self.dict_info)

    def load(self):
        with open(ProjectPath.absolute('md_toml')) as f:
            self.dict_toml = toml.load(f)

    def read(self, dict_toml:dict, parent_keys:str):
        for key in dict_toml:
            if 'field' in dict_toml[key]:
                md = MDTypeInfo(parent_keys.replace('/', '.'), key, dict_toml[key])
                if len(parent_keys) == 0:
                    self.dict_info[MDTypeManager.ROOT][md.data_type_name] = md
                else:
                    self.dict_info[parent_keys][md.data_type_name] = md
            else:
                full_key = self.full_key(key, parent_keys)
                self.dict_info[full_key] = dict()
                self.read(dict_toml[key], full_key)

    def full_key(self, key:str, parent_keys:str) -> str:
        if len(parent_keys) == 0:
            return key
        else:
            return '%s/%s' % (parent_keys, key)

    def at(self, type_name:str, key:str) -> MDTypeInfo:
        return self.dict_info[key][type_name]


if __name__ == "__main__":
    basicConfig(level=DEBUG)
    mgr = MDTypeManager()

