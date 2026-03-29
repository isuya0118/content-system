"""
fetch_metrics.py

WordPress・note・X の運用数値を自動取得し、
strategy/metrics.md を更新するスクリプト。

使い方：
    python3 scripts/fetch_metrics.py

必要な環境変数（.env ファイルに記載）：
    WP_BASE_URL      ... WordPressサイトのURL
    NOTE_CREATOR     ... noteのクリエイターID
    X_USERNAME       ... XのユーザーID（@なし）
    X_BEARER_TOKEN   ... X API v2 Bearer Token（X のみ必須）

WordPress と note は認証なしで取得可能。
ログは logs/fetch_metrics.log に出力される。
"""

import os
import re
import logging
import requests
from datetime import datetime
from pathlib import Path

# ─── パス定義 ───────────────────────────────────────────

PROJECT_ROOT     = Path(__file__).parent.parent
METRICS_FILE     = PROJECT_ROOT / "strategy" / "metrics.md"
METRICS_HIST_DIR = PROJECT_ROOT / "strategy" / "metrics_history"
ENV_FILE         = PROJECT_ROOT / ".env"
LOG_FILE         = PROJECT_ROOT / "logs" / "fetch_metrics.log"

# ─── ログ設定 ───────────────────────────────────────────

LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ─── .env 読み込み ─────────────────────────────────────

def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
        logger.info(".env の読み込み完了")
    else:
        logger.warning(".env ファイルが見つかりません。環境変数から設定を読み込みます。")

load_env()

# ─── 設定（.env から読み込み） ──────────────────────────

WP_BASE_URL  = os.environ.get("WP_BASE_URL",  "https://isuya0118.com")
NOTE_CREATOR = os.environ.get("NOTE_CREATOR", "seminomise")
X_USERNAME   = os.environ.get("X_USERNAME",   "isuya0118")

# ─── WordPress ─────────────────────────────────────────

def fetch_wordpress_pv(post_id: int) -> int:
    """
    Post Views Counter プラグインの専用エンドポイントから PV を取得する。
    エンドポイント: /wp-json/post-views-counter/get-post-views/{id}
    取得できない場合は -1 を返す。
    """
    url = f"{WP_BASE_URL}/wp-json/post-views-counter/get-post-views/{post_id}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # レスポンスが数値の場合（PVC が直接整数を返す）
            if isinstance(data, (int, float)):
                return int(data)
            # レスポンスがオブジェクトの場合
            if isinstance(data, dict):
                for key in ("views_count", "post_views_count", "views"):
                    if key in data:
                        return int(data[key])
        return -1
    except Exception:
        return -1


def fetch_wordpress() -> dict:
    """
    WordPress REST API から公開記事一覧を取得する。
    PV は Post Views Counter プラグインの専用エンドポイントから取得する。
    プラグインが未導入の場合は "N/A" を表示する。
    """
    result = {"posts": [], "total_posts": 0, "pv_available": False, "error": None}
    url = f"{WP_BASE_URL}/wp-json/wp/v2/posts"
    logger.info(f"[WordPress] 取得開始 → {url}")
    try:
        resp = requests.get(
            url,
            params={"per_page": 100, "status": "publish", "_fields": "id,title,date,link,slug"},
            timeout=10,
        )
        logger.info(f"[WordPress] HTTP {resp.status_code}")
        resp.raise_for_status()
        posts = resp.json()
        result["total_posts"] = int(resp.headers.get("X-WP-Total", len(posts)))

        # Post Views Counter プラグインの動作確認（最初の記事でテスト）
        pvc_available = False
        if posts:
            test_pv = fetch_wordpress_pv(posts[0]["id"])
            pvc_available = test_pv >= 0
            if pvc_available:
                result["pv_available"] = True
                logger.info("[WordPress] Post Views Counter エンドポイント確認済み")
            else:
                logger.warning("[WordPress] Post Views Counter エンドポイントに接続できません。PV は N/A になります。")

        parsed = []
        for p in posts:
            if pvc_available:
                views = fetch_wordpress_pv(p["id"])
                views = views if views >= 0 else "N/A"
            else:
                views = "N/A"
            parsed.append({
                "id":    p["id"],
                "title": re.sub(r"<[^>]+>", "", p["title"]["rendered"]),
                "date":  p["date"][:10],
                "link":  p["link"],
                "slug":  p["slug"],
                "views": views,
            })
        result["posts"] = parsed
        logger.info(f"[WordPress] 取得成功 → 公開記事数: {result['total_posts']} 本 / PV: {'取得可' if result['pv_available'] else 'N/A（プラグイン未導入）'}")
    except requests.RequestException as e:
        result["error"] = str(e)
        logger.error(f"[WordPress] 取得失敗 → {e}")
    return result


