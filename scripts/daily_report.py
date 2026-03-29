"""
daily_report.py

WordPress・note・X のメトリクスを取得し、短期目標とのギャップ分析を含む
デイリーレポートを生成する。

使い方：
    python3 scripts/daily_report.py

出力：
    strategy/daily_report.md          （最新レポート・上書き）
    strategy/daily_report_history/YYYY-MM-DD.md  （日付別履歴）

ログは logs/fetch_metrics.log に出力される（fetch_metrics 共通）。
"""

import sys
import logging
from pathlib import Path
from datetime import date, datetime

# fetch_metrics モジュールを同ディレクトリから読み込む
sys.path.insert(0, str(Path(__file__).parent))
from fetch_metrics import (
    fetch_wordpress,
    fetch_note,
    fetch_x,
    update_metrics_md,
    logger,
    PROJECT_ROOT,
)

# ─── 出力パス ────────────────────────────────────────────

REPORT_FILE     = PROJECT_ROOT / "strategy" / "daily_report.md"
REPORT_HIST_DIR = PROJECT_ROOT / "strategy" / "daily_report_history"

# ─── 短期目標（2026-04-30） ──────────────────────────────

GOALS = {
    "deadline":            date(2026, 4, 30),
    "wordpress_articles":  15,
    "wordpress_pv":        5_000,
    "note_paid_articles":  10,
    "note_sales_yen":      50_000,  # note APIでは取得不可・手動入力用
    "x_followers":         500,
}

# テーマ連動記事はこの日以降に公開されたもの
THEME_START_DATE = "2026-03-18"

# ─── ヘルパー ────────────────────────────────────────────

def days_remaining() -> int:
    return max(0, (GOALS["deadline"] - date.today()).days)


def status_flag(current: float, goal: float, days_left: int, daily_rate: float) -> str:
    """現ペースを維持した場合の達成見込みで判定"""
    if goal <= 0:
        return "✅ 順調"
    projected = current + daily_rate * days_left
    ratio = projected / goal
    if ratio >= 1.0:
        return "✅ 順調"
    elif ratio >= 0.6:
        return "⚠️ 要加速"
    else:
        return "🔴 危機"


def count_theme_articles(posts: list) -> int:
    """THEME_START_DATE 以降に公開された記事数をカウント"""
    return sum(1 for p in posts if p.get("date", "") >= THEME_START_DATE)


def total_pv(posts: list) -> int:
    total = 0
    for p in posts:
        v = p.get("views", "N/A")
        if isinstance(v, int):
            total += v
        elif isinstance(v, str) and v.isdigit():
            total += int(v)
    return total


def elapsed_days() -> int:
    """プロジェクト開始（THEME_START_DATE）からの経過日数"""
    start = date.fromisoformat(THEME_START_DATE)
    return max(1, (date.today() - start).days)


def daily_rate(current: float) -> float:
    return current / elapsed_days()


# ─── レポート生成 ────────────────────────────────────────

