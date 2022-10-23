#!/usr/bin/python3
#coding:utf-8

import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
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
    GOOGLE_DRIVE_MD_PATH = "home/pro/develop/EleCuit/Data/MasterData"

    def __init__(self):
        logger.info('[MasterDataConverter] initialize ...')
        logger.info('[MasterDataConverter] authorize ...')
        self.gs = self._authorize_and_get_gspread()
        logger.info('[MasterDataConverter] load file keys ...')
        self.file_keys = list()
        self.records = dict()

    def _authorize_and_get_gspread(self) -> gspread.Client:
        tool_dir = ProjectPath.absolute('tool')
        key_json_path = tool_dir / 'Schema/secrets/gspread_key.json'
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']
        c = ServiceAccountCredentials.from_json_keyfile_name(key_json_path, scope)
        return gspread.authorize(c)

    def load_file_keys(self) -> None:
        self.g_auth = GoogleAuth()
        self.g_auth.LocalWebserverAuth()
        self.g_drive = GoogleDrive(self.g_auth)
        g_drive_md_path_as_list = self.GOOGLE_DRIVE_MD_PATH.split('/')
        md_root_dir = self._search_dir(self.g_drive, g_drive_md_path_as_list)
        logger.info('[MasterDataConverter.SearchFilesAtGoogleDrive] MasterData/')
        self._load_file_keys_impl(md_root_dir)
        # self.file_keys = ['1Cd3ASeYgy7XOFFU0V1Hj0DGK9oh1g632ShAmpEmtvXc']

    def _load_file_keys_impl(self, dir_id:str, log_indent:int=1) -> None:
        children = self.g_drive.ListFile({'q': ('"%s" in parents' % dir_id)}).GetList()
        for child in children:
            if child['mimeType'] == 'application/vnd.google-apps.folder':
                logger.info('[MasterDataConverter.SearchFilesAtGoogleDrive] %s%s/' % ('  ' * log_indent, child['title']))
                self._load_file_keys_impl(child['id'], log_indent + 1)
            elif child['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                logger.info('[MasterDataConverter.SearchFilesAtGoogleDrive] %s%s' % ('  ' * log_indent, child['title']))
                self.file_keys.append(child['id'])

    def _search_dir(self, drive:GoogleDrive, absolute_path:list[str]) -> str:
        parent_dir = 'root'
        for next_dir in absolute_path:
            searched_dir = drive.ListFile({'q': ('"%s" in parents and title = "%s"' % (parent_dir, next_dir))}).GetList()
            if len(searched_dir) != 1:
                logger.critical('[MasterDataConverter.SearchFilesAtGoogleDrive] No such directory: %s (%s)' % (next_dir, absolute_path))
                logger.critical('[MasterDataConverter.SearchFilesAtGoogleDrive] Exist directories: %s' % searched_dir)
                return None
            parent_dir = searched_dir[0]['id']
        return parent_dir

    def load_spreadsheets(self) -> None:
        self.records.clear()
        loaded_files = 0
        for file_key in self.file_keys:
            for worksheet in self.gs.open_by_key(file_key).worksheets():
                self._worksheet_to_json(worksheet)
            loaded_files += 1
            logger.info('[MasterDataConverter.ConvertToJson] converted %d / %d files' % (loaded_files, len(self.file_keys)))

    def _worksheet_to_json(self, worksheet:gspread.Worksheet):
        class_name = worksheet.title
        logger.info('[MasterDataConverter.ConvertToJson] convert %s sheet' % class_name)
        if not class_name in self.records.keys():
            self.records[class_name] = dict()
        field_names = worksheet.row_values(1)
        field_types = worksheet.row_values(2)
        id_column = self._search_id_column(field_names)
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
    def _search_id_column(self, field_names:list[str]):
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
    #  認証情報ファイルがカレントディレクトリにある必要があるので実行ディレクトリを指定する
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    mdConverter = MasterDataConverter()
    logger.info('[MasterDataConverter] load master data file list ...')
    mdConverter.load_file_keys()
    logger.info('[MasterDataConverter] load master data ...')
    mdConverter.load_spreadsheets()
    logger.info('[MasterDataConverter] dump json ...')
    mdConverter.dump_records_as_json()
    logger.info('[MasterDataConverter] completed.')
