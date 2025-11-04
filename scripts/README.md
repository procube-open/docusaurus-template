# Docusaurus Documentation Scripts

このディレクトリには、Docusaurusドキュメントのメンテナンスと変換を行うスクリプトが含まれています。

## スクリプト一覧

### reorganize_docs.py

DITA OTからエクスポートされたMarkdownファイルをDocusaurus MDX形式に変換し、ドキュメント構造を再編成する統合スクリプトです。

### rename_package.py

このテンプレートリポジトリを新しいプロジェクト用にカスタマイズするための設定置き換えスクリプトです。Organization名、タイトル、パッケージ名を一括置換します。

---

## 詳細

### reorganize_docs.py (詳細)

このスクリプトは以下の3つのステップを自動的に実行します：

1. **MDX互換性の修正**
   - HTMLテーブルタグの前後に適切な空行を追加
   - ネストされたテーブルのスペーシング修正
   - コードブロックの言語指定を自動追加
   - 行頭の`import`キーワードをエスケープ（MDXのimport文との混同を防止）
   - 複数の連続空行を正規化

2. **ドキュメント構造の再編成**
   - `index.md`の階層構造に基づいてファイルを再配置
   - ファイル名に順序番号を付与（例：`01-overview.md`）
   - サブディレクトリの自動作成
   - Markdown内のリンクと画像パスを自動修正
   - Docusaurus用の`_category_.json`ファイルを生成

3. **元ファイルの削除**
   - 番号なしの元ファイルを削除し、重複を回避

---

## 詳細

### reorganize_docs.py (詳細)

DITA OTからエクスポートされたMarkdownファイルをDocusaurus MDX形式に変換し、ドキュメント構造を再編成する統合スクリプトです。

#### 機能

このスクリプトは以下の3つのステップを自動的に実行します：

1. **MDX互換性の修正**
   - HTMLテーブルタグの前後に適切な空行を追加
   - ネストされたテーブルのスペーシング修正
   - コードブロックの言語指定を自動追加
   - 行頭の`import`キーワードをエスケープ（MDXのimport文との混同を防止）
   - 複数の連続空行を正規化

2. **ドキュメント構造の再編成**
   - `index.md`の階層構造に基づいてファイルを再配置
   - ファイル名に順序番号を付与（例：`01-overview.md`）
   - サブディレクトリの自動作成
   - Markdown内のリンクと画像パスを自動修正
   - Docusaurus用の`_category_.json`ファイルを生成

3. **元ファイルの削除**
   - 番号なしの元ファイルを削除し、重複を回避

#### 使用方法

```bash
cd /workspaces/docusaurus-template/scripts
python3 reorganize_docs.py --docs-dir ../docs
```

#### 実行後の確認

```bash
npm run start-doc
```

ブラウザで http://localhost:3000 を開き、サイドバーの構造と各ページの表示を確認してください。

---

### reorganize_docs.py (オプション詳細)

##### 1. 通常の実行（すべての処理を一括実行）

```bash
python3 scripts/reorganize_docs.py --docs-dir docs
```

実行内容：
- すべてのMarkdownファイルのMDX互換性を修正
- `index.md`を解析して階層構造を抽出
- ファイルに順序番号を付与して再配置
- リンクと画像パスを自動修正
- `_category_.json`を生成
- 元のファイル（番号なし）を削除

##### 2. ドライラン（変更内容のプレビュー）

```bash
python3 scripts/reorganize_docs.py --docs-dir docs --dry-run
```

実行内容：
- 実際のファイル操作を行わず、変更内容を表示のみ

##### 3. MDX修正のスキップ

```bash
python3 scripts/reorganize_docs.py --docs-dir docs --skip-mdx-fix
```

実行内容：
- MDX互換性の修正をスキップし、ドキュメント構造の再編成のみ実行

##### 4. 元ファイルの削除のみ

```bash
python3 scripts/reorganize_docs.py --docs-dir docs --remove-originals
```

実行内容：
- 番号なしの元ファイルを削除（再編成後に重複を避けるため）

##### 5. クリーンアップ（番号付きファイルの削除）

```bash
python3 scripts/reorganize_docs.py --docs-dir docs --clean
```

実行内容：
- 番号付きファイルを削除（再実行前のクリーンアップ用）

#### オプション

| オプション | 説明 |
|-----------|------|
| `--docs-dir <path>` | docsディレクトリのパス（デフォルト: `docs`） |
| `--dry-run` | ドライランモード（実際のファイル操作を行わない） |
| `--skip-mdx-fix` | MDX互換性の修正をスキップ |
| `--remove-originals` | 元のファイル（番号なし）を削除 |
| `--clean` | 番号付きファイルを削除してクリーンアップ |

#### ファイル名の規則

- **通常ファイル**: `{順序番号}-{元のファイル名}.md`
  - 例：`01-overview.md`, `02-architecture.md`
- **子要素を持つファイル**: サブディレクトリの`index.md`
  - 例：`install/index.md`（子要素用のサブディレクトリを作成）

#### 実行フロー

```
ステップ1: MDX互換性の修正
  ├─ すべてのMarkdownファイルをスキャン
  ├─ HTMLテーブルタグの前後に空行を追加
  ├─ コードブロックの言語指定を自動追加
  └─ import文をエスケープ

ステップ2: ドキュメント構造の再編成
  ├─ 第1パス: ファイルマッピングの構築
  │   ├─ index.mdを解析
  │   ├─ 元のパス → 新しいパスのマッピングを作成
  │   └─ カテゴリ索引ファイルもマッピングに追加
  ├─ 第2パス: ファイルの移動と内容の修正
  │   ├─ ファイルを新しい位置にコピー
  │   ├─ Markdownリンクを修正
  │   ├─ 画像パスを修正
  │   └─ _category_.jsonを生成
  ├─ 第3パス: カテゴリ索引ファイルのリンク修正
  │   └─ 各カテゴリのインデックスファイルのリンクを修正
  └─ 第4パス: index.mdのリンク修正
      └─ メインのindex.mdのリンクを修正

ステップ3: 元ファイルの削除
  └─ 番号なしの元ファイルを削除
```

---

### rename_package.py

このテンプレートリポジトリを新しいプロジェクト用にカスタマイズするための設定置き換えスクリプトです。リポジトリ全体のOrganization名、タイトル、パッケージ名を一括で置き換えます。

#### 機能

- **Organization名の置き換え**: GitHub Organization名を変更（例：`procube-open` → `your-org`）
- **タイトルの置き換え**: プロジェクトタイトルを変更（例：`[Enter Title Here]` → `My Project`）
- **パッケージ名の置き換え**: NPMパッケージ名を変更（例：`docusaurus-template` → `my-project`）
- **ファイル名のリネーム**: パッケージ名を含むファイル名も自動的にリネーム
- **対象ファイル**: `.py`, `.json`, `.md`, `.ts`, `.tsx`, `.js`, `.mjs`, `.jsx`, `.yaml`, `.yml`, `.sh`, `.txt`, `.css`, `.jsonc`
- **除外ディレクトリ**: `.git`, `node_modules`, `.docusaurus`, `build`, `__pycache__`, `.venv` などは処理対象外

#### 使用方法

##### 基本的な使い方

```bash
cd /workspaces/docusaurus-template/scripts
python3 rename_package.py
```

実行すると対話形式で入力を求められます：

```
============================================================
リポジトリ設定置き換えツール
============================================================

現在の設定:
  Organization: procube-open
  タイトル: [Enter Title Here]
  パッケージ名: docusaurus-template

新しい設定を入力してください（Enterでデフォルト値を使用）:

Organization名 (デフォルト: procube-open): your-org
タイトル (デフォルト: [Enter Title Here]): My Documentation
パッケージ名 (デフォルト: docusaurus-template): my-docs

============================================================
置き換え内容の確認:
  Organization: procube-open → your-org
  タイトル: [Enter Title Here] → My Documentation
  パッケージ名: docusaurus-template → my-docs
============================================================

この内容で置き換えを実行しますか? (y/N): y
```