# ─── note ──────────────────────────────────────────────

def fetch_note() -> dict:
    result = {"articles": [], "error": None}
    url = f"https://note.com/api/v2/creators/{NOTE_CREATOR}/contents"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; content-system/1.0)"}
    logger.info(f"[note] 取得開始 → クリエイター: {NOTE_CREATOR}")
    page = 1
    try:
        while True:
            logger.info(f"[note] ページ {page} を取得中...")
            resp = requests.get(url, params={"kind": "note", "page": page}, headers=headers, timeout=10)
            logger.info(f"[note] HTTP {resp.status_code}（ページ {page}）")
            resp.raise_for_status()
            data = resp.json().get("data", {})
            contents = data.get("contents", [])
            if not contents:
                logger.info(f"[note] ページ {page} にコンテンツなし → 終了")
                break
            for item in contents:
                result["articles"].append({
                    "title":     item.get("name", ""),
                    "price":     item.get("price", 0),
                    "views":     item.get("readCount", 0),
                    "likes":     item.get("likeCount", 0),
                    "is_paid":   item.get("price", 0) > 0,
                    "published": item.get("publishAt", "")[:10] if item.get("publishAt") else "",
                    "url":       f"https://note.com/{NOTE_CREATOR}/n/{item.get('key', '')}",
                })
            logger.info(f"[note] ページ {page} 取得完了 → {len(contents)} 件")
            if not data.get("isLastPage", True):
                page += 1
            else:
                break
        paid_count = len([a for a in result["articles"] if a["is_paid"]])
        logger.info(f"[note] 取得成功 → 全記事: {len(result['articles'])} 本 / 有料: {paid_count} 本")
    except requests.RequestException as e:
        result["error"] = str(e)
        logger.error(f"[note] 取得失敗（ページ {page}）→ {e}")
    return result


# ─── X (Twitter) ───────────────────────────────────────

