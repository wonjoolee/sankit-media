#!/usr/bin/env bash
# 산킷 뉴스를 CI에서 만든다.  pipeline/news_ci.sh [출력폴더] [YYYY-MM-DD]
# 조용히 실패하지 않는다. 단계마다 표시를 남기고, 실패하면 그 자리에서 멈춘다.
set -euo pipefail

D="${2:-$(TZ=Asia/Seoul date +%F)}"
OUT="${1:-queue/$D/slot1}"

echo "::group::산킷 뉴스 빌드 $D -> $OUT"
echo "[0] KST $(TZ=Asia/Seoul date '+%F %H:%M')  UTC $(date -u '+%F %H:%M')"

echo "[1] 한글·이모지 글꼴 + ffmpeg"
NEED=""
fc-list | grep -q "Noto Sans CJK"     || NEED="$NEED fonts-noto-cjk"
fc-list | grep -qi "Noto Color Emoji" || NEED="$NEED fonts-noto-color-emoji"
command -v ffmpeg >/dev/null          || NEED="$NEED ffmpeg"
if [ -n "$NEED" ]; then
  for i in 1 2 3; do
    sudo apt-get update -qq && sudo apt-get install -y -qq $NEED && break
    echo "   설치 실패 ($i/3):$NEED"; sleep 20
  done
fi
fc-list | grep -q "Noto Sans CJK"      || { echo "::error::한글 글꼴 없음"; exit 1; }
fc-list | grep -qi "Noto Color Emoji"  || { echo "::error::이모지 글꼴 없음"; exit 1; }
echo "   ok"

echo "[2] pillow"
python -c "import PIL" 2>/dev/null || pip install -q pillow
python -c "import PIL; print('   pillow', PIL.__version__)"

echo "[3] playwright + chromium"
npm i -s playwright@1.56.1
npx -y playwright@1.56.1 install --with-deps chromium \
  || { echo "   --with-deps 실패(러너 OS 변경?) - 의존성 없이 다시"; npx -y playwright@1.56.1 install chromium; }
node -e "require('playwright').chromium.executablePath()" && echo "   ok"

echo "[4] ffmpeg"
command -v ffmpeg >/dev/null || { echo "::error::ffmpeg 없음"; exit 1; }
ffmpeg -version | head -1

echo "[5] 데이터 수집"
python pipeline/fetch_data.py || echo "   수집 실패 - 있는 데이터로 만든다"

echo "[6] 뉴스 제작"
mkdir -p "$OUT"
python pipeline/news_build.py "$OUT" "$D"

echo "[7] 결과 확인"
for f in 01.jpg reel.mp4 story.jpg threads.json post.json; do
  [ -s "$OUT/$f" ] || { echo "::error::$OUT/$f 없음"; exit 1; }
  echo "   $(printf '%-12s' "$f") $(stat -c%s "$OUT/$f") bytes"
done
echo "::endgroup::"
