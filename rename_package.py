#!/usr/bin/env python3
"""
リポジトリ全体でorganization名、タイトル、パッケージ名を置き換えるスクリプト
"""

import os
import sys
import json
import re
from pathlib import Path


# デフォルト値
DEFAULT_ORG = "procube-open"
DEFAULT_TITLE = "[Enter Title Here]"
DEFAULT_PACKAGE = "docusaurus-template"


def get_input_with_default(prompt: str, default: str) -> str:
    """
    デフォルト値を表示してユーザーに入力を求める
    """
    user_input = input(f"{prompt} (デフォルト: {default}): ").strip()
    return user_input if user_input else default


def replace_in_file(file_path: Path, replacements: dict[str, str]) -> bool:
    """
    ファイル内の文字列を置き換える
    
    Args:
        file_path: ファイルのパス
        replacements: 置き換え対象の辞書 {old: new}
    
    Returns:
        置き換えが行われた場合True
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 置き換えを実行
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # 変更があった場合のみファイルを書き込む
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"エラー: {file_path} の処理中にエラーが発生しました: {e}", file=sys.stderr)
        return False


def main():
    """
    メイン処理
    """
    print("=" * 60)
    print("リポジトリ設定置き換えツール")
    print("=" * 60)
    print()
    print("現在の設定:")
    print(f"  Organization: {DEFAULT_ORG}")
    print(f"  タイトル: {DEFAULT_TITLE}")
    print(f"  パッケージ名: {DEFAULT_PACKAGE}")
    print()
    print("新しい設定を入力してください（Enterでデフォルト値を使用）:")
    print()
    
    # ユーザー入力を取得
    new_org = get_input_with_default("Organization名", DEFAULT_ORG)
    new_title = get_input_with_default("タイトル", DEFAULT_TITLE)
    new_package = get_input_with_default("パッケージ名", DEFAULT_PACKAGE)
    
    print()
    print("=" * 60)
    print("置き換え内容の確認:")
    print(f"  Organization: {DEFAULT_ORG} → {new_org}")
    print(f"  タイトル: {DEFAULT_TITLE} → {new_title}")
    print(f"  パッケージ名: {DEFAULT_PACKAGE} → {new_package}")
    print("=" * 60)
    print()
    
    # 確認
    confirm = input("この内容で置き換えを実行しますか? (y/N): ").strip().lower()
    if confirm != 'y':
        print("キャンセルしました。")
        return
    
    print()
    print("置き換えを開始します...")
    print()
    
    # リポジトリのルートディレクトリを取得
    repo_root = Path(__file__).parent
    
    # 置き換えマップを作成
    replacements = {
        DEFAULT_ORG: new_org,
        DEFAULT_TITLE: new_title,
        DEFAULT_PACKAGE: new_package,
    }
    
    # 除外するディレクトリとファイル
    exclude_dirs = {
        '.git', 'node_modules', '.docusaurus', 'build', 
        '.docusaurus-template', '__pycache__', '.venv'
    }
    exclude_files = {'.DS_Store', 'package-lock.json'}
    
    # 処理対象の拡張子
    target_extensions = {
        '.py', '.json', '.md', '.ts', '.tsx', '.js', '.jsx',
        '.yaml', '.yml', '.sh', '.txt', '.css', '.jsonc'
    }
    
    modified_files = []
    
    # ファイルを再帰的に検索して置き換え
    for root, dirs, files in os.walk(repo_root):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # 除外ファイルをスキップ
            if file in exclude_files:
                continue
            
            file_path = Path(root) / file
            
            # 拡張子をチェック（拡張子なしのファイルも処理）
            if file_path.suffix in target_extensions or not file_path.suffix:
                try:
                    if replace_in_file(file_path, replacements):
                        rel_path = file_path.relative_to(repo_root)
                        modified_files.append(rel_path)
                        print(f"✓ {rel_path}")
                except Exception as e:
                    rel_path = file_path.relative_to(repo_root)
                    print(f"✗ {rel_path}: {e}", file=sys.stderr)
    
    print()
    print("=" * 60)
    print(f"置き換えが完了しました！ ({len(modified_files)}個のファイルを更新)")
    print("=" * 60)
    
    if modified_files:
        print()
        print("更新されたファイル:")
        for file_path in modified_files:
            print(f"  - {file_path}")


if __name__ == "__main__":
    main()