def fetch_x() -> dict:
    result = {"followers": None, "recent_tweets": [], "top_tweets": [], "error": None}
    bearer = os.environ.get("X_BEARER_TOKEN")
    if not bearer:
        result["error"] = "X_BEARER_TOKEN が未設定です。.env に追記してください。"
        logger.warning(f"[X] {result['error']}")
        return result

    headers = {"Authorization": f"Bearer {bearer}"}
    logger.info(f"[X] 取得開始 → ユーザー: {X_USERNAME}")
    try:
        # ユーザー情報（フォロワー数）
        logger.info("[X] ユーザー情報を取得中...")
        resp = requests.get(
            f"https://api.twitter.com/2/users/by/username/{X_USERNAME}",
            headers=headers,
            params={"user.fields": "public_metrics"},
            timeout=10,
        )
        logger.info(f"[X] ユーザー情報 HTTP {resp.status_code}")
        resp.raise_for_status()
        user = resp.json().get("data", {})
        metrics = user.get("public_metrics", {})
        result["followers"] = metrics.get("followers_count")
        user_id = user.get("id")
        logger.info(f"[X] ユーザー情報取得成功 → フォロワー: {result['followers']} 人 / user_id: {user_id}")

        # 全ツイート取得（ページネーション）→ 直近20件 + 全体TOP10 を生成
        if user_id:
            all_tweets = []
            next_token = None
            page = 1
            logger.info("[X] 全ツイートを取得中（ページネーション）...")
            while True:
                params = {
                    "max_results": 100,
                    "tweet.fields": "public_metrics,created_at",
                    "exclude": "retweets,replies",
                }
                if next_token:
                    params["pagination_token"] = next_token
                resp2 = requests.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets",
                    headers=headers,
                    params=params,
                    timeout=10,
                )
                logger.info(f"[X] ツイート取得 HTTP {resp2.status_code}（ページ {page}）")
                resp2.raise_for_status()
                body = resp2.json()
                tweets = body.get("data", [])
                if not tweets:
                    break
                for t in tweets:
                    pm = t.get("public_metrics", {})
                    all_tweets.append({
                        "id":          t["id"],
                        "text":        t["text"][:60] + "..." if len(t["text"]) > 60 else t["text"],
                        "created_at":  t.get("created_at", "")[:10],
                        "impressions": pm.get("impression_count", 0),
                        "likes":       pm.get("like_count", 0),
                        "retweets":    pm.get("retweet_count", 0),
                        "replies":     pm.get("reply_count", 0),
                        "url_clicks":  pm.get("url_link_clicks", 0),
                    })
                logger.info(f"[X] ページ {page} 取得完了 → {len(tweets)} 件（累計: {len(all_tweets)} 件）")
                next_token = body.get("meta", {}).get("next_token")
                if not next_token:
                    break
                page += 1

            # 直近20件（取得順 = 新しい順）
            result["recent_tweets"] = all_tweets[:20]
            # 全体インプレッション TOP10
            result["top_tweets"] = sorted(all_tweets, key=lambda t: t["impressions"], reverse=True)[:10]
            logger.info(f"[X] 全ツイート取得完了 → 合計: {len(all_tweets)} 件 / 直近20件・TOP10 を集計")
        else:
            logger.warning("[X] user_id が取得できなかったためツイート取得をスキップ")

    except requests.RequestException as e:
        result["error"] = str(e)
        logger.error(f"[X] 取得失敗 → {e}")
    return result


# ─── スナップショット生成 ────────────────────────────────

def build_snapshot(wp: dict, note: dict, x: dict, today: str) -> str:
    """取得データをMarkdown文字列に変換して返す"""
    lines = [f"# メトリクス スナップショット（{today}）\n"]

    lines.append("## WordPress")
    if wp["error"]:
        lines.append(f"- 取得エラー：{wp['error']}")
    else:
        pv_note = "（PV取得可）" if wp.get("pv_available") else "（PV: N/A ※Post Views Counterプラグイン未導入）"
        lines.append(f"- 公開記事数：{wp['total_posts']} 本 {pv_note}\n")
        lines.append("| タイトル | 公開日 | PV | URL |")
        lines.append("|--------|--------|----|-----|")
        for p in wp["posts"]:
            lines.append(f"| {p['title']} | {p['date']} | {p['views']} | {p['link']} |")
    lines.append("")

    lines.append("## note")
    if note["error"]:
        lines.append(f"- 取得エラー：{note['error']}")
    else:
        paid = [a for a in note["articles"] if a["is_paid"]]
        lines.append(f"- 有料記事数：{len(paid)} 本")
        lines.append(f"- 累計ビュー：{sum(a['views'] for a in note['articles'])}")
        lines.append(f"- 累計スキ：{sum(a['likes'] for a in note['articles'])}\n")
        lines.append("| タイトル | 価格 | ビュー | スキ |")
        lines.append("|--------|------|--------|------|")
        for a in note["articles"]:
            price = f"{a['price']}円" if a["price"] > 0 else "無料"
            lines.append(f"| {a['title']} | {price} | {a['views']} | {a['likes']} |")
    lines.append("")

    lines.append("## X")
    if x["error"]:
        lines.append(f"- {x['error']}")
    else:
        lines.append(f"- フォロワー：{x['followers']} 人\n")
        if x["recent_tweets"]:
            lines.append("### 直近20件")
            lines.append("")
            lines.append("| 日付 | 概要 | インプレ | いいね | RT | リプライ |")
            lines.append("|------|------|---------|-------|-----|--------|")
            for t in x["recent_tweets"]:
                lines.append(
                    f"| {t['created_at']} | {t['text']} | {t['impressions']} | {t['likes']} | {t['retweets']} | {t['replies']} |"
                )
            lines.append("")
        if x["top_tweets"]:
            lines.append("### インプレッション TOP10（全期間）")
            lines.append("")
            lines.append("| 日付 | 概要 | インプレ | いいね | RT | リプライ |")
            lines.append("|------|------|---------|-------|-----|--------|")
            for t in x["top_tweets"]:
                lines.append(
                    f"| {t['created_at']} | {t['text']} | {t['impressions']} | {t['likes']} | {t['retweets']} | {t['replies']} |"
                )
    lines.append("")

    return "\n".join(lines)


