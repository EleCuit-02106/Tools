#!/usr/bin/python3
#coding:utf-8

from master_type import MDTypeInfo

class CsSourceGeneratorBase:
    def __init__(self, indent:str):
        self.indent = indent
        self.build_info:str
        self.usings:str
        self.namespace_begin:str
        self.namespace_end:str
        self.class_body:str

    # 5つに分けて生成し、最後に結合する
    # 分けた5つのうちファイルごとに異なる部分はサブクラスでオーバーライド
    def generate(self, md_type_info:MDTypeInfo) -> str:
        self.generate_class_body(md_type_info.data_type_name, md_type_info.fields)
        self.generate_build_info(md_type_info.data_type_name)
        self.generate_usings(md_type_info)
        self.generate_namespace_begin(md_type_info.namespace)
        self.generate_namespace_end()
        return self.concatenate()

    def concatenate(self) -> str:
        full_text  = self.build_info
        full_text += self.usings + '\n'
        full_text += self.namespace_begin + '\n'
        full_text += self.class_body + '\n'
        full_text += self.namespace_end + '\n'
        return full_text

    def generate_build_info(self, data_type_name:str):
        self.build_info = '// This file is auto-generated from %s.toml\n' % data_type_name

    def generate_usings(self, md_type_info:MDTypeInfo):
        pass

    def generate_namespace_begin(self, namespace:str):
        if len(namespace) > 0:
            self.namespace_begin = 'namespace MD.%s\n{\n' % namespace
        else:
            self.namespace_begin = 'namespace MD\n{\n'

    def generate_namespace_end(self):
        self.namespace_end = '}\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        pass

    def snake_to_camel_case(self, snake_str:str):
        first, *others = snake_str.split('_') # capwords() も使えそう
        return ''.join([first.lower(), *map(str.title, others)])

    def snake_to_pascal_case(self, snake_str:str):
        words = snake_str.split('_')
        return ''.join(map(str.title, words))

    def camel_to_pascal_case(self, camel_str:str):
        return camel_str[0].upper() + camel_str[1:]

    def pascal_to_camel_case(self, camel_str:str):
        return camel_str[0].lower() + camel_str[1:]

    def using_line(self, typename:str) -> str:
        return 'using %s;\n' % typename

    def begin_region(self, label:str) -> str:
        return self.indent * 2 + '#region %s\n' % label

    def end_region(self) -> str:
        return self.indent * 2 + '#endregion\n'

    def switch_region(self, label:str) -> str:
        return self.end_region() + '\n' + self.begin_region(label)


class DataCsGenerator(CsSourceGeneratorBase):
    def generate_usings(self, md_type_info:MDTypeInfo):
        self.usings:str = ''
        self.usings += 'using System;\n'
        self.usings += 'using UnityEngine;\n'
        for using in md_type_info.using_list():
            self.usings += self.using_line(using)

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        self.class_body = ''
        properties = ''
        field_declarations = ''
        ctor_declaration = self.indent * 2 + 'public Master%s(\n' % data_type_name
        ctor_definition = ''
        for field in field_dict.values():
            pass_type = field.pass_type
            property_name = self.camel_to_pascal_case(field.name)
            # e.g. public string Label { get; }
            properties += self.indent * 2 + 'public %s %s => %s;\n' % (pass_type, property_name, field.name)
            # e.g. [SerializeField] private string label;
            field_declarations += self.indent * 2 + '[SerializeField] private %s %s;\n' % (pass_type, field.name)
            # e.g. MasterHoge(string label, ... ) {
            ctor_declaration += self.indent * 3 + '%s %s,\n' % (pass_type, field.name)
            # e.g. Label = label;
            ctor_definition += self.indent * 3 + 'this.%s = %s;\n' % (field.name, field.name)
        ctor_declaration = ctor_declaration.rstrip(',\n')
        ctor_declaration += ')\n' + self.indent * 2 + '{\n'
        ctor_definition = ctor_definition.rstrip(',\n')
        ctor_definition += '\n' + self.indent * 2 + '}\n'
        self.generate_class_body_impl(data_type_name, properties, field_declarations, ctor_declaration + ctor_definition)
        self.generate_list_class_impl(data_type_name)

    def generate_class_body_impl(self, data_type_name:str, properties:str, field_declarations:str, constructor:str):
        self.class_body += self.indent + '[Serializable]\n'
        self.class_body += self.indent + 'public sealed class Master%s\n' % data_type_name
        self.class_body += self.indent + '{\n'
        self.class_body += self.begin_region('property')
        self.class_body += properties
        self.class_body += self.switch_region('field')
        self.class_body += field_declarations
        self.class_body += self.switch_region('ctor')
        self.class_body += constructor
        self.class_body += self.end_region()
        self.class_body += self.indent + '}\n'

    def generate_list_class_impl(self, data_type_name):
        self.class_body += '\n'
        self.class_body += self.indent + '[Serializable]\n'
        self.class_body += self.indent + 'public sealed class Master%sList\n' % data_type_name
        self.class_body += self.indent + '{\n'
        self.class_body += self.indent * 2 + 'public Master%s[] data;\n' % data_type_name
        self.class_body += self.indent + '}\n'


