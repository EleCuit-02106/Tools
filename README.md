# Tools
various tools e.g. setup, build, asset download, asset convert

## Schema

check and generate Master/UserClasses

- id_manage.py
  - id.toml からID情報をロード
  - 数値を渡すとそれが属するIDを返す
  - ID名を渡すとその定義域を返す
- master_type.py
  - masterdata.toml から型情報をロード
- validate_data.py
  - 実データ (schema/master/class/) が 型定義(masterdata.toml) に適合しているかを確認
- cs_source_generator.py
  - 与えられた型情報をもとに cs生成を行う
- build_schema.py
  - cs自動生成時に呼ぶ
  - master_type.py を呼び出し型情報を取得、それを cs_source_generator.py に渡してファイルを生成
- repository_path.py
  - path.toml にて固有のパスを定義、それを読み出す


## python から Google Drive へのアクセス方法

### PyDrive2

- 全体の流れ
  - https://note.nkmk.me/python-pydrive-download-upload-delete/
    - PyDrive1 時代の説明だが 2 でも大体同じ
    - PyDrive1 のリンクは切れているので PyDrive2 に読み替えること
      - GitHub: https://github.com/iterative/PyDrive2
      - Docs::QuickStart: https://docs.iterative.ai/PyDrive2/quickstart/
      - Docs::settings.yaml: https://docs.iterative.ai/PyDrive2/oauth/

1. 疎通
  1. Google Cloud の Develop Console にアクセス
    - https://console.cloud.google.com/apis/dashboard?project=readmdbypython&supportedpurview=project
  1. プロジェクト作成
  1. Google Drive API の有効化
    - スプレッドシートの内容を python で読み込むのに Google Sheets API も有効化しておくと良い
      - cf. https://kino-code.com/python_spreadsheets/#Google
  1. 左ペイン > 認証情報 > 認証情報を作成 > OAuthクライアントID と選択
    - 初回はここで同意画面の作成に飛ばされるので飛ばされるので、表示に従い作成する
  1. 終わるとダッシュボードに戻されるので再度「認証情報を作成 > OAuthクライアントID」を選択
    - ドキュメント通りに進行、client_secretsXXXXXX.json をダウンロードする
  - ここまで来たら、 client_secrets.json があるディレクトリで認証が可能
    ~~~py
    from pydrive2.auth import GoogleAuth
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    ~~~
    - 実行するとブラウザが起動しGoogleの同意画面が表示される
    - Google Cloud Console 上でアプリ公開していない場合はテストユーザしかアクセスできないので注意
      1. Google Cloud Console > 左ペイン > OAuth同意画面 のテストユーザ欄の ADD USER からユーザを追加 (Googleアカウント)
      1. 上記コード実行時に表示される同意画面上で、テストユーザに登録したGoogleアカウントを選択する
1. サイレント認証
  - 認証時にブラウザでの操作が要らないように設定する
  1. 認証する python スクリプトと同じ場所に settings.yaml を作成
  1. settings.yaml に以下を記入
    ~~~yaml
    save_credentials: True
    save_credentials_backend: file
    save_credentials_file: secrets/credentials.json # settings.yaml からの相対パス
    ~~~
    - 他にも色々設定できる
      - https://note.nkmk.me/python-pydrive-download-upload-delete/
        - サンプルが PyDrive1 向けなので注意
      - https://docs.iterative.ai/PyDrive2/oauth/
      - settings.yaml を変更した場合は python を再起動すること
        - GoogleAuth() のインスタンスを作り直さないと変更が反映されず変なエラーが出たりする
        - e.g. InvalidConfigError: Unknown client_config_backend
  - 一度ローカル保存してもセッションが切れると認証できなくなる
    - エラーになった場合ローカルの保存ファイルを削除して再度実行するとブラウザで認証画面が表示される
    - TOdO: 自動でファイル消すようにしたい & セッション切れないようにしたい
    ~~~py
    $ python load_spreadsheet.py
    INFO:__main__:[MasterDataConverter] initialize ...
    INFO:__main__:[MasterDataConverter] authorize ...
    INFO:__main__:[MasterDataConverter] load file keys ...
    INFO:__main__:[MasterDataConverter] load master data file list ...
    INFO:oauth2client.client:Refreshing access_token
    INFO:oauth2client.client:Failed to retrieve access token: {
      "error": "invalid_grant",
      "error_description": "Token has been expired or revoked."
    }
    Traceback (most recent call last):
      File "/usr/local/lib/python3.9/site-packages/pydrive2/auth.py", line 668, in Refresh
        self.credentials.refresh(self.http)
      File "/usr/local/lib/python3.9/site-packages/oauth2client/client.py", line 545, in refresh
        self._refresh(http)
      File "/usr/local/lib/python3.9/site-packages/oauth2client/client.py", line 761, in _refresh
        self._do_refresh_request(http)
      File "/usr/local/lib/python3.9/site-packages/oauth2client/client.py", line 819, in _do_refresh_request
        raise HttpAccessTokenRefreshError(error_msg, status=resp.status)
    oauth2client.client.HttpAccessTokenRefreshError: invalid_grant: Token has been expired or revoked.

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):
      File "/Users/kazuaki/develop/Unity/EleCuit/EleCuit/Client/Tools/Schema/load_spreadsheet.py", line 125, in <module>
        mdConverter.load_file_keys()
      File "/Users/kazuaki/develop/Unity/EleCuit/EleCuit/Client/Tools/Schema/load_spreadsheet.py", line 41, in load_file_keys
        self.g_auth.LocalWebserverAuth()
      File "/usr/local/lib/python3.9/site-packages/pydrive2/auth.py", line 131, in _decorated
        self.Refresh()
      File "/usr/local/lib/python3.9/site-packages/pydrive2/auth.py", line 670, in Refresh
        raise RefreshError("Access token refresh failed: %s" % error)
    pydrive2.auth.RefreshError: Access token refresh failed: invalid_grant: Token has been expired or revoked.
    ~~~





