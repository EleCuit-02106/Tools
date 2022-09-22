#!/usr/bin/python3
#coding:utf-8

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import rapidjson
from master_type import MDField
from repository_path import ProjectPath
from build_schema import output
import pprint
from logging import getLogger, basicConfig, DEBUG, INFO
logger = getLogger(__name__)

class MasterDataConverter:
    """Google Drive 内の SpreadSheet に入稿されたマスタデータを読み込み json 出力する
    """

    NUMERIC_TYPES = ('int', 'float', 'unixtime')

    def __init__(self):
        logger.info('[MasterDataConverter] initialize ...')
        logger.info('[MasterDataConverter] authorize ...')
        self.gs = self.authorize_and_get_gspread()
        logger.info('[MasterDataConverter] load file keys ...')
        self.file_keys = self.load_file_keys()
        self.records = dict()

    def authorize_and_get_gspread(self) -> gspread.Client:
        KEY_JSON_PATH = '/Users/kazuaki/.ssh/readmdbypython-a352795e2e0a.json'
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']
        c = ServiceAccountCredentials.from_json_keyfile_name(KEY_JSON_PATH, scope)
        return gspread.authorize(c)

    def load_file_keys(self) -> list[str]:
        file_keys = ['1Cd3ASeYgy7XOFFU0V1Hj0DGK9oh1g632ShAmpEmtvXc']
        return file_keys

    def load_spreadsheets(self) -> None:
        self.records.clear()
        for file_key in self.file_keys:
            for worksheet in self.gs.open_by_key(file_key).worksheets():
                self.worksheet_to_json(worksheet)

    def worksheet_to_json(self, worksheet:gspread.Worksheet):
        class_name = worksheet.title
        if not class_name in self.records.keys():
            self.records[class_name] = dict()
        field_names = worksheet.row_values(1)
        field_types = worksheet.row_values(2)
        id_column = self.search_id_column(field_names)
        row = 4 # マスタデータのレコードは4行目から
        while True:
            record = worksheet.row_values(row)
            if record is None or len(record) < id_column or record[id_column] == '':
                break # id カラムが空なら全レコードを読み終わったとみなして終了する
            data = dict()
            for column in range(len(field_types)):
                field_type = field_types[column]
                field_name = field_names[column]
                if field_type == 'int' or field_type == 'unixtime':
                    data[field_name] = int(record[column])
                elif field_type == 'float':
                    data[field_name] = float(record[column])
                elif field_type in MDField.VALID_TYPE_NAMES or field_type == 'version':
                    data[field_name] = record[column]
            self.records[class_name][record[id_column]] = data
            row += 1

    # 見つからなかった場合 -1 を返す
    def search_id_column(self, field_names:list[str]):
        column = 1
        for field_name in field_names:
            if field_name == 'id':
                return column - 1
            column += 1
        return -1

    def dump_records_as_json(self):
        dest_dir = ProjectPath.absolute('md_json')
        for md_type in self.records:
            dest_file = 'Master%s.json' % md_type
            output(dest_dir / dest_file, rapidjson.dumps(self.records[md_type]))

if __name__ == "__main__":
    basicConfig(level=INFO)
    mdConverter = MasterDataConverter()
    logger.info('[MasterDataConverter] load master data ...')
    mdConverter.load_spreadsheets()
    logger.info('[MasterDataConverter] dump json ...')
    mdConverter.dump_records_as_json()
    logger.info('[MasterDataConverter] completed.')
