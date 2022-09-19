#!/usr/bin/python3
#coding:utf-8

from pathlib import Path
import sys
import os
import shutil
from repository_path import ProjectPath
from cs_source_generator import DataCsGenerator, RepositoryCsGenerator
from master_type import MDTypeInfo, MDTypeManager
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)

IS_DEBUG = False

# file_path に text を書き込むだけ
def output(file_path:Path, text:str):
    os.makedirs(file_path.parent.absolute(), exist_ok=True)
    logger.info('create file: %s' % file_path.relative_to(ProjectPath.absolute('md_impl')))
    with open(file_path,'w') as f:
        f.write(text)

# cs内容を生成して書き込む
# IS_DEBUG 時は書き込まずにprintする
def create_cs_source(generator, type_info:MDTypeInfo, file_path:Path):
    full_text = generator.generate(type_info)
    if IS_DEBUG:
        print('// %s ------------------------------------------' % file_path.name)
        print(full_text)
    else:
        output(file_path, full_text)

# 1つの型についてcs生成処理を呼び出す
# MasterData自体とRepositoryのcsの2ファイルを生成
def create_cs_sources_impl(type_info:MDTypeInfo, path:Path, key:str):
    indent = '    '
    if key == MDTypeManager.ROOT:
        key = ''
    # MasterXXXX.cs
    create_cs_source(
        DataCsGenerator(indent),
        type_info,
        path / 'Classes' / key / ('Master%s.cs' % type_info.data_type_name))
    # MasterXXXXRepository.cs
    create_cs_source(
        RepositoryCsGenerator(indent),
        type_info,
        path / 'Repositories' / key / ('Master%sRepository.cs' % type_info.data_type_name))

def create_cs_sources(mgr:MDTypeManager, path_dst:Path):
    for key in mgr.dict_info:
        for value in mgr.dict_info[key].values():
            create_cs_sources_impl(value, path_dst, key)

if __name__ == "__main__":
    basicConfig(level=INFO)
    args = sys.argv
    IS_DEBUG = len(args) > 1 and args[1] == 'debug'

    dest_dir = ProjectPath.absolute('md_impl')
    if not IS_DEBUG and os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    mgr = MDTypeManager()
    create_cs_sources(mgr, dest_dir)
