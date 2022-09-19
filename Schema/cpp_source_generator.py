#!/usr/bin/python3
#coding:utf-8

from master_type import MDTypeInfo

class CppSourceGeneratorBase:
    def __init__(self, indent:str):
        self.indent = indent
        self.build_info:str
        self.preprocessor:str
        self.namespace_begin:str
        self.namespace_end:str
        self.class_body:str

    # 5つに分けて生成し、最後に結合する
    # 分けた5つのうちファイルごとに異なる部分はサブクラスでオーバーライド
    def generate(self, md_type_info:MDTypeInfo) -> str:
        self.generate_class_body(md_type_info.data_type_name, md_type_info.fields)
        self.generate_build_info(md_type_info.data_type_name)
        self.generate_preprocessor(md_type_info)
        self.generate_namespace_begin()
        self.generate_namespace_end()
        return self.concatenate()

    def concatenate(self) -> str:
        full_text  = self.build_info
        full_text += self.preprocessor + '\n'
        full_text += self.namespace_begin + '\n'
        full_text += self.class_body + '\n'
        full_text += self.namespace_end + '\n'
        return full_text

    def generate_build_info(self, data_type_name:str):
        self.build_info = '// This file is generated from %s.toml\n' % data_type_name

    def generate_preprocessor(self, md_type_info:MDTypeInfo):
        pass

    def generate_namespace_begin(self):
        self.namespace_begin  = 'namespace kanji {\n'
        self.namespace_begin += 'namespace md {\n'

    def generate_namespace_end(self):
        self.namespace_end  = '}\n'
        self.namespace_end += '}\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        pass

    def to_camel_case(self, snake_str:str):
        first, *others = snake_str.split('_')
        return ''.join([first.lower(), *map(str.title, others)])


class DataHppGenerator(CppSourceGeneratorBase):
    def generate_preprocessor(self, md_type_info:MDTypeInfo):
        need_ids_hpp = False
        for field in md_type_info.fields.values():
            if field.is_id:
                need_ids_hpp = True
        self.preprocessor = '#pragma once\n'
        if need_ids_hpp:
            self.preprocessor += '#include "IDs.hpp"\n'
        for include_file in md_type_info.include_files():
            self.preprocessor += '#include %s\n' % include_file

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        getters = ''
        fields = ''
        ctor_declaration = self.indent + 'Master%s(' % data_type_name
        ctor_definition = ''
        for field in field_dict.values():
            raw_type = field.raw_type
            pass_type = field.pass_type
            # e.g. const s3d::String& label() const { return m_label; }
            getters += self.indent + '%s %s() const { return m_%s; }\n' % (pass_type, self.to_camel_case(field.name), field.name)
            # e.g. s3d::String m_label;
            fields  += self.indent + '%s m_%s;\n' % (raw_type, field.name)
            # e.g. MasterHoge(const s3d::String& label, ... ):
            ctor_declaration += '%s %s, ' % (pass_type, field.name)
            # e.g. m_label(label), ... {}
            ctor_definition += self.indent + 'm_%s(%s),\n' % (field.name, field.name)
        ctor_declaration = ctor_declaration.rstrip(', ')
        ctor_declaration += ') :\n'
        ctor_definition = ctor_definition.rstrip(',\n')
        ctor_definition += ' {}\n'
        self.generateClassBodyImpl(data_type_name, getters, fields, ctor_declaration + ctor_definition)

    def generateClassBodyImpl(self, data_type_name:str, getter:str, field:str, constructor:str):
        self.class_body  = 'class Master%s {\n' % data_type_name
        self.class_body += 'public: // public getter\n'
        self.class_body += getter
        self.class_body += 'private: // field\n'
        self.class_body += field
        self.class_body += 'public: // ctor\n'
        self.class_body += constructor
        self.class_body += '};\n'


class RepositoryHppGenerator(CppSourceGeneratorBase):
    def generate_preprocessor(self, md_type_info:MDTypeInfo):
        need_ids_hpp = False
        for field in md_type_info.fields.values():
            if field.is_id:
                need_ids_hpp = True
        self.preprocessor  = '#pragma once\n'
        self.preprocessor += '#include "Singleton.hpp"\n'
        self.preprocessor += '#include "MasterDataRepository.hpp"\n'
        self.preprocessor += '#include "Master%s.hpp"\n' % md_type_info.data_type_name
        if need_ids_hpp:
            self.preprocessor += '#include "IDs.hpp"\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        primary_key_type = None
        for field in field_dict.values():
            if field.is_primary_key:
                primary_key_type = field.raw_type
        self.class_body  = 'class Master%sRepository :\n' % data_type_name
        self.class_body += self.indent + 'public dx::md::MasterDataRepository<%s, Master%s>,\n' % (primary_key_type, data_type_name)
        self.class_body += self.indent + 'public dx::cmp::Singleton<Master%sRepository> {\n' % data_type_name
        self.class_body += 'protected: // protected function\n'
        self.class_body += self.indent + 'void initialize();\n'
        self.class_body += 'public: // ctor\n'
        self.class_body += self.indent + 'Master%sRepository() { initialize(); }\n' % data_type_name
        self.class_body += '};\n'


class RepositoryCppGenerator(CppSourceGeneratorBase):
    CLASS_TYPE = {'Vec2': 'vec2'}

    def generate_preprocessor(self, md_type_info:MDTypeInfo):
        self.preprocessor  = '#include "Master%sRepository.hpp"\n' % md_type_info.data_type_name
        self.preprocessor += '#include "TomlAsset.hpp"\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        primary_key = None
        for field in field_dict.values():
            if field.is_primary_key:
                primary_key = field
        self.class_body  = 'void Master%sRepository::initialize() {\n' % data_type_name
        self.class_body += self.indent + 'const dx::toml::TomlAsset toml(U"%s");\n' % (data_type_name)
        self.class_body += self.indent + 'const dx::toml::TomlKey key(U"masterdata");\n'
        self.class_body += self.indent + 's3d::TOMLTableView table = toml[key].tableView();\n'
        self.class_body += self.indent + 'for (const s3d::TOMLTableMember& table_member : table) {\n'
        self.class_body += self.indent * 2 + 'const auto& toml_value = table_member.value;\n'
        # 主キー
        self.class_body += self.indent * 2 + 'm_data.emplace(%s(toml_value[U"%s"].get<int>()),\n' % (primary_key.raw_type, primary_key.name)
        self.class_body += self.indent * 3 + 'std::make_shared<kanji::md::Master%s>(\n' % data_type_name
        # メンバ変数
        fields_str = ''
        for field in field_dict.values():
            if field.is_id:
                fields_str += self.indent * 4 + '%s(toml_value[U"%s"].get<int>()),\n' % (field.raw_type, field.name)
            elif field.type_name in RepositoryCppGenerator.CLASS_TYPE:
                fields_str += self.indent * 4 + 'dx::toml::%s(toml_value[U"%s"]),\n' % (RepositoryCppGenerator.CLASS_TYPE[field.type_name], field.name)
            else:
                fields_str += self.indent * 4 + 'toml_value[U"%s"].get<%s>(),\n' % (field.name, field.raw_type)
        fields_str = fields_str.rstrip(',\n') + '));\n'
        self.class_body += fields_str
        self.class_body += self.indent + '}\n'
        self.class_body += '}\n'

