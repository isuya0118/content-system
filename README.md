# content-system

WordPress・note・X を連動させたコンテンツ運用プロジェクト。
テーマ「思考を取り戻す仕事術」を軸に、記事制作・分析・改善を行う。

## メディアの役割

| メディア | 役割 | URL |
|---------|------|-----|
| WordPress | 無料記事でSEO資産を積み上げる | https://isuya0118.com/ |
| note | 有料記事で収益化する | https://note.com/seminomise |
| X | 認知拡大・流入獲得・反応検証 | https://x.com/isuya0118 |

## ディレクトリ構造

```
content-system/
├── CLAUDE.md                  # コンセプト・記事ルール・運用方針
├── workflow.md                # コンテンツ制作フロー（ideas→drafts→reviews→published）
│
├── strategy/
│   ├── roadmap.md             # 目標数値（短期・中期・長期）
│   ├── links.md               # 公開済みコンテンツURL一覧
│   ├── metrics.md             # 最新メトリクス（自動生成・日次更新）
│   ├── daily_report.md        # ギャップ分析レポート（自動生成・日次更新）
│   ├── metrics_history/       # メトリクス履歴（日付別）
│   └── daily_report_history/  # レポート履歴（日付別）
│
├── contents/
│   ├── 01_WordPress/
│   │   ├── ideas/             # 記事アイデア
│   │   ├── drafts/            # 執筆中
│   │   ├── reviews/           # レビュー待ち
│   │   └── published/         # 公開済み
│   ├── 02_note/               # （同上）
│   └── 03_X/                  # （同上）
│
├── scripts/
│   ├── fetch_metrics.py       # メトリクス取得スクリプト
│   ├── daily_report.py        # デイリーレポート生成スクリプト
│   ├── daily_batch.sh         # cronから呼ぶバッチスクリプト（毎朝7時）
│   └── requirements.txt       # Python依存パッケージ
│
├── .claude/skills/            # Claude Codeスキル定義
│   ├── analyze/               # /analyze：運用状況分析
│   ├── wordpress-article/     # /wordpress-article：WordPress記事作成
│   ├── note-article/          # /note-article：note記事作成
│   ├── x-post/                # /x-post：X投稿作成
│   └── review-content/        # /review-content：コンテンツレビュー
│
├── .env                       # 認証情報（gitignore済み）
└── .env.example               # 認証情報のテンプレート
```

## セットアップ

```bash
pip3 install -r scripts/requirements.txt
cp .env.example .env
# .env に認証情報を入力
```

## 日次バッチ（Ubuntu サーバー）

毎朝7時に自動でメトリクス取得＋レポート生成を行う。

```bash
# crontab -e に追加
0 7 * * * /path/to/content-system/scripts/daily_batch.sh >> /path/to/content-system/logs/cron.log 2>&1
```
