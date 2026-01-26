import streamlit as st
import streamlit.components.v1 as components

# ページ設定（スマホで見やすいように広げる）
st.set_page_config(page_title="Hit Stop Othello Mobile", layout="wide")

st.title("🍄 重力オセロ：スマホ対応版")
st.write("スマホでも指でつかんで投げられるようになったっち！📱💨")

# ゲームのHTML/JSコンポーネント
html_code = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
    body { 
        margin: 0; 
        overflow: hidden; 
        background-color: #f0f2f6; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        height: 100vh;
        touch-action: none; /* スマホでのスクロール防止 */
    }
    canvas { 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        background-color: #262730;
        border-radius: 10px;
    }
</style>
</head>
<body>
<canvas id="gameCanvas"></canvas>
<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');

    // 画面サイズに合わせてキャンバスをリサイズする関数
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas(); // 初期実行

    // パラメータ設定
    const GRAVITY = 0.5;
    const FRICTION = 0.98;
    const BOUNCE = 0.7;
    const HIT_STOP_DURATION = 15;
    const SHAKE_INTENSITY = 10;

    // オブジェクトの状態（初期位置は画面中央あたりになるように調整）
    let black = { x: 100, y: 100, vx: 0, vy: 0, radius: 30, isDragging: false };
    let white = { x: 0, y: 0, baseX: 0, baseY: 0, radius: 30, color: 'white' };
    
    // 白丸の初期位置をセット（リサイズ対応のため関数化）
    function initPositions() {
        // 白丸を画面の右側・中央に配置
        white.baseX = window.innerWidth * 0.75;
        white.baseY = window.innerHeight * 0.5;
        white.x = white.baseX;
        white.y = white.baseY;
        
        // 黒丸を左側に
        black.x = window.innerWidth * 0.25;
        black.y = window.innerHeight * 0.5;
    }
    // 少し遅らせて初期化（キャンバスサイズ確定待ち）
    setTimeout(initPositions, 100);

    // インタラクション用
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    let lastMouseX = 0;
    let lastMouseY = 0;

    // 演出用
    let hitStopTimer = 0;
    let particles = [];

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
            ctx.fillStyle = '#FFD700';
            ctx.beginPath();
            ctx.arc(this.x, this.y, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    // --- 入力ハンドリング（マウス & タッチ両対応） ---

    function getPointerPos(e) {
        const rect = canvas.getBoundingClientRect();
        let clientX, clientY;
        
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        return {
            x: clientX - rect.left,
            y: clientY - rect.top
        };
    }

    function onDown(e) {
        // スマホでのスクロール等のデフォルト動作を防ぐ
        if(e.type === 'touchstart') e.preventDefault();
        
        const pos = getPointerPos(e);
        const dist = Math.hypot(pos.x - black.x, pos.y - black.y);
        
        // タッチ判定を少し甘くする（指は太いから）
        if (dist < black.radius * 2.5) { 
            black.isDragging = true;
            dragOffsetX = black.x - pos.x;
            dragOffsetY = black.y - pos.y;
            black.vx = 0;
            black.vy = 0;
            lastMouseX = pos.x;
            lastMouseY = pos.y;
        }
    }

    function onMove(e) {
        if(e.type === 'touchmove') e.preventDefault();

        if (black.isDragging) {
            const pos = getPointerPos(e);
            black.x = pos.x + dragOffsetX;
            black.y = pos.y + dragOffsetY;
            
            // 速度計算
            black.vx = (pos.x - lastMouseX) * 0.5;
            black.vy = (pos.y - lastMouseY) * 0.5;
            
            lastMouseX = pos.x;
            lastMouseY = pos.y;
        }
    }

    function onUp(e) {
        if (black.isDragging) {
            black.isDragging = false;
        }
    }

    // イベントリスナー登録
    canvas.addEventListener('mousedown', onDown);
    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseup', onUp);
    
    // スマホ用タッチイベント
    canvas.addEventListener('touchstart', onDown, {passive: false});
    canvas.addEventListener('touchmove', onMove, {passive: false});
    canvas.addEventListener('touchend', onUp);

    // メインループ
    function update() {
        if (hitStopTimer > 0) {
            hitStopTimer--;
            if (hitStopTimer > 0) {
                const shakeX = (Math.random() - 0.5) * SHAKE_INTENSITY;
                const shakeY = (Math.random() - 0.5) * SHAKE_INTENSITY * 0.2;
                white.x = white.baseX + shakeX;
                white.y = white.baseY + shakeY;
            } else {
                white.x = white.baseX;
                white.y = white.baseY;
            }
            draw();
            requestAnimationFrame(update);
            return;
        }

        if (!black.isDragging) {
            black.vy += GRAVITY;
            black.vx *= FRICTION;
            black.vy *= FRICTION;
            black.x += black.vx;
            black.y += black.vy;

            // 壁判定（画面端で跳ね返る）
            if (black.x + black.radius > canvas.width) {
                black.x = canvas.width - black.radius;
                black.vx *= -BOUNCE;
            } else if (black.x - black.radius < 0) {
                black.x = black.radius;
                black.vx *= -BOUNCE;
            }
            // 床判定（下）
            if (black.y + black.radius > canvas.height) {
                black.y = canvas.height - black.radius;
                // 床で転がるように摩擦を強く
                black.vy *= -BOUNCE; 
                if(Math.abs(black.vy) < GRAVITY) black.vy = 0; // 振動防止
            } else if (black.y - black.radius < 0) {
                black.y = black.radius;
                black.vy *= -BOUNCE;
            }
        }

        const dx = black.x - white.x;
        const dy = black.y - white.y;
        const distance = Math.hypot(dx, dy);
        const minDist = black.radius + white.radius;

        if (distance < minDist) {
            hitStopTimer = HIT_STOP_DURATION;
            for(let i=0; i<15; i++) {
                particles.push(new Particle(
                    black.x + (dx/distance) * black.radius,
                    black.y + (dy/distance) * black.radius
                ));
            }
            const angle = Math.atan2(dy, dx);
            const speed = Math.sqrt(black.vx**2 + black.vy**2);
            black.vx = Math.cos(angle) * (speed * 0.8 + 5); 
            black.vy = Math.sin(angle) * (speed * 0.8 + 5);
            
            const overlap = minDist - distance;
            black.x += Math.cos(angle) * overlap;
            black.y += Math.sin(angle) * overlap;
        }

        particles = particles.filter(p => p.life > 0);
        particles.forEach(p => p.update());

        draw();
        requestAnimationFrame(update);
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // 背景グリッド（レスポンシブ対応）
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        // 画面サイズが変わってもグリッドを描画
        for(let i=0; i<canvas.width; i+=80) {
            ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i, canvas.height); ctx.stroke();
        }
        for(let i=0; i<canvas.height; i+=80) {
            ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width, i); ctx.stroke();
        }

        // 白丸
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.arc(white.x, white.y, white.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 黒丸
        ctx.fillStyle = 'black';
        ctx.beginPath();
        ctx.arc(black.x, black.y, black.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#555';
        ctx.beginPath();
        ctx.arc(black.x - 10, black.y - 10, 5, 0, Math.PI * 2);
        ctx.fill();

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

        particles.forEach(p => p.draw(ctx));
    }

    update();
</script>
</body>
</html>
"""

# 高さをスマホ画面に合わせて広めにとる（スクロールバーが出ないように調整）
components.html(html_code, height=600, scrolling=False)

st.write("---")
st.write("※ スマホの場合は、画面を横にするとより遊びやすいかもだっち！🍄")
