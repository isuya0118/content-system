# Workflow

## 目的
このプロジェクトでは、WordPress・note・Xのコンテンツ制作を  
「思いつき」ではなく「工程」として管理する。

すべてのコンテンツは、以下の流れで運用する。

- ideas
- drafts
- reviews
- published

レビューを必ず通し、95点以上になったものだけを公開する。

---

## 基本方針

- テンプレートを使って初稿を作る
- 媒体ごとの criteria を使ってレビューする
- レビュー結果は review-template.md に沿って出力する
- 95点未満なら公開しない
- published に入るのは公開レベルに達したもののみ

---

## ディレクトリの役割

### ideas
記事・投稿のアイデア置き場。  
まだ本文を書いていない状態。

最低限、以下を記載する。
- 仮タイトル
- 想定ペルソナ
- 記事 / 投稿の目的
- 接続したい有料記事や無料記事

---

### drafts
本文を書き始めた状態。  
必ず templates 配下のテンプレートを使って初稿を作る。

---

### reviews
draft を criteria に沿ってレビューした結果を置く場所。  
review-template.md を使って出力する。

レビューでは必ず以下を明示する。
- 現在点数
- 95点未満の理由
- 修正すべきポイント
- 公開可否

---

### published
95点以上になり、公開済みまたは公開可能な状態のものを置く場所。  
必要に応じて公開URLを追記する。

---

## ファイル命名規則

### 基本ルール
すべてのファイルは以下で統一する。

`YYYY-MM-DD_slug.md`

例：
- `2026-03-24_ai-checklist-5.md`
- `2026-03-24_primary-sources-reading-8steps.md`
- `2026-03-24_hon-gyo-fukugyo-synergy.md`

### slug ルール
- 小文字英数字
- 単語はハイフン区切り
- 長すぎない
- 日本語ファイル名は使わない

---

## 媒体ごとの運用フロー

---

## WordPress

### 1. idea作成
`contents/01_WordPress/ideas/` に作成する。

記載内容：
- 仮タイトル
- ペルソナ
- 記事の役割（集客 / 信頼構築 / 導線）
- 接続先note

### 2. draft作成
`contents/99_template/wordpress-article.md` を使って
`contents/01_WordPress/drafts/` に初稿を作成する。

### 3. review実行
以下を使ってレビューする。
- `contents/99_criteria/wordpress-criteria.md`
- `contents/99_template/review-template.md`

レビュー結果は `contents/01_WordPress/reviews/` に保存する。

### 4. revise
95点未満なら、レビュー結果に従って `drafts/` の本文を修正する。
修正後は再レビューする。

### 5. publish
95点以上になったら `contents/01_WordPress/published/` に移動する。
公開後は必要に応じてURLを追記する。

---

## note

### 1. idea作成
`contents/02_note/ideas/` に作成する。

記載内容：
- 仮タイトル
- ペルソナ
- 価格
- 記事の役割（入口商品 / 本命商品 / アップセル）
- 主導線元（WordPress / X）

### 2. draft作成
`contents/99_template/note-article.md` を使って
`contents/02_note/drafts/` に初稿を作成する。

### 3. review実行
以下を使ってレビューする。
- `contents/99_criteria/note-criteria.md`
- `contents/99_template/review-template.md`

レビュー結果は `contents/02_note/reviews/` に保存する。

### 4. revise
95点未満なら、レビュー結果に従って `drafts/` の本文を修正する。
修正後は再レビューする。

### 5. publish
95点以上になったら `contents/02_note/published/` に移動する。
公開後は必要に応じてURLを追記する。

---

## X

### 1. idea作成
`contents/03_X/ideas/YYYY-MM-DD_slug.md` に作成する。

記載内容：
- 投稿の目的（いいね / リプ / 保存 / クリック）
- 狙うテーマ・切り口
- バズパターンの型（`strategy/x-buzz-patterns.md` を参照）
- 誘導先URL（ある場合）

### 2. draft作成
`contents/03_X/drafts/YYYY-MM-DD_slug.md` に初稿を作成する。

- `strategy/x-buzz-patterns.md` のチェックリストを参照しながら複数案（3〜10本）を作成する
- `contents/99_template/x-post.md` を使う

### 3. review実行
以下を使ってレビューする。
- `strategy/x-buzz-patterns.md`（バズ投稿チェックリスト）
- `contents/99_criteria/x-criteria.md`
- `contents/99_template/review-template.md`

レビュー結果は `contents/03_X/reviews/` に保存する。

### 4. revise
95点未満の投稿は修正する。
反応の弱そうなものは破棄してよい。

### 5. publish
実際に投稿したものは `contents/03_X/published/YYYY-MM-DD_posts.md` に記録する。
必要ならインプレ・いいね・クリックなどの結果も追記する。

---

## レビュー基準

### 共通ルール
- 95点以上のみ公開可
- 95点未満なら公開しない
- 「悪くない」ではなく「十分強いか」で判断する
- 迷ったら、ペルソナに対して本当に刺さるか / 売れるか / 満足するかで判断する

### WordPress固有ルール
- 文体はです・ます調に統一する（だ・である調は使わない）
- 本文の文字数は2,500〜3,500字を目安とする

### 媒体別
- WordPress：無料記事として有料級の価値があるか、有料noteへの導線が自然で強いか
- note：ペルソナに売れるか、購入後に満足してもらえるか
- X：伸びる可能性があるか、反応またはクリックを取りにいけるか

---

## 導線ルール

### WordPress → note
- 導線は1〜3箇所まで
- 冒頭直後（軽く）
- 興味が最大になる中盤（最重要）
- 記事末尾（回収）

### note → note
- 300円記事は入口商品
- 500円記事は本命商品
- 300円記事から500円記事へのアップセル導線を入れる

### X → WordPress / note
- 価値提供 3 : 宣伝 1 を維持する
- 宣伝投稿は「読まないと損する理由」を必ず入れる
- リプライでクリック補強する場合、URLは1つのリプにだけ付ける

---

## 運用上の注意

- 実績がないのに成功を語らない
- 自分語りを主役にしない
- 抽象論で終わらせない
- 「思考を取り戻す仕事術」の軸からズレない
- 今のアカウント規模や信頼残高に合わない売り方をしない

---

## 現在の運用方針

- WordPress：無料記事を蓄積し、SEO資産として育てる
- note：有料記事を販売し、収益化を担う
- X：認知拡大・流入獲得・反応検証を行う

優先順位：
1. 認知（X）
2. 信頼（WordPress）
3. 収益（note）

---

## 迷ったときの判断基準

### WordPress
- 単体で価値があるか
- それでも続きを読みたくなるか

### note
- 読者が買う理由があるか
- 読後に満足して行動を変えられるか

### X
- 最初の1行で止まるか
- 反応 / クリック / 拡散のどれを狙う投稿か明確か