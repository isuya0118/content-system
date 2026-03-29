#!/bin/bash
# daily_batch.sh
#
# 毎朝7時に cron から実行するバッチスクリプト。
# メトリクス取得 + デイリーレポート生成を行う。
#
# cron 設定（Ubuntu）:
#   crontab -e
#   0 7 * * * /path/to/content-system/scripts/daily_batch.sh >> /path/to/content-system/logs/cron.log 2>&1

set -euo pipefail

# スクリプトのディレクトリからプロジェクトルートを特定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily_batch 開始"
echo "========================================"

# Python コマンドを確認（python3 優先）
PYTHON=$(command -v python3 || command -v python)
if [ -z "${PYTHON}" ]; then
    echo "[ERROR] Python が見つかりません。インストールしてください。"
    exit 1
fi
echo "Python: ${PYTHON} ($(${PYTHON} --version))"

# 仮想環境があれば有効化（venv がある場合）
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
    echo "仮想環境を有効化しました"
fi

# デイリーレポート生成（fetch_metrics も内部で実行される）
echo "デイリーレポートを生成中..."
${PYTHON} scripts/daily_report.py

echo "[$(date '+%Y-%m-%d %H:%M:%S')] daily_batch 完了"
echo "========================================"
