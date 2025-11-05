# docusaurus-template

このレポジトリでは、Docusaurus を利用して複数レポジトリと連携したドキュメント管理を行うためのテンプレートを提供します。

### 注意点

このテンプレートは開発コンテナを利用することを前提としています。開発コンテナのセットアップ方法については、[公式ドキュメント](https://code.visualstudio.com/docs/remote/containers)を参照してください。

## 利用手順

1. このレポジトリをTemplateとして利用し、新しいリポジトリを作成します。
1. 作成したレポジトリを開発コンテナで開きます。
1. ターミナルから、rename_package.py スクリプトを実行し、パッケージ名を変更します。

   ```bash
   python3 scripts/rename_package.py
   ```

1. ドキュメントなどで使われるタイトル、レポジトリの組織名、リポジトリ名を入力して下さい。
1. pushするとnpmパッケージがGithubにリリースされます。

### Github Pages の有効化

Github Pages を有効化するには、リポジトリの Settings > Pages に移動し、Source を `gh-pages` ブランチに設定します。


### docs.zip　のリリース

ドキュメントを外部レポジトリから取得する場合、外部レポジトリ上でdocs.zipをリリースする必要があります。
docs.zipの作成手順については、`packages/docusaurus/README.md`の「3. docs.zip の作成」を参照してください。

### 外部リポジトリからのドキュメント取得

外部レポジトリにリリースされたdocs.zipを取得するには、リポジトリ設定画面の Secrets and variables > Actions に以下のシークレットを登録してください。

Secrets:

- `PAT_FOR_DISPATCH`: 外部リポジトリにアクセス可能なPersonal Access Token

Variables:

- `TARGET_REPOS`: ドキュメントを取得する外部リポジトリの一覧（スペース区切り）
- `CNAME`: GitHub Pagesで利用するカスタムドメイン名（必須ではない）

### Ditaからの移行手順

1. DITA OTを利用して、DITAドキュメントをMarkdown形式でエクスポートします。
   ```
   mkdir docs
   dita --input=src/Manual/IDManagerV2.ditamap --format=markdown_github --output=docs
   ```
1. 開発コンテナのターミナルで、reorganize_docs.pyスクリプトを実行します。
   ```
   python3 scripts/reorganize_docs.py --docs-dir docs
   ```
1. Docusaurusサーバーを起動し、ドキュメントを確認します。
   ```
   npm run start-doc
   ```

スクリプトの詳細については、`scripts/README.md`を参照してください。