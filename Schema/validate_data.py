#!/usr/bin/python3
#coding:utf-8

from pathlib import Path
import toml
from repository_path import KanjiPath
from master_type import MDTypeManager, MDTypeInfo
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)


class MDValidator:
    def __init__(self):
        self.root_path = KanjiPath.absolute('md_class')
        self.type_mgr = MDTypeManager()

    def validate(self):
        for toml_path in self.root_path.glob('**/*.toml'): # e.g. 'class/kanji/KanjiParam.toml'
            sub_directories = tuple(str(toml_path.parent.relative_to(self.root_path)).split('/'))
            type_name = toml_path.stem
            self.validate_toml(sub_directories, type_name)

    def validate_toml(self, sub_directories:tuple, type_name:str):
        toml_name = type_name + '.toml'
        logger.info('validate... : %s (%s)' % (toml_name, '/'.join(sub_directories)))
        data = self.load(sub_directories, toml_name)
        for dir in sub_directories:
            if dir == '.':
                type_info_list = self.type_mgr.dict_info[MDTypeManager.ROOT]
            else:
                type_info_list = self.type_mgr.dict_info[dir]
        data_have_error = list()
        for key in data: # key = yama, tera, ...
            record = data[key] # e.g. { 'id': 0, 'character': '山', ...}
            type_info = type_info_list[type_name] # e.g. { 'id': MDField(id, KanjiID), ... }
            if not self.vaildate_necessary_and_sufficient(key, record, type_info):
                data_have_error.append('%s::%s' % (type_name, key))
        if len(data_have_error) == 0:
            logger.info('All data is validated : %d records in %s' % (len(data), toml_name))

    def load(self, sub_directories:tuple, toml_name:str) -> dict:
        for dir in sub_directories:
            toml_path = self.root_path / dir
        logger.debug('load ' + str(toml_path.absolute()))
        dict_toml = dict()
        with open(toml_path / toml_name) as f:
            dict_toml = toml.load(f)
        return dict_toml['masterdata']

    # type_infoで定義されているfieldとrecordの持つfieldが必要十分か
    def vaildate_necessary_and_sufficient(self, key:str, record:dict, type_info:MDTypeInfo) -> bool:
        return self.vaildate_sufficient(key, record, type_info) and self.vaildate_necessary(key, record, type_info)

    # type_infoで定義されているfieldがすべてrecordに含まれているか
    def vaildate_sufficient(self, key:str, record:dict, type_info:MDTypeInfo) -> bool:
        lack_fields = list()
        for necessary_field in type_info.fields:
            if not necessary_field in record:
                lack_fields.append(necessary_field)
        if len(lack_fields) != 0:
            logger.error('The submitted data contains missing fields. (key: [%s])' % key)
            for lack_field in lack_fields:
                logger.error('> ' + lack_field)
        return len(lack_fields) == 0

    # recordに入稿されているfieldがすべてtype_infoに含まれているか
    def vaildate_necessary(self, key:str, record:dict, type_info:MDTypeInfo) -> bool:
        unnecessary_fields = list()
        for exist_field in record:
            if not exist_field in type_info.fields:
                unnecessary_fields.append(exist_field)
        if len(unnecessary_fields) != 0:
            logger.error('The submitted data contains unnecessary fields. (key: [%s])' % key)
            for unnecessary_field in unnecessary_fields:
                logger.error('> ' + unnecessary_field)
        return len(unnecessary_fields) == 0


if __name__ == "__main__":
    basicConfig(level=INFO)
    validator = MDValidator()
    validator.validate()