def build_report(wp: dict, note_data: dict, x: dict, today_str: str) -> str:
    lines = [f"# デイリーレポート（{today_str}）\n"]

    d_left = days_remaining()
    elapsed = elapsed_days()
    deadline_str = GOALS["deadline"].strftime("%Y-%m-%d")

    lines.append(f"> 短期目標締め切り：{deadline_str}　残り {d_left} 日　経過 {elapsed} 日\n")

    # ── 1. 現状スナップショット ──────────────────────────
    lines.append("## 1. 現状スナップショット\n")

    # WordPress
    if wp["error"]:
        lines.append(f"- **WordPress** 取得エラー：{wp['error']}\n")
        theme_count = 0
        pv_total = 0
    else:
        theme_count = count_theme_articles(wp["posts"])
        pv_total    = total_pv(wp["posts"])
        pv_label    = str(pv_total) if wp["pv_available"] else "未計測（PVCプラグイン導入後に蓄積）"
        lines.append("### WordPress\n")
        lines.append(f"- テーマ連動記事数：{theme_count} 本（全公開記事 {wp['total_posts']} 本）")
        lines.append(f"- 累計PV（計測分）：{pv_label}\n")
        lines.append("| タイトル | 公開日 | PV |")
        lines.append("|--------|--------|----|")
        for p in sorted(wp["posts"], key=lambda x: x["date"], reverse=True):
            if p["date"] >= THEME_START_DATE:
                lines.append(f"| {p['title']} | {p['date']} | {p['views']} |")
        lines.append("")

    # note
    if note_data["error"]:
        lines.append(f"- **note** 取得エラー：{note_data['error']}\n")
        paid_count = 0
        note_views = 0
        note_likes = 0
    else:
        paid = [a for a in note_data["articles"] if a["is_paid"]]
        paid_count  = len(paid)
        note_views  = sum(a["views"] for a in note_data["articles"])
        note_likes  = sum(a["likes"] for a in note_data["articles"])
        lines.append("### note\n")
        lines.append(f"- 有料記事数：{paid_count} 本")
        lines.append(f"- 累計ビュー：{note_views}")
        lines.append(f"- 累計スキ：{note_likes}")
        lines.append(f"- 売上：手動入力が必要（note APIでは取得不可）\n")
        if paid:
            lines.append("| タイトル | 価格 | ビュー | スキ |")
            lines.append("|--------|------|--------|------|")
            for a in paid:
                lines.append(f"| {a['title']} | {a['price']}円 | {a['views']} | {a['likes']} |")
            lines.append("")

    # X
    followers = None
    if x["error"]:
        lines.append(f"- **X** {x['error']}\n")
    else:
        followers = x["followers"] or 0
        lines.append("### X\n")
        lines.append(f"- フォロワー：{followers} 人\n")
        if x["top_tweets"]:
            lines.append("**インプレッション TOP5（全期間）**\n")
            lines.append("| 日付 | 概要 | インプレ | いいね | RT |")
            lines.append("|------|------|---------|-------|----|")
            for t in x["top_tweets"][:5]:
                lines.append(
                    f"| {t['created_at']} | {t['text']} | {t['impressions']} | {t['likes']} | {t['retweets']} |"
                )
            lines.append("")

    # ── 2. 目標ギャップ分析 ──────────────────────────────
    lines.append("## 2. 目標ギャップ分析\n")
    lines.append("| 指標 | 目標 | 現在 | 残り | 必要ペース(/日) | 現ペース(/日) | 判定 |")
    lines.append("|------|------|------|------|----------------|--------------|------|")

    def row(label, goal, current, unit=""):
        rate_now  = daily_rate(current)
        rate_need = (goal - current) / d_left if d_left > 0 else float("inf")
        flag      = status_flag(current, goal, d_left, rate_now)
        rate_need_str = f"{rate_need:.1f}{unit}" if rate_need != float("inf") else "—"
        rate_now_str  = f"{rate_now:.1f}{unit}"
        return f"| {label} | {goal}{unit} | {current}{unit} | {max(0, goal - current)}{unit} | {rate_need_str} | {rate_now_str} | {flag} |"

    lines.append(row("WordPress 記事数",  GOALS["wordpress_articles"],  theme_count,          "本"))
    lines.append(row("WordPress PV",      GOALS["wordpress_pv"],        pv_total,             "回"))
    lines.append(row("note 有料記事数",   GOALS["note_paid_articles"],  paid_count,           "本"))
    lines.append(f"| note 売上 | {GOALS['note_sales_yen']:,}円 | 手動入力 | — | — | — | — |")
    lines.append(row("X フォロワー",      GOALS["x_followers"],         followers or 0,       "人"))
    lines.append("")

    # ── 3. ボトルネック ──────────────────────────────────
    lines.append("## 3. ボトルネック\n")

    # WordPress
    if theme_count < GOALS["wordpress_articles"] * 0.5:
        wp_bottle = "テーマ連動記事が不足。SEO母数が少なく、全媒体への流入が限られている。記事制作速度を上げることが最優先。"
    elif pv_total < GOALS["wordpress_pv"] * 0.3:
        wp_bottle = "記事数はあるが PV が伸びていない。X からの誘導強化と、既存記事のタイトル・導線の見直しを検討。"
    else:
        wp_bottle = "現ペースを維持。note への導線設置状況を定期確認すること。"
    lines.append(f"**WordPress**　{wp_bottle}\n")

    # note
    if note_views == 0 or note_views < 20:
        note_bottle = "ビュー数が極めて少ない。note 単体の問題ではなく、上流（X・WordPress）からの流入不足が根本原因。"
    elif paid_count < GOALS["note_paid_articles"] * 0.5:
        note_bottle = "流入はあるが有料記事の本数が足りない。制作ペースを週1〜2本に上げること。"
    else:
        note_bottle = "本数・流入ともに増加中。購入率の改善（タイトル・価格・導線）に注力。"
    lines.append(f"**note**　{note_bottle}\n")

    # X
    if followers is not None:
        x_rate = daily_rate(followers)
        x_needed = (GOALS["x_followers"] - followers) / d_left if d_left > 0 else float("inf")
        if x_rate < x_needed * 0.5:
            x_bottle = "フォロワー成長が目標ペースを大きく下回っている。刺さる投稿型（問い→構造化）の反復と、リプライによるリーチ拡大が必要。"
        elif x_rate < x_needed:
            x_bottle = "成長しているが目標ペースには届いていない。価値提供投稿の比率を上げ、宣伝比率を下げること。"
        else:
            x_bottle = "現ペースを維持。いいね・RT からフォローに繋げる設計（固定ポスト・プロフィール）を確認。"
        lines.append(f"**X**　{x_bottle}\n")

    # ── 4. 導線の状態 ────────────────────────────────────
    lines.append("## 4. 導線の状態\n")
    lines.append("| 導線 | 評価 | 状態 |")
    lines.append("|------|------|------|")

    x_to_wp   = "△" if (followers or 0) < 100 else "○"
    wp_to_note = "△" if theme_count < 5 else "○"
    note_conv  = "✕" if note_views < 10 else ("△" if note_views < 50 else "○")

    lines.append(f"| X → WordPress | {x_to_wp} | フォロワー {followers or 0} 人。クリック誘導は設置済みだが母数不足。 |")
    lines.append(f"| WordPress → note | {wp_to_note} | テーマ記事 {theme_count} 本。導線設置状況を要確認。 |")
    lines.append(f"| note → 購入 | {note_conv} | ビュー数 {note_views}。流入が少ない段階。 |")
    lines.append("")

    # ── 5. 今日の推奨アクション ──────────────────────────
    lines.append("## 5. 今日の推奨アクション\n")

    actions_p1 = []
    actions_p2 = []
    actions_p3 = []

    # WordPress 記事不足
    wp_rate_now  = daily_rate(theme_count)
    wp_rate_need = (GOALS["wordpress_articles"] - theme_count) / d_left if d_left > 0 else 0
    if wp_rate_now < wp_rate_need:
        actions_p1.append("WordPress記事を執筆する（目標ペース：週3本）。テーマ軸「思考を取り戻す仕事術」に直結する内容のみ。")

    # X フォロワー不足
    if followers is not None:
        x_rate_now  = daily_rate(followers)
        x_rate_need = (GOALS["x_followers"] - followers) / d_left if d_left > 0 else 0
        if x_rate_now < x_rate_need * 0.8:
            actions_p1.append("Xに「問い→構造化」型の投稿を1〜2本投稿する（高インプレッション型の反復）。")
            actions_p1.append("「副業日記」型の活動記録を投稿する（透明性・正直な数字が鍵）。")
        else:
            actions_p2.append("X投稿の質を維持。宣伝比率が25%以下になっているか確認する。")

    # note 記事不足
    note_rate_now  = daily_rate(paid_count)
    note_rate_need = (GOALS["note_paid_articles"] - paid_count) / d_left if d_left > 0 else 0
    if note_rate_now < note_rate_need:
        actions_p2.append("note有料記事の執筆を進める（目標ペース：週1〜2本）。WordPress記事の「再現性」部分の深掘り版を作る。")

    # リプライ施策
    actions_p3.append("関連アカウントへの質の高いリプライを2〜3件行い、インプレッションを拡大する。")
    actions_p3.append("metrics.md を確認し、PV・ビューの変化があれば CLAUDE.md の現状数値を更新する。")

    if actions_p1:
        lines.append("🔴 **P1（今日必ずやる）**")
        for a in actions_p1:
            lines.append(f"- {a}")
        lines.append("")

    if actions_p2:
        lines.append("🟡 **P2（できればやる）**")
        for a in actions_p2:
            lines.append(f"- {a}")
        lines.append("")

    if actions_p3:
        lines.append("🟢 **P3（余裕があれば）**")
        for a in actions_p3:
            lines.append(f"- {a}")
        lines.append("")

    # ── フッター ──────────────────────────────────────────
    lines.append("---")
    lines.append(f"*生成日時：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}　by daily_report.py*")

    return "\n".join(lines)