# ─── metrics.md 更新 ────────────────────────────────────

def update_metrics_md(wp: dict, note: dict, x: dict):
    today = datetime.now().strftime("%Y-%m-%d")
    snapshot = build_snapshot(wp, note, x, today)

    # metrics.md を最新状態で上書き
    logger.info(f"[metrics.md] {METRICS_FILE} を最新状態で上書き中...")
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        f.write(snapshot)
    logger.info("[metrics.md] 上書き完了")

    # 履歴ファイルに保存（同日は上書き、別日は新規作成）
    METRICS_HIST_DIR.mkdir(exist_ok=True)
    hist_file = METRICS_HIST_DIR / f"{today}.md"
    action = "上書き" if hist_file.exists() else "新規作成"
    logger.info(f"[metrics_history] {hist_file.name} を{action}中...")
    with open(hist_file, "w", encoding="utf-8") as f:
        f.write(snapshot)
    logger.info(f"[metrics_history] {action}完了")


# ─── メイン ────────────────────────────────────────────

def main():
    logger.info("=" * 50)
    logger.info("メトリクス取得処理 開始")
    logger.info("=" * 50)

    results = {}

    # WordPress
    wp = fetch_wordpress()
    results["wordpress"] = "SUCCESS" if not wp["error"] else "FAILED"

    # note
    note = fetch_note()
    results["note"] = "SUCCESS" if not note["error"] else "FAILED"

    # X
    x = fetch_x()
    results["x"] = "SUCCESS" if not x["error"] else "SKIPPED" if "未設定" in (x["error"] or "") else "FAILED"

    # metrics.md 更新
    try:
        update_metrics_md(wp, note, x)
        results["metrics_md"] = "SUCCESS"
    except Exception as e:
        results["metrics_md"] = "FAILED"
        logger.error(f"[metrics.md] 更新失敗 → {e}")

    # 処理結果サマリー
    logger.info("=" * 50)
    logger.info("処理結果サマリー")
    logger.info("=" * 50)
    for key, status in results.items():
        mark = "✅" if status == "SUCCESS" else "⚠️ " if status == "SKIPPED" else "❌"
        logger.info(f"  {mark} {key:<15} {status}")

    # 数値サマリー
    logger.info("-" * 50)
    if not wp["error"]:
        logger.info(f"  WordPress  公開記事数: {wp['total_posts']} 本")
    if not note["error"]:
        paid_count = len([a for a in note["articles"] if a["is_paid"]])
        logger.info(f"  note       有料記事: {paid_count} 本 / 全記事: {len(note['articles'])} 本")
    if not x["error"]:
        logger.info(f"  X          フォロワー: {x['followers']} 人")
    logger.info("=" * 50)
    logger.info("メトリクス取得処理 終了")


if __name__ == "__main__":
    main()
