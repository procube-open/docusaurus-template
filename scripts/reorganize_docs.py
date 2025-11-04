#!/usr/bin/env python3
"""
Docusaurusのサイドバー構造に従ってドキュメントファイルを再編成するスクリプト

DITA OTからエクスポートされたMarkdownファイルをDocusaurus MDX形式に変換し、
index.mdの階層構造を解析して、Docusaurusが認識できるフォルダ構造とファイル名に変換します。
ファイル名の先頭に番号を付与することで、サイドバーの表示順序を制御します。

機能:
- MDX互換性の修正（HTMLテーブル、コードブロック、import文のエスケープ等）
- ファイルの順序番号付与
- サブディレクトリの自動作成
- Markdown内のリンクを自動修正
- 画像パスの修正
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class DocItem:
    """ドキュメント項目を表すデータクラス"""
    title: str
    file_path: Optional[str]
    indent_level: int
    order: int
    children: List['DocItem']


class FileMapping:
    """ファイルパスのマッピングを管理するクラス"""

    def __init__(self):
        # 元のファイルパス -> 新しいファイルパスのマッピング
        self.mapping: Dict[str, str] = {}

    def add_mapping(self, original_path: str, new_path: str):
        """マッピングを追加"""
        # 正規化したパスで保存
        original_normalized = original_path.replace('\\', '/')
        new_normalized = new_path.replace('\\', '/')
        self.mapping[original_normalized] = new_normalized

        # ファイル名だけのマッピングも追加（相対パス解決用）
        original_filename = Path(original_path).name
        self.mapping[original_filename] = new_normalized

    def get_new_path(self, original_path: str) -> Optional[str]:
        """元のパスから新しいパスを取得"""
        original_normalized = original_path.replace('\\', '/')
        return self.mapping.get(original_normalized)

    def find_target_path(self, link: str, current_file_dir: str) -> Optional[str]:
        """リンクから対象ファイルの新しいパスを探す"""
        # リンクの正規化
        link_normalized = link.replace('\\', '/')

        # 完全パスでの検索
        if link_normalized in self.mapping:
            return self.mapping[link_normalized]

        # ファイル名だけでの検索
        link_filename = Path(link).name
        if link_filename in self.mapping:
            return self.mapping[link_filename]

        # 相対パスの解決を試みる
        # ../や./を除去してファイル名を取得
        clean_link = link_normalized.split('/')[-1]
        if clean_link in self.mapping:
            return self.mapping[clean_link]

        return None


def parse_index_md(index_path: str) -> tuple[Dict[str, List[DocItem]], Dict[str, str]]:
    """
    index.mdを解析して階層構造を抽出

    Args:
        index_path: index.mdファイルのパス

    Returns:
        タプル: (カテゴリごとのドキュメント構造辞書, カテゴリフォルダ名->索引ファイルパスの辞書)
    """
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    structure = {}
    category_index_files = {}  # カテゴリフォルダ名 -> 索引ファイルパス
    current_category = None
    current_category_index_file = None
    current_items = []
    stack = []  # (indent_level, DocItem)のスタック
    order_counter = [0]  # 各階層での順序カウンター

    for line_num, line in enumerate(lines, 1):
        # 空行やヘッダーはスキップ
        if not line.strip() or line.startswith('#'):
            continue

        # リスト項目のパターンマッチング: -   [タイトル](path.md)
        match = re.match(r'^(\s*)-\s+\[([^\]]+)\]\(([^)]+)\)', line)
        if not match:
            continue

        indent_str = match.group(1)
        title = match.group(2)
        file_path = match.group(3)

        # インデントレベルを計算（実際のインデント文字数から判定）
        # 最初の項目のインデントを基準とする
        if indent_str == '':
            indent_level = 0
        else:
            # スペースの数で判定（通常は4スペース単位）
            indent = len(indent_str)
            # 4スペース単位でレベルを計算
            indent_level = (indent + 2) // 4  # 切り上げ

        # カテゴリの検出（最初のレベルの項目）
        if indent_level == 0:
            # 前のカテゴリを保存
            if current_category and current_items:
                structure[current_category] = current_items
                if current_category_index_file:
                    category_index_files[current_category] = current_category_index_file

            # ファイルパスからカテゴリフォルダ名を取得
            category_folder = file_path.split('/')[0]
            current_category = category_folder
            current_category_index_file = file_path  # カテゴリの索引ファイルパスを保存
            current_items = []
            stack = []
            order_counter = [0]
            continue  # カテゴリ項目自体は追加しない

        # DocItemの作成
        order_counter = order_counter[:indent_level + 1]
        if len(order_counter) == indent_level:
            order_counter.append(0)
        order_counter[indent_level] += 1

        item = DocItem(
            title=title,
            file_path=file_path,
            indent_level=indent_level,
            order=order_counter[indent_level],
            children=[]
        )

        # スタックを使って親子関係を構築
        while stack and stack[-1][0] >= indent_level:
            stack.pop()

        if stack:
            # 親要素の子として追加
            parent_item = stack[-1][1]
            parent_item.children.append(item)
        else:
            # トップレベルの項目
            if current_category and indent_level > 0:
                current_items.append(item)

        stack.append((indent_level, item))

    # 最後のカテゴリを追加
    if current_category and current_items:
        structure[current_category] = current_items
        if current_category_index_file:
            category_index_files[current_category] = current_category_index_file

    return structure, category_index_files


def generate_docusaurus_filename(item: DocItem, parent_order: str = "") -> str:
    """
    Docusaurus用のファイル名を生成（順序番号付き）

    Args:
        item: ドキュメント項目
        parent_order: 親の順序番号

    Returns:
        順序番号付きファイル名（例: "01-overview.md"）
    """
    if not item.file_path:
        return ""

    # ファイル名から拡張子を除いた部分を取得
    original_filename = Path(item.file_path).stem

    # 順序番号を2桁で生成
    order_str = f"{item.order:02d}"
    if parent_order:
        order_str = f"{parent_order}-{order_str}"

    # ファイル名の生成
    return f"{order_str}-{original_filename}.md"


def create_category_metadata(category_name: str, label: str, position: int, doc_id: Optional[str] = None) -> str:
    """
    Docusaurusのカテゴリメタデータファイル(_category_.json)の内容を生成

    Args:
        category_name: カテゴリ名
        label: 表示ラベル
        position: 表示位置
        doc_id: リンク先のドキュメントID（省略時は自動生成インデックス）

    Returns:
        JSONファイルの内容
    """
    if doc_id:
        link_config = f'''"link": {{
    "type": "doc",
    "id": "{doc_id}"
  }}'''
    else:
        link_config = f'''"link": {{
    "type": "generated-index",
    "description": "{label}のドキュメント一覧"
  }}'''

    return f'''{{
  "label": "{label}",
  "position": {position},
  {link_config}
}}
'''


def fix_markdown_links(content: str, current_file_path: str, file_mapping: FileMapping, docs_dir: str) -> str:
    """
    Markdownファイル内のリンクを修正

    Args:
        content: Markdownファイルの内容
        current_file_path: 現在のファイルの絶対パス
        file_mapping: ファイルマッピング
        docs_dir: docsディレクトリのパス

    Returns:
        修正後の内容
    """
    current_dir = os.path.dirname(current_file_path)
    docs_path = Path(docs_dir)

    # Markdownリンクのパターン: [text](path.md) or [text](path.md#anchor)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md(?:#[^)]*)?)\)')

    def replace_link(match):
        text = match.group(1)
        link = match.group(2)

        # アンカーを分離
        anchor = ""
        if '#' in link:
            link, anchor = link.split('#', 1)
            anchor = f"#{anchor}"

        # 絶対URLやhttp/httpsリンクはスキップ
        if link.startswith('http://') or link.startswith('https://') or link.startswith('/'):
            return match.group(0)

        # リンク先の元のパスを解決
        if link.startswith('../') or link.startswith('./'):
            # 相対パスの場合
            original_link_path = os.path.normpath(
                os.path.join(current_dir, link))
        else:
            # ファイル名だけの場合
            original_link_path = os.path.join(current_dir, link)

        # docsディレクトリからの相対パスに変換
        try:
            rel_path = os.path.relpath(original_link_path, docs_dir)
            rel_path = rel_path.replace('\\', '/')
        except ValueError:
            # 相対パス計算に失敗した場合
            rel_path = link

        # 新しいパスを検索
        new_path = file_mapping.find_target_path(rel_path, current_dir)

        if new_path:
            # 現在のファイルから新しいターゲットへの相対パスを計算
            current_file_rel = os.path.relpath(current_file_path, docs_dir)
            current_file_dir = os.path.dirname(current_file_rel)

            new_path_abs = os.path.join(docs_dir, new_path)
            try:
                new_rel_link = os.path.relpath(
                    new_path_abs, os.path.join(docs_dir, current_file_dir))
                new_rel_link = new_rel_link.replace('\\', '/')

                return f"[{text}]({new_rel_link}{anchor})"
            except ValueError:
                pass

        # 変換できない場合は元のまま
        return match.group(0)

    return link_pattern.sub(replace_link, content)


def fix_image_paths(content: str, current_file_path: str, docs_dir: str, original_file_path: str = None) -> str:
    """
    Markdownファイル内の画像パスを修正

    Args:
        content: Markdownファイルの内容
        current_file_path: 現在のファイルの絶対パス（新しい位置）
        docs_dir: docsディレクトリのパス
        original_file_path: 元のファイルの絶対パス（省略可）

    Returns:
        修正後の内容
    """
    current_dir = os.path.dirname(current_file_path)

    # 画像パターン: ![alt](path)
    image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    def replace_image(match):
        alt = match.group(1)
        img_path = match.group(2)

        # 絶対URLはスキップ
        if img_path.startswith('http://') or img_path.startswith('https://'):
            return match.group(0)

        # 絶対パス（/で始まる）もスキップ
        if img_path.startswith('/'):
            return match.group(0)

        # 相対パスの画像パスを解決
        if img_path.startswith('../') or img_path.startswith('./'):
            # 元のファイルの位置から画像への絶対パスを解決
            if original_file_path:
                original_dir = os.path.dirname(original_file_path)
            else:
                # original_file_pathが指定されていない場合は、
                # current_file_pathから推測（バックアップからの復元など）
                original_dir = current_dir

            # 元のファイルの位置から相対パスで画像の絶対パスを解決
            img_abs_path = os.path.normpath(
                os.path.join(original_dir, img_path))

            # 画像が存在するか確認
            if os.path.exists(img_abs_path):
                try:
                    # 新しいファイルの位置から画像への相対パスを計算
                    new_rel_path = os.path.relpath(img_abs_path, current_dir)
                    new_rel_path = new_rel_path.replace('\\', '/')
                    img_path = new_rel_path
                except ValueError:
                    # 相対パス計算に失敗した場合は元のまま
                    pass
            else:
                # 画像が存在しない場合、docs/image/配下を探索
                # 元の相対パスからファイル名とサブディレクトリを抽出
                # 例: ../image/ActiveDirectory/startMenu.jpg -> ActiveDirectory/startMenu.jpg
                img_path_parts = img_path.replace('\\', '/').split('/')

                # ../や./を除去
                clean_parts = [
                    part for part in img_path_parts if part not in ['..', '.']]

                # imageの後の部分を取得（サブディレクトリ + ファイル名）
                if 'image' in clean_parts:
                    image_idx = clean_parts.index('image')
                    img_relative_parts = clean_parts[image_idx + 1:]
                else:
                    # imageが見つからない場合は全体を使用
                    img_relative_parts = clean_parts

                # docs/image/配下での絶対パスを構築
                img_abs_path = os.path.join(
                    docs_dir, 'image', *img_relative_parts)

                if os.path.exists(img_abs_path):
                    try:
                        # 新しいファイルの位置から画像への相対パスを計算
                        new_rel_path = os.path.relpath(
                            img_abs_path, current_dir)
                        new_rel_path = new_rel_path.replace('\\', '/')
                        img_path = new_rel_path
                    except ValueError:
                        pass
                else:
                    # それでも見つからない場合、現在のファイルの深さから推測
                    current_rel_path = os.path.relpath(
                        current_file_path, docs_dir)
                    current_depth = current_rel_path.count(os.sep)

                    # imageディレクトリへの相対パスを生成
                    up_levels = '../' * current_depth
                    img_path = up_levels + 'image/' + \
                        '/'.join(img_relative_parts)
        else:
            # 相対パス記号がない場合（同じディレクトリを想定）
            # ファイル名だけの場合も同様に処理
            img_filename = os.path.basename(img_path)
            image_dir = os.path.join(docs_dir, 'image')
            img_abs_path = os.path.join(image_dir, img_filename)

            if os.path.exists(img_abs_path):
                try:
                    new_rel_path = os.path.relpath(img_abs_path, current_dir)
                    new_rel_path = new_rel_path.replace('\\', '/')
                    img_path = new_rel_path
                except ValueError:
                    pass

        return f"![{alt}]({img_path})"

    return image_pattern.sub(replace_image, content)


def fix_mdx_compatibility(content: str) -> str:
    """
    MDX互換性の問題を修正

    DITA OTからエクスポートされたMarkdownファイルをDocusaurus MDX形式に変換:
    - HTMLテーブルタグの前後に適切な空行を追加
    - ネストされたテーブルのスペーシング修正
    - コードブロックの言語指定を自動追加
    - 行頭の`import`キーワードをエスケープ（MDXのimport文との混同を防止）
    - 複数の連続空行を正規化

    Args:
        content: Markdownファイルの内容

    Returns:
        修正後の内容
    """
    # 1. </table>の直後に文字が来ている場合(改行なし)、空行を追加
    content = re.sub(r'</table>([^\n])', r'</table>\n\n\1', content)

    # 2. </table>の直後に改行1つだけで文字が続く場合、空行を追加
    content = re.sub(r'</table>\n([^\n])', r'</table>\n\n\1', content)

    # 3. <table>の前に空行がない場合、空行を追加(ファイル先頭を除く)
    content = re.sub(r'([^\n])\n<table>', r'\1\n\n<table>', content)

    # 4. ネストされたテーブル: テキストの直後にスペースなしまたはスペース1つで<table>がある場合、改行を追加
    content = re.sub(r'([^\n])<table>', r'\1\n\n<table>', content)
    content = re.sub(r'([^\n]) <table>', r'\1\n\n<table>', content)

    # 5. テキストの直後にスペース1つでコードブロック(```)が来る場合、改行を追加
    content = re.sub(r'([^\n]) ```', r'\1\n\n```', content)

    # 6. 行頭の"import"をバッククォートで囲む(MDXのimport文と誤認されるのを防ぐ)
    content = re.sub(r'^import / (.*)$', r'`import` / \1',
                     content, flags=re.MULTILINE)
    # 重複修正を防ぐ
    content = re.sub(r'`import` / `import` / ', r'`import` / ', content)

    # 7. 3つ以上の連続した空行を2つに削減
    content = re.sub(r'\n{3,}', r'\n\n', content)

    # 8. コードブロックの言語指定がない場合、適切な言語を推測
    # (既にjson, bash等が指定されている場合は変更しない)
    content = re.sub(r'```\n(\[)', r'```json\n\1', content)  # JSON配列で始まる場合
    content = re.sub(r'```\n(\{)', r'```json\n\1', content)  # JSONオブジェクトで始まる場合
    content = re.sub(r'```\n(yum |npm |cd |mkdir )',
                     r'```bash\n\1', content)  # bashコマンドの場合

    return content


def fix_all_markdown_files(docs_dir: str, dry_run: bool = False):
    """
    すべてのMarkdownファイルのMDX互換性を修正

    Args:
        docs_dir: docsディレクトリのパス
        dry_run: ドライランモード
    """
    print("\n=== MDX互換性の修正 ===")
    print("Markdownファイルをスキャン中...")

    md_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))

    print(f"見つかったMarkdownファイル: {len(md_files)}個\n")

    for file_path in md_files:
        print(f"処理中: {file_path}")

        if not dry_run:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # MDX互換性を修正
                original_content = content
                content = fix_mdx_compatibility(content)

                # 変更があった場合のみ書き込み
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ 修正完了")
                else:
                    print(f"  - 変更なし")
            except Exception as e:
                print(f"  ✗ エラー: {e}")
        else:
            print(f"  (ドライラン)")


def reorganize_docs(docs_dir: str, dry_run: bool = False):
    """
    ドキュメントファイルを再編成

    Args:
        docs_dir: docsディレクトリのパス
        dry_run: Trueの場合、実際のファイル操作は行わずに表示のみ
    """
    index_path = os.path.join(docs_dir, 'index.md')
    index_backup_path = os.path.join(docs_dir, '.index.md.backup')

    if not os.path.exists(index_path):
        print(f"エラー: {index_path} が見つかりません")
        return

    # index.mdをバックアップ（dry_runでない場合のみ）
    if not dry_run:
        print("index.mdをバックアップ中...")
        shutil.copy2(index_path, index_backup_path)
        print(f"  ✓ バックアップ作成: {index_backup_path}")

    # バックアップが存在する場合はそちらを使用、なければ元のファイルを使用
    parse_path = index_backup_path if os.path.exists(
        index_backup_path) else index_path

    print(f"\n{os.path.basename(parse_path)} を解析中...")
    structure, category_index_files = parse_index_md(parse_path)

    print(f"\n検出されたカテゴリ: {list(structure.keys())}")
    print(f"カテゴリ索引ファイル: {category_index_files}\n")

    # ファイルマッピングを作成
    file_mapping = FileMapping()

    # 第1パス: ファイルマッピングを構築
    print("\n=== 第1パス: ファイルマッピングを構築 ===")
    for category_folder, items in structure.items():
        category_path = os.path.join(docs_dir, category_folder)
        if os.path.exists(category_path):
            build_file_mapping(items, category_path, docs_dir, file_mapping)

    # カテゴリ索引ファイルもマッピングに追加
    # これらのファイルは移動しないが、リンク修正の対象にする
    for category_folder, index_file_path in category_index_files.items():
        category_index_path = os.path.join(docs_dir, index_file_path)
        if os.path.exists(category_index_path):
            # 移動しないので、自分自身にマッピング
            file_mapping.add_mapping(index_file_path, index_file_path)
            print(f"カテゴリ索引ファイルをマッピングに追加: {index_file_path}")

    # 第2パス: ファイルの移動と名前変更、リンクの修正
    print("\n=== 第2パス: ファイルの移動と内容の修正 ===")
    category_position = 1
    for category_folder, items in structure.items():
        print(f"\n{'='*60}")
        print(f"カテゴリ: {category_folder}")
        print(f"{'='*60}")

        category_path = os.path.join(docs_dir, category_folder)

        if not os.path.exists(category_path):
            print(f"警告: カテゴリフォルダ {category_path} が存在しません")
            continue

        # カテゴリフォルダに_category_.jsonを作成
        if not dry_run and category_folder in category_index_files:
            category_json_path = os.path.join(category_path, '_category_.json')
            # カテゴリ名をindex.mdから取得
            category_title = get_category_title(parse_path, category_folder)
            category_json_content = create_category_metadata(
                category_folder,
                category_title,
                category_position
            )

            try:
                with open(category_json_path, 'w', encoding='utf-8') as f:
                    f.write(category_json_content)
                print(f"✓ カテゴリ _category_.json 作成: {category_title}")
            except Exception as e:
                print(f"✗ カテゴリ _category_.json作成エラー: {e}")

        category_position += 1

        # ファイルの移動と名前変更
        process_items(items, category_path, docs_dir, dry_run,
                      file_mapping=file_mapping, category_path_prefix=category_folder)

    # 第3パス: カテゴリ索引ファイルのリンク修正
    print("\n=== 第3パス: カテゴリ索引ファイルのリンク修正 ===")
    for category_folder, index_file_path in category_index_files.items():
        category_index_path = os.path.join(docs_dir, index_file_path)

        if os.path.exists(category_index_path):
            print(f"\n{index_file_path} のリンクを修正中...")

            if not dry_run:
                try:
                    with open(category_index_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # リンクを修正
                    original_content = content
                    content = fix_markdown_links(
                        content, category_index_path, file_mapping, docs_dir)
                    content = fix_image_paths(
                        content, category_index_path, docs_dir, category_index_path)

                    # 変更があった場合のみ書き込み
                    if content != original_content:
                        with open(category_index_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"  ✓ リンク修正完了")
                    else:
                        print(f"  - 変更なし")
                except Exception as e:
                    print(f"  ✗ エラー: {e}")

    # 第4パス: index.mdのリンク修正
    print("\n=== 第4パス: index.mdのリンク修正 ===")
    if os.path.exists(index_path):
        print(f"\nindex.md のリンクを修正中...")

        if not dry_run:
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # リンクを修正
                original_content = content
                content = fix_markdown_links(
                    content, index_path, file_mapping, docs_dir)
                content = fix_image_paths(
                    content, index_path, docs_dir, index_path)

                # 変更があった場合のみ書き込み
                if content != original_content:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ リンク修正完了")
                else:
                    print(f"  - 変更なし")
            except Exception as e:
                print(f"  ✗ エラー: {e}")


def get_category_title(index_path: str, category_folder: str) -> str:
    """
    index.mdからカテゴリのタイトルを取得

    Args:
        index_path: index.mdファイルのパス
        category_folder: カテゴリフォルダ名

    Returns:
        カテゴリのタイトル
    """
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # カテゴリフォルダに対応するリンクを探す
        # 例: -   [概要編](abstruct/abstruct.md)
        pattern = rf'^\s*-\s+\[([^\]]+)\]\({category_folder}/[^)]+\)'
        match = re.search(pattern, content, re.MULTILINE)

        if match:
            return match.group(1)
        else:
            # 見つからない場合はフォルダ名をそのまま返す
            return category_folder
    except Exception as e:
        print(f"警告: カテゴリタイトルの取得に失敗: {e}")
        return category_folder


def build_file_mapping(items: List[DocItem], target_dir: str, docs_dir: str,
                       file_mapping: FileMapping, parent_order: str = ""):
    """
    ファイルマッピングを構築（第1パス）

    Args:
        items: 処理するドキュメント項目のリスト
        target_dir: ターゲットディレクトリ
        docs_dir: docsディレクトリのパス
        file_mapping: ファイルマッピングオブジェクト
        parent_order: 親の順序番号
    """
    for item in items:
        has_children = bool(item.children)

        if item.file_path:
            # 新しいファイル名を生成
            order_str = f"{item.order:02d}"
            if parent_order:
                order_str = f"{parent_order}-{order_str}"

            original_filename = Path(item.file_path).stem

            # 子要素がある場合はサブフォルダ内のindex.mdにマッピング
            if has_children:
                subdir_name = original_filename
                subdir_path = os.path.join(target_dir, subdir_name)
                new_filename = "index.md"

                # 相対パスで保存
                target_rel_dir = os.path.relpath(subdir_path, docs_dir)
                new_rel_path = os.path.join(
                    target_rel_dir, new_filename).replace('\\', '/')
            else:
                # 子要素がない場合は通常のファイル
                new_filename = f"{order_str}-{original_filename}.md"

                # 相対パスで保存
                target_rel_dir = os.path.relpath(target_dir, docs_dir)
                new_rel_path = os.path.join(
                    target_rel_dir, new_filename).replace('\\', '/')

            # マッピングを追加
            file_mapping.add_mapping(item.file_path, new_rel_path)

        # 子要素がある場合は再帰的に処理
        if has_children:
            subdir_name = Path(
                item.file_path).stem if item.file_path else f"section_{item.order}"
            subdir_path = os.path.join(target_dir, subdir_name)

            child_order = f"{item.order:02d}" if not parent_order else f"{parent_order}-{item.order:02d}"
            build_file_mapping(item.children, subdir_path,
                               docs_dir, file_mapping, child_order)


def process_items(items: List[DocItem], target_dir: str, docs_dir: str,
                  dry_run: bool = False, parent_order: str = "", depth: int = 0,
                  file_mapping: Optional[FileMapping] = None, category_path_prefix: str = ""):
    """
    ドキュメント項目を再帰的に処理（第2パス）

    Args:
        items: 処理するドキュメント項目のリスト
        target_dir: ターゲットディレクトリ
        docs_dir: docsディレクトリのパス
        dry_run: ドライランモード
        parent_order: 親の順序番号
        depth: 現在の階層の深さ
        file_mapping: ファイルマッピングオブジェクト
        category_path_prefix: カテゴリパスのプレフィックス（doc IDの生成用）
    """
    for item in items:
        indent = "  " * depth

        # 子要素があるかどうかをチェック
        has_children = bool(item.children)

        if item.file_path:
            # ファイルパスを解決
            source_path = os.path.join(docs_dir, item.file_path)

            # 新しいファイル名を生成
            order_str = f"{item.order:02d}"
            if parent_order:
                order_str = f"{parent_order}-{order_str}"

            # ファイル名から拡張子を除いた部分を取得
            original_filename = Path(item.file_path).stem

            # 子要素がある場合の処理
            if has_children:
                # サブディレクトリの作成
                subdir_name = original_filename
                subdir_path = os.path.join(target_dir, subdir_name)

                # index.mdとして配置
                new_filename = "index.md"
                target_path = os.path.join(subdir_path, new_filename)

                print(f"{indent}[{order_str}] {item.title} (サブフォルダあり)")
                print(f"{indent}  📁 サブディレクトリ: {subdir_path}")
                print(f"{indent}  移動元: {source_path}")
                print(f"{indent}  移動先: {target_path}")

                if not dry_run:
                    os.makedirs(subdir_path, exist_ok=True)
            else:
                # 子要素がない場合は通常のファイルとして配置
                new_filename = f"{order_str}-{original_filename}.md"
                target_path = os.path.join(target_dir, new_filename)

                print(f"{indent}[{order_str}] {item.title}")
                print(f"{indent}  移動元: {source_path}")
                print(f"{indent}  移動先: {target_path}")

            # ファイルの存在確認
            if not os.path.exists(source_path):
                print(f"{indent}  ⚠️  警告: ソースファイルが見つかりません")
            elif not dry_run:
                # ファイルを読み込んで内容を修正
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # リンクを修正
                    if file_mapping:
                        content = fix_markdown_links(
                            content, target_path, file_mapping, docs_dir)
                        content = fix_image_paths(
                            content, target_path, docs_dir, source_path)

                    # 修正した内容で新しいファイルに書き込み
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    print(f"{indent}  ✓ コピー・リンク修正完了")
                except Exception as e:
                    print(f"{indent}  ✗ エラー: {e}")

        # 子要素がある場合は再帰的に処理
        if has_children:
            # サブディレクトリの作成
            subdir_name = Path(
                item.file_path).stem if item.file_path else f"section_{item.order}"
            subdir_path = os.path.join(target_dir, subdir_name)

            if not dry_run:
                os.makedirs(subdir_path, exist_ok=True)

                # ドキュメントIDを生成（カテゴリパス + サブディレクトリ名 + /index）
                if category_path_prefix:
                    doc_id = f"{category_path_prefix}/{subdir_name}/index"
                else:
                    doc_id = f"{subdir_name}/index"

                # _category_.jsonを作成（index.mdにリンク）
                category_json_path = os.path.join(
                    subdir_path, '_category_.json')
                order_num = item.order if not parent_order else int(
                    parent_order.split('-')[-1]) * 100 + item.order
                category_json_content = create_category_metadata(
                    subdir_name,
                    item.title,
                    order_num,
                    doc_id=doc_id  # index.mdへのリンクを指定
                )

                try:
                    with open(category_json_path, 'w', encoding='utf-8') as f:
                        f.write(category_json_content)
                    print(f"{indent}    ✓ _category_.json 作成（{doc_id}にリンク）")
                except Exception as e:
                    print(f"{indent}    ✗ _category_.json作成エラー: {e}")

            # 子要素を処理
            child_order = f"{item.order:02d}" if not parent_order else f"{parent_order}-{item.order:02d}"
            # カテゴリパスプレフィックスを更新
            new_category_prefix = f"{category_path_prefix}/{subdir_name}" if category_path_prefix else subdir_name
            process_items(item.children, subdir_path, docs_dir, dry_run,
                          child_order, depth + 1, file_mapping, new_category_prefix)


def clean_numbered_files(docs_dir: str, dry_run: bool = False):
    """
    番号付きファイルを削除（再実行前のクリーンアップ用）

    Args:
        docs_dir: docsディレクトリのパス
        dry_run: ドライランモード
    """
    pattern = re.compile(r'^\d+-')

    for root, dirs, files in os.walk(docs_dir):
        for filename in files:
            if pattern.match(filename) and filename.endswith('.md'):
                file_path = os.path.join(root, filename)
                print(f"削除: {file_path}")

                if not dry_run:
                    os.remove(file_path)


def remove_original_files(docs_dir: str, dry_run: bool = False):
    """
    元のファイル(番号なし)を削除
    index.mdに記載されているファイルのうち、番号付きバージョンが存在するものを削除

    Args:
        docs_dir: docsディレクトリのパス
        dry_run: ドライランモード
    """
    index_backup_path = os.path.join(docs_dir, '.index.md.backup')

    # バックアップが存在する場合はそちらを使用、なければ元のファイルを使用
    if os.path.exists(index_backup_path):
        parse_path = index_backup_path
        print(f"バックアップファイル {parse_path} を使用します")
    else:
        parse_path = os.path.join(docs_dir, 'index.md')
        if not os.path.exists(parse_path):
            print(f"エラー: index.mdもバックアップも見つかりません")
            return

    # index.mdを解析
    structure, category_index_files = parse_index_md(parse_path)

    # 削除対象のファイルリストを作成
    files_to_remove = []

    for category_folder, items in structure.items():
        category_path = os.path.join(docs_dir, category_folder)
        if os.path.exists(category_path):
            collect_original_files(items, docs_dir, files_to_remove)

    # ファイルを削除
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            print(f"削除: {file_path}")
            if not dry_run:
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"  ✗ エラー: {e}")


def collect_original_files(items: List[DocItem], docs_dir: str, files_to_remove: List[str]):
    """
    削除対象の元ファイルを収集

    Args:
        items: ドキュメント項目のリスト
        docs_dir: docsディレクトリのパス
        files_to_remove: 削除対象ファイルリスト
    """
    for item in items:
        if item.file_path:
            original_path = os.path.join(docs_dir, item.file_path)
            files_to_remove.append(original_path)

        if item.children:
            collect_original_files(item.children, docs_dir, files_to_remove)


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Docusaurusのサイドバー構造に従ってドキュメントを再編成し、MDX互換性を修正'
    )
    parser.add_argument(
        '--docs-dir',
        default='docs',
        help='docsディレクトリのパス（デフォルト: docs）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='ドライランモード（実際のファイル操作を行わない）'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='番号付きファイルを削除してクリーンアップ'
    )
    parser.add_argument(
        '--remove-originals',
        action='store_true',
        help='元のファイル（番号なし）を削除'
    )
    parser.add_argument(
        '--skip-mdx-fix',
        action='store_true',
        help='MDX互換性の修正をスキップ'
    )

    args = parser.parse_args()

    # スクリプトのディレクトリから相対パスを解決
    script_dir = Path(__file__).parent
    docs_dir = script_dir / args.docs_dir

    if not docs_dir.exists():
        print(f"エラー: ディレクトリが見つかりません: {docs_dir}")
        return

    if args.dry_run:
        print("=" * 60)
        print("ドライランモード（実際のファイル操作は行いません）")
        print("=" * 60)

    if args.clean:
        print("\n番号付きファイルをクリーンアップ中...")
        clean_numbered_files(str(docs_dir), args.dry_run)
        print("\nクリーンアップ完了")
    elif args.remove_originals:
        print("\n元のファイル（番号なし）を削除中...")
        remove_original_files(str(docs_dir), args.dry_run)
        print("\n削除完了")
    else:
        # ステップ1: MDX互換性の修正
        if not args.skip_mdx_fix:
            print("\n" + "=" * 60)
            print("ステップ 1/3: MDX互換性の修正")
            print("=" * 60)
            fix_all_markdown_files(str(docs_dir), args.dry_run)

        # ステップ2: ドキュメント構造の再編成
        print("\n" + "=" * 60)
        print(f"ステップ 2/3: ドキュメント構造の再編成")
        print("=" * 60)
        reorganize_docs(str(docs_dir), args.dry_run)

        # ステップ3: 元ファイルの削除
        if not args.dry_run:
            print("\n" + "=" * 60)
            print("ステップ 3/3: 元ファイルの削除")
            print("=" * 60)
            remove_original_files(str(docs_dir), args.dry_run)

        print("\n" + "=" * 60)
        print("すべての処理が完了しました！")
        print("=" * 60)

        if not args.dry_run:
            print("\nまとめ:")
            print("  1. MDX互換性の問題を修正（テーブル、import文、コードブロック等）")
            print("  2. index.mdの階層構造に従ってファイルを再編成")
            print("  3. 元のファイル（番号なし）を削除して重複を回避")
            print("\n'npm run start-doc' を実行して結果を確認してください。")
        else:
            print("\n実際にファイルを移動するには --dry-run オプションなしで実行してください")


if __name__ == '__main__':
    main()