# ─── レポート保存 ────────────────────────────────────────

def save_report(content: str):
    today = datetime.now().strftime("%Y-%m-%d")

    # 最新レポート上書き
    logger.info(f"[daily_report] {REPORT_FILE} を上書き中...")
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("[daily_report] 上書き完了")

    # 履歴保存
    REPORT_HIST_DIR.mkdir(parents=True, exist_ok=True)
    hist_file = REPORT_HIST_DIR / f"{today}.md"
    action = "上書き" if hist_file.exists() else "新規作成"
    logger.info(f"[daily_report_history] {hist_file.name} を{action}中...")
    with open(hist_file, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"[daily_report_history] {action}完了")


# ─── メイン ──────────────────────────────────────────────

def main():
    logger.info("=" * 50)
    logger.info("デイリーレポート生成 開始")
    logger.info("=" * 50)

    today_str = datetime.now().strftime("%Y-%m-%d")

    logger.info("[step 1/3] メトリクス取得中...")
    wp        = fetch_wordpress()
    note_data = fetch_note()
    x         = fetch_x()

    logger.info("[step 2/3] metrics.md を更新中...")
    try:
        update_metrics_md(wp, note_data, x)
    except Exception as e:
        logger.error(f"metrics.md の更新に失敗しました: {e}")

    logger.info("[step 3/3] デイリーレポートを生成中...")
    report = build_report(wp, note_data, x, today_str)
    save_report(report)

    logger.info("=" * 50)
    logger.info("デイリーレポート生成 完了")
    logger.info(f"  → {REPORT_FILE}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
