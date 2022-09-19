#!/usr/bin/python3
#coding:utf-8

from pathlib import Path
import sys
import os
import shutil
import toml
from repository_path import KanjiPath
from cpp_source_generator import DataHppGenerator, RepositoryHppGenerator, RepositoryCppGenerator
from master_type import MDTypeInfo, MDTypeManager
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)

IS_DEBUG = False

# file_path に text を書き込むだけ
def output(file_path:Path, text:str):
    os.makedirs(file_path.parent.absolute(), exist_ok=True)
    logger.info('create file: %s' % file_path.relative_to(KanjiPath.absolute('md_header')))
    with open(file_path,'w') as f:
        f.write(text)

# hpp/cpp内容を生成して書き込む
# IS_DEBUG 時は書き込まずにprintする
def create_cpp_source(generator, type_info:MDTypeInfo, file_path:Path):
    full_text = generator.generate(type_info)
    if IS_DEBUG:
        print('// %s ------------------------------------------' % file_path.name)
        print(full_text)
    else:
        output(file_path, full_text)

# 1つの型についてhpp/cpp生成処理を呼び出す
# MasterData自体のhpp、Repositoryのhpp/cppがあるので3ファイルを生成
def create_cpp_sources_impl(type_info:MDTypeInfo, path:Path, key:str):
    indent = '    '
    if key == MDTypeManager.ROOT:
        key = ''
    # MasterHoge.hpp
    create_cpp_source(
        DataHppGenerator(indent),
        type_info,
        path / 'class' / key / ('Master%s.hpp' % type_info.data_type_name))
    # MasterHogeRepository.hpp
    create_cpp_source(
        RepositoryHppGenerator(indent),
        type_info,
        path / 'repository' / key / ('Master%sRepository.hpp' % type_info.data_type_name))
    # MasterHogeRepository.cpp
    create_cpp_source(
        RepositoryCppGenerator(indent),
        type_info,
        path / 'repository' / key / ('Master%sRepository.cpp' % type_info.data_type_name))

def create_cpp_sources(mgr:MDTypeManager, path_dst:Path):
    for key in mgr.dict_info:
        for value in mgr.dict_info[key].values():
            create_cpp_sources_impl(value, path_dst, key)

if __name__ == "__main__":
    basicConfig(level=INFO)
    args = sys.argv
    IS_DEBUG = len(args) > 1 and args[1] == 'debug'

    dest_dir = KanjiPath.absolute('md_header')
    if not IS_DEBUG and os.path.isdir(dest_dir):
        shutil.rmtree(dest_dir)
    mgr = MDTypeManager()
    create_cpp_sources(mgr, dest_dir)
