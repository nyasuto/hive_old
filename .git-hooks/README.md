# Hive Git Hooks

このディレクトリには、Hiveプロジェクトのgit hooksが含まれています。

## 📁 ファイル構成

- `pre-commit` - コミット前の品質チェックとルール検証
- `pre-push` - プッシュ前の最終検証（将来実装予定）

## 🚀 使用方法

### 自動セットアップ
```bash
make git-hooks    # git hooksを設定
make dev          # 開発環境全体をセットアップ（git hooks含む）
```

### 手動セットアップ
```bash
cp .git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## 🪝 現在のフック機能

### pre-commit
- **mainブランチ保護**: mainブランチへの直接コミットを禁止
- **ブランチ命名規則**: 規定のプレフィックス（feat/, fix/, docs/等）を強制
- **ファイル検証**: 
  - Python固有チェック（__pycache__, .pycファイル除外）
  - 大きなファイル警告（10MB以上）
  - 機密情報パターン検出
- **品質チェック**: `make quality`（lint, format, type-check）
- **テスト実行**: `make test`
- **Makefile構文チェック**: Makefile変更時の構文検証

## 📋 ブランチ命名規則

以下のプレフィックスが必要です：

- `feat/issue-X-feature-name` - 新機能
- `fix/issue-X-description` - バグ修正  
- `docs/X-description` - ドキュメント
- `refactor/X-description` - リファクタリング
- `test/X-description` - テスト
- `ci/X-description` - CI/CD
- `cicd/X-description` - CI/CD
- `perf/X-description` - パフォーマンス改善
- `security/X-description` - セキュリティ修正
- `deps/X-description` - 依存関係更新
- `claude/X-description` - Claude Code作業

## 🔧 トラブルシューティング

### フックが実行されない場合
```bash
# 実行権限を確認
ls -la .git/hooks/pre-commit

# 実行権限を付与
chmod +x .git/hooks/pre-commit
```

### 品質チェックに失敗する場合
```bash
# 手動で品質チェック
make quality

# 自動修正を試す
make quality-fix
```

### フックを一時的に無効化したい場合
```bash
# 一時的にスキップ（非推奨）
git commit --no-verify -m "message"
```

## 🔄 将来の拡張予定

### pre-push フック  
- プッシュ前の最終品質チェック
- テストカバレッジ閾値チェック
- リモートブランチとの同期確認

## 📚 参考

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [../beaver project git-hooks](../beaver/.git-hooks/) - 参考実装