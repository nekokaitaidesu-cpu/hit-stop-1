import streamlit as st
import streamlit.components.v1 as components

# ページ設定だっち
st.set_page_config(page_title="Hit Stop & Gravity Othello", layout="wide")

st.title("🍄 重力オセロ：ヒットストップ体験")
st.write("黒丸（●）を掴んで、白丸（○）に投げつけてみて！ぶつかると「ヒットストップ」するっち！😊")

# ゲームのHTML/JSコンポーネント
# Streamlit上で滑らかに動かすために、CanvasとJavaScriptを使うっち
html_code = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background-color: #f0f2f6; display: flex; justify-content: center; align-items: center; height: 100vh; }
    canvas { background-color: #262730; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
</style>
</head>
<body>
<canvas id="gameCanvas" width="800" height="500"></canvas>
<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    // パラメータ設定
    const GRAVITY = 0.5;
    const FRICTION = 0.98;
    const BOUNCE = 0.7;
    const HIT_STOP_DURATION = 15; // フレーム数（ヒットストップの長さ）
    const SHAKE_INTENSITY = 10;   // シェイクの激しさ

    // オブジェクトの状態
    let black = { x: 100, y: 100, vx: 0, vy: 0, radius: 30, isDragging: false };
    let white = { x: 600, y: 250, baseX: 600, baseY: 250, radius: 30, color: 'white' };
    
    // インタラクション用
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    let lastMouseX = 0;
    let lastMouseY = 0;

    // 演出用
    let hitStopTimer = 0;
    let shakeTimer = 0;
    let particles = [];

    // エフェクトパーティクルクラス
    class Particle {
        constructor(x, y) {
            this.x = x;
            this.y = y;
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 5 + 2;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.life = 1.0;
            this.decay = Math.random() * 0.05 + 0.02;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.life -= this.decay;
        }
        draw(ctx) {
            ctx.globalAlpha = this.life;
            ctx.fillStyle = '#FFD700'; // 金色の火花
            ctx.beginPath();
            ctx.arc(this.x, this.y, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    // マウスイベント
    canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        // 黒丸との距離
        const dist = Math.hypot(mx - black.x, my - black.y);
        if (dist < black.radius * 2) { // 判定を少し大きめに
            black.isDragging = true;
            dragOffsetX = black.x - mx;
            dragOffsetY = black.y - my;
            black.vx = 0;
            black.vy = 0;
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (black.isDragging) {
            black.x = mx + dragOffsetX;
            black.y = my + dragOffsetY;
            
            // 投げるための速度計算
            black.vx = (mx - lastMouseX) * 0.5; // 感度調整
            black.vy = (my - lastMouseY) * 0.5;
        }
        lastMouseX = mx;
        lastMouseY = my;
    });

    canvas.addEventListener('mouseup', () => {
        if (black.isDragging) {
            black.isDragging = false;
        }
    });

    // メインループ
    function update() {
        // --- ヒットストップ中の処理 ---
        if (hitStopTimer > 0) {
            hitStopTimer--;
            
            // 白丸をシェイクさせる（横揺れ）
            // ヒットストップ中は物理演算を止めるのがポイント！
            if (hitStopTimer > 0) {
                const shakeX = (Math.random() - 0.5) * SHAKE_INTENSITY;
                const shakeY = (Math.random() - 0.5) * SHAKE_INTENSITY * 0.2; // 縦は控えめに
                white.x = white.baseX + shakeX;
                white.y = white.baseY + shakeY;
            } else {
                white.x = white.baseX;
                white.y = white.baseY;
            }
            
            draw();
            requestAnimationFrame(update);
            return; // ここで物理更新をスキップしてリターン
        }

        // --- 物理更新 ---
        
        if (!black.isDragging) {
            // 重力
            black.vy += GRAVITY;
            // 摩擦（空気抵抗）
            black.vx *= FRICTION;
            black.vy *= FRICTION;

            // 位置更新
            black.x += black.vx;
            black.y += black.vy;

            // 壁の跳ね返り
            if (black.x + black.radius > canvas.width) {
                black.x = canvas.width - black.radius;
                black.vx *= -BOUNCE;
            } else if (black.x - black.radius < 0) {
                black.x = black.radius;
                black.vx *= -BOUNCE;
            }
            if (black.y + black.radius > canvas.height) {
                black.y = canvas.height - black.radius;
                black.vy *= -BOUNCE;
            } else if (black.y - black.radius < 0) {
                black.y = black.radius;
                black.vy *= -BOUNCE;
            }
        }

        // --- 衝突判定（黒丸 vs 白丸） ---
        const dx = black.x - white.x;
        const dy = black.y - white.y;
        const distance = Math.hypot(dx, dy);
        const minDist = black.radius + white.radius;

        if (distance < minDist) {
            // 衝突発生！
            
            // 1. ヒットストップ開始
            hitStopTimer = HIT_STOP_DURATION;

            // 2. エフェクト発生（パーティクル）
            for(let i=0; i<15; i++) {
                particles.push(new Particle(
                    black.x + (dx/distance) * black.radius, // 接触点付近
                    black.y + (dy/distance) * black.radius
                ));
            }

            // 3. 反発処理（物理的に跳ね返す）
            const angle = Math.atan2(dy, dx);
            const speed = Math.sqrt(black.vx**2 + black.vy**2);
            // 相手に当たったら少し跳ね返る
            black.vx = Math.cos(angle) * (speed * 0.8 + 5); 
            black.vy = Math.sin(angle) * (speed * 0.8 + 5);
            
            // 埋まり防止
            const overlap = minDist - distance;
            black.x += Math.cos(angle) * overlap;
            black.y += Math.sin(angle) * overlap;
        }

        // パーティクル更新
        particles = particles.filter(p => p.life > 0);
        particles.forEach(p => p.update());

        draw();
        requestAnimationFrame(update);
    }

    // 描画処理
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 床（グリッド）
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=100) {
            ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i, canvas.height); ctx.stroke();
        }
        for(let i=0; i<canvas.height; i+=100) {
            ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width, i); ctx.stroke();
        }

        // 白丸（相手）
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.arc(white.x, white.y, white.radius, 0, Math.PI * 2);
        ctx.fill();
        // 白丸の縁取り
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 黒丸（自分）
        ctx.fillStyle = 'black';
        ctx.beginPath();
        ctx.arc(black.x, black.y, black.radius, 0, Math.PI * 2);
        ctx.fill();
        // 黒丸のハイライト（立体感）
        ctx.fillStyle = '#555';
        ctx.beginPath();
        ctx.arc(black.x - 10, black.y - 10, 5, 0, Math.PI * 2);
        ctx.fill();

        // エフェクト描画
        // ヒット時のみ表示される衝撃波リング
        if (hitStopTimer > 0) {
            ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
            ctx.lineWidth = 5;
            ctx.beginPath();
            ctx.arc(
                (black.x + white.x) / 2, 
                (black.y + white.y) / 2, 
                black.radius + 20 + (HIT_STOP_DURATION - hitStopTimer) * 2, 
                0, Math.PI * 2
            );
            ctx.stroke();
        }

        // パーティクル
        particles.forEach(p => p.draw(ctx));
    }

    update();
</script>
</body>
</html>
"""

# HTMLを埋め込む（高さはCanvasサイズ+余白）
components.html(html_code, height=600)

st.write("### 使い方だっち")
st.write("1. **掴む**: 黒い石（●）をマウスでドラッグするっち。")
st.write("2. **投げる**: ドラッグの勢いをつけて離すと飛んでいくっち！")
st.write("3. **体験**: 白い石（○）にぶつかった瞬間、画面が一瞬止まる（ヒットストップ）のを感じてね！😊")