class RepositoryCsGenerator(CsSourceGeneratorBase):
    def generate_usings(self, md_type_info:MDTypeInfo):
        self.usings:str = ''
        self.usings += 'using System.Collections.Generic;\n'
        self.usings += 'using Cysharp.Threading.Tasks;\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        # 主キーを特定
        primary_key_type = None
        for field in field_dict.values():
            if field.is_primary_key:
                primary_key_type = field.raw_type
        if primary_key_type is None:
            return # 保険: 主キーがないのはおかしい

        self.generate_class_body_impl(primary_key_type, 'Master' + data_type_name)

    def generate_class_body_impl(self, key_type:str, value_type:str):
        self.class_body  = self.indent + 'public class %sRepository : du.Cmp.Singleton<%sRepository>\n' % (value_type, value_type)
        self.class_body += self.indent + '{\n'
        self.class_body += self.begin_region('public')
        self.class_body += self.indent * 2 + 'public bool IsExist(%s id) => m_data.ContainsKey(id);\n' % key_type
        self.class_body += self.indent * 2 + 'public %s At(%s id) => m_data[id];\n' % (value_type, key_type)
        self.class_body += self.indent * 2 + 'public IReadOnlyDictionary<%s, %s> Data { get => m_data; }\n' % (key_type, value_type)
        self.class_body += self.switch_region('field')
        self.class_body += self.indent * 2 + 'private Dictionary<%s, %s> m_data;\n' % (key_type, value_type)
        self.class_body += self.switch_region('private function')
        self.class_body += self.indent * 2 + 'public async UniTask Load()\n'
        self.class_body += self.indent * 2 + '{\n'
        self.class_body += self.indent * 3 + 'if (m_data != null) { return; }\n'
        self.class_body += self.indent * 3 + 'm_data = new Dictionary<%s, %s>();\n' % (key_type, value_type)
        self.class_body += self.indent * 3 + 'string assetAddress = global::EC.Adds.MasterJson + "%s" + ".json";\n' % value_type
        self.class_body += self.indent * 3 + 'var task = du.File.FileUtils.LoadTextFileFull(assetAddress);\n'
        self.class_body += self.indent * 3 + 'string mdRecordsAsJson = await task;\n'
        self.class_body += self.indent * 3 + 'var mdList = UnityEngine.JsonUtility.FromJson<%sList>(mdRecordsAsJson);\n' % value_type
        self.class_body += self.indent * 3 + 'foreach (var record in mdList.data)\n'
        self.class_body += self.indent * 3 + '{\n'
        self.class_body += self.indent * 4 + 'm_data.Add(record.Id, record);\n'
        self.class_body += self.indent * 3 + '}\n'
        self.class_body += self.indent * 2 + '}\n'
        self.class_body += self.end_region()
        self.class_body += self.indent + '}\n'


class RepositoryCsCppGenerator(CsSourceGeneratorBase):
    CLASS_TYPE = {'Vec2': 'Vector2', 'Vec3': 'Vector3' }

    def generate_usings(self, md_type_info:MDTypeInfo):
        self.usings  = '#include "Master%sRepository.hpp"\n' % md_type_info.data_type_name
        self.usings += '#include "TomlAsset.hpp"\n'

    def generate_class_body(self, data_type_name:str, field_dict:dict):
        primary_key = None
        for field in field_dict.values():
            if field.is_primary_key:
                primary_key = field
        self.class_body  = 'void Master%sRepository::Initialize() {\n' % data_type_name
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
            elif field.type_name in RepositoryCsGenerator.CLASS_TYPE:
                fields_str += self.indent * 4 + 'dx::toml::%s(toml_value[U"%s"]),\n' % (RepositoryCsGenerator.CLASS_TYPE[field.type_name], field.name)
            else:
                fields_str += self.indent * 4 + 'toml_value[U"%s"].get<%s>(),\n' % (field.name, field.raw_type)
        fields_str = fields_str.rstrip(',\n') + '));\n'
        self.class_body += fields_str
        self.class_body += self.indent + '}\n'
        self.class_body += '}\n'