#### 実行例

新しいプロジェクトを開始する際の手順：

```bash
# 1. このテンプレートリポジトリをクローン
git clone https://github.com/procube-open/docusaurus-template.git my-project
cd my-project

# 2. 設定を置き換え
cd scripts
python3 rename_package.py

# 3. Organization名、タイトル、パッケージ名を入力
# （対話形式でプロンプトに従って入力）

# 4. 変更を確認してコミット
git add .
git commit -m "Customize project settings"
```

#### 注意事項

- **実行前にバックアップを推奨**: 一括置換を行うため、必要に応じて事前にバックアップを取ってください
- **確認プロンプト**: 実行前に置き換え内容が表示され、確認を求められます
- **ファイルリネーム**: パッケージ名を含むファイル名（例：`docusaurus-template.zip`）も自動的にリネームされます
- **除外ファイル**: `node_modules`や`.git`などの自動生成・管理ファイルは対象外です

#### 処理の流れ

1. 現在の設定（デフォルト値）を表示
2. 新しい設定値の入力を対話形式で受け付け
3. 置き換え内容を確認プロンプトで表示
4. ユーザーが承認（`y`入力）したら実行
5. ファイル名にパッケージ名が含まれる場合はリネーム
6. 対象ファイルの内容を一括置換
7. 処理結果（リネームされたファイル、更新されたファイル）を表示

---

## ワークフロー

### 初回セットアップ

```bash
# 1. Markdownファイルの修正とドキュメント再編成を一括実行
cd /workspaces/docusaurus-template/scripts
python3 reorganize_docs.py --docs-dir ../docs

# 2. Docusaurusサーバーを起動して確認
npm run start-doc
```

### 既存のドキュメントを更新する場合

```bash
# 1. 既存の番号付きファイルをクリーンアップ
python3 scripts/reorganize_docs.py --docs-dir docs --clean

# 2. index.mdを編集して構造を変更

# 3. 再編成を実行
python3 scripts/reorganize_docs.py --docs-dir docs
```

### ドライランでプレビュー

```bash
# 変更内容を確認（ファイル操作なし）
python3 scripts/reorganize_docs.py --docs-dir docs --dry-run
```

## トラブルシューティング

### リンクが正しく修正されない場合

1. `index.md`のバックアップ（`.index.md.backup`）が存在することを確認
2. リンク先のファイルが`index.md`に記載されていることを確認
3. ファイルパスが正しいことを確認

### 画像が表示されない場合

- 画像ファイルが`docs/image/`配下に存在することを確認
- 元のMarkdownファイルからの相対パスが正しいことを確認
- スクリプトは自動的に`../image/`形式のパスを新しい構造に合わせて修正します

### エラーが発生した場合

1. `--dry-run`オプションで問題を特定
2. `.index.md.backup`から`index.md`を復元
3. エラーメッセージを確認して該当ファイルをチェック

## 注意事項

- スクリプトはscriptsディレクトリまたはプロジェクトルートから実行できます
- スクリプトを実行すると、`index.md`が自動的にバックアップされます（`.index.md.backup`）
- 元のファイル（番号なし）は自動的に削除されます
- 変更を確認してからコミットすることを推奨します
- 初回実行時は`--dry-run`オプションで動作を確認することをお勧めします

## ファイル構造の例

実行前：
```
docs/
  ├── index.md
  ├── abstruct/
  │   ├── abstruct.md
  │   ├── overview.md
  │   └── architecture.md
  └── construct/
      ├── construct.md
      └── systemStructure.md
```

実行後：
```
docs/
  ├── index.md
  ├── .index.md.backup
  ├── abstruct/
  │   ├── _category_.json
  │   ├── 01-overview.md
  │   └── 02-architecture.md
  └── construct/
      ├── _category_.json
      └── 01-systemStructure.md
```

## ライセンス

このスクリプトは、docusaurus-templateプロジェクトの一部として提供されています。
