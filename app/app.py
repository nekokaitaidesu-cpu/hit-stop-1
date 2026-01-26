import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Hit Stop Othello: KO Edition", layout="wide")

st.title("重力オセロ")
st.write("ヒットストップで気持ちよくなろう")

html_code = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
    body { 
        margin: 0; overflow: hidden; background-color: #f0f2f6; 
        display: flex; justify-content: center; align-items: center; height: 100vh;
        touch-action: none; font-family: sans-serif;
    }
    canvas { 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        background-color: #262730;
        border-radius: 10px;
    }
    /* リスポーンボタンのスタイル（最初は隠しておく） */
    #respawnBtn {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        padding: 15px 30px;
        font-size: 24px;
        font-weight: bold;
        color: white;
        background-color: #ff4b4b;
        border: none;
        border-radius: 50px;
        cursor: pointer;
        display: none; /* 最初は非表示 */
        box-shadow: 0 0 20px rgba(255, 75, 75, 0.6);
        animation: pulse 1.5s infinite;
        z-index: 10;
    }
    @keyframes pulse {
        0% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.1); }
        100% { transform: translate(-50%, -50%) scale(1); }
    }
</style>
</head>
<body>

<canvas id="gameCanvas"></canvas>
<button id="respawnBtn" onclick="respawn()">もう一回！</button>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const respawnBtn = document.getElementById('respawnBtn');

    // リサイズ対応
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        // リサイズ時に位置がずれないように少し調整（簡易的）
        if(white.hp > 0 && white.baseX === 0) initPositions();
    }
    window.addEventListener('resize', resizeCanvas);

    // パラメータ
    const GRAVITY = 0.5;
    const FRICTION = 0.98;
    const BOUNCE = 0.7;
    const NORMAL_HIT_STOP = 15;   // 通常時のヒットストップ（フレーム）
    const KO_HIT_STOP = 120;      // KO時のヒットストップ（約2秒）
    const SHAKE_INTENSITY = 10;
    const MAX_HP = 5;

    // ゲーム状態
    let black = { x: 100, y: 100, vx: 0, vy: 0, radius: 30, isDragging: false };
    let white = { x: 0, y: 0, baseX: 0, baseY: 0, radius: 30, hp: MAX_HP, visible: true };
    let isKO = false; // KO演出中フラグ

    // 初期配置
    function initPositions() {
        white.baseX = window.innerWidth * 0.75;
        white.baseY = window.innerHeight * 0.5;
        white.x = white.baseX;
        white.y = white.baseY;
        
        black.x = window.innerWidth * 0.25;
        black.y = window.innerHeight * 0.5;
        black.vx = 0;
        black.vy = 0;
    }
    
    // リスポーン処理
    window.respawn = function() {
        white.hp = MAX_HP;
        white.visible = true;
        isKO = false;
        initPositions();
        respawnBtn.style.display = 'none'; // ボタン隠す
    };

    setTimeout(() => { resizeCanvas(); initPositions(); }, 100);

    // インタラクション
    let dragOffsetX = 0, dragOffsetY = 0, lastMouseX = 0, lastMouseY = 0;
    let hitStopTimer = 0;
    let particles = [];
    let screenShakeX = 0; // 画面全体の揺れ
    let screenShakeY = 0;

    class Particle {
        constructor(x, y, isBig = false) {
            this.x = x;
            this.y = y;
            const angle = Math.random() * Math.PI * 2;
            // KO時はパーティクルも派手に！
            const speed = isBig ? Math.random() * 15 + 5 : Math.random() * 5 + 2;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.life = 1.0;
            this.decay = isBig ? Math.random() * 0.01 + 0.005 : Math.random() * 0.05 + 0.02;
            this.color = isBig ? `hsl(${Math.random()*60 + 10}, 100%, 60%)` : '#FFD700'; // KO時は炎色
            this.size = isBig ? Math.random() * 8 + 4 : 4;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.vx *= 0.95; // 空気抵抗
            this.vy *= 0.95;
            this.life -= this.decay;
        }
        draw(ctx) {
            ctx.globalAlpha = this.life;
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    // --- 入力処理 (タッチ＆マウス) ---
    function getPointerPos(e) {
        const rect = canvas.getBoundingClientRect();
        let cx = e.touches ? e.touches[0].clientX : e.clientX;
        let cy = e.touches ? e.touches[0].clientY : e.clientY;
        return { x: cx - rect.left, y: cy - rect.top };
    }

    function onDown(e) {
        if(e.type === 'touchstart') e.preventDefault();
        const pos = getPointerPos(e);
        const dist = Math.hypot(pos.x - black.x, pos.y - black.y);
        if (dist < black.radius * 2.5) { 
            black.isDragging = true;
            dragOffsetX = black.x - pos.x;
            dragOffsetY = black.y - pos.y;
            black.vx = 0; black.vy = 0;
            lastMouseX = pos.x; lastMouseY = pos.y;
        }
    }

    function onMove(e) {
        if(e.type === 'touchmove') e.preventDefault();
        if (black.isDragging) {
            const pos = getPointerPos(e);
            black.x = pos.x + dragOffsetX;
            black.y = pos.y + dragOffsetY;
            black.vx = (pos.x - lastMouseX) * 0.5;
            black.vy = (pos.y - lastMouseY) * 0.5;
            lastMouseX = pos.x; lastMouseY = pos.y;
        }
    }

    function onUp(e) { black.isDragging = false; }

    canvas.addEventListener('mousedown', onDown);
    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseup', onUp);
    canvas.addEventListener('touchstart', onDown, {passive: false});
    canvas.addEventListener('touchmove', onMove, {passive: false});
    canvas.addEventListener('touchend', onUp);

    // --- メインループ ---
    function update() {
        // ヒットストップ中の処理
        if (hitStopTimer > 0) {
            hitStopTimer--;

            // KO時は画面全体も揺らす！（派手派手演出）
            if (isKO) {
                // 揺れはだんだん収束するように（動画の教え）
                const shakePower = 30 * (hitStopTimer / KO_HIT_STOP); 
                screenShakeX = (Math.random() - 0.5) * shakePower;
                screenShakeY = (Math.random() - 0.5) * shakePower;
                
                // 相手も激しく揺れる
                white.x = white.baseX + (Math.random() - 0.5) * shakePower * 2;
                white.y = white.baseY + (Math.random() - 0.5) * shakePower * 2;
            } else {
                // 通常ヒット時は相手だけ少し揺れる
                white.x = white.baseX + (Math.random() - 0.5) * SHAKE_INTENSITY;
                white.y = white.baseY + (Math.random() - 0.5) * SHAKE_INTENSITY * 0.2;
                screenShakeX = 0;
                screenShakeY = 0;
            }

            // ヒットストップが終わった瞬間
            if (hitStopTimer <= 0) {
                if (isKO) {
                    white.visible = false; // 消滅
                    respawnBtn.style.display = 'block'; // ボタン出現
                }
                // 位置リセット
                white.x = white.baseX;
                white.y = white.baseY;
                screenShakeX = 0;
                screenShakeY = 0;
            }

            draw();
            requestAnimationFrame(update);
            return; // 物理停止
        }

        // 物理更新
        if (!black.isDragging) {
            black.vy += GRAVITY;
            black.vx *= FRICTION; black.vy *= FRICTION;
            black.x += black.vx; black.y += black.vy;

            // 壁・床
            if (black.x + black.radius > canvas.width) { black.x = canvas.width - black.radius; black.vx *= -BOUNCE; }
            else if (black.x - black.radius < 0) { black.x = black.radius; black.vx *= -BOUNCE; }
            
            if (black.y + black.radius > canvas.height) { 
                black.y = canvas.height - black.radius; 
                black.vy *= -BOUNCE; 
                if(Math.abs(black.vy) < GRAVITY) black.vy = 0;
            } else if (black.y - black.radius < 0) { black.y = black.radius; black.vy *= -BOUNCE; }
        }

        // 衝突判定（相手が生きてる時だけ）
        if (white.visible) {
            const dx = black.x - white.x;
            const dy = black.y - white.y;
            const dist = Math.hypot(dx, dy);
            const minDist = black.radius + white.radius;

            if (dist < minDist) {
                // ダメージ処理
                white.hp--;
                
                // 反発計算
                const angle = Math.atan2(dy, dx);
                // 埋まり防止
                const overlap = minDist - dist;
                black.x += Math.cos(angle) * overlap;
                black.y += Math.sin(angle) * overlap;
                
                // 跳ね返り
                const speed = Math.sqrt(black.vx**2 + black.vy**2);
                black.vx = Math.cos(angle) * (speed * 0.8 + 5);
                black.vy = Math.sin(angle) * (speed * 0.8 + 5);

                // --- 演出分岐 ---
                if (white.hp <= 0) {
                    // ③ KO発生！
                    isKO = true;
                    hitStopTimer = KO_HIT_STOP; // 長いストップ！
                    
                    // 派手なパーティクル大量発生
                    for(let i=0; i<80; i++) {
                        particles.push(new Particle(
                            white.x, white.y, true // true = Big Particle
                        ));
                    }
                } else {
                    // 通常ヒット
                    hitStopTimer = NORMAL_HIT_STOP;
                    for(let i=0; i<10; i++) {
                        particles.push(new Particle(
                            black.x + (dx/dist)*black.radius,
                            black.y + (dy/dist)*black.radius
                        ));
                    }
                }
            }
        }

        // パーティクル更新
        particles = particles.filter(p => p.life > 0);
        particles.forEach(p => p.update());

        draw();
        requestAnimationFrame(update);
    }

    function draw() {
        // 画面全体を揺らすために save/restore を使う
        ctx.save();
        ctx.translate(screenShakeX, screenShakeY);
        
        ctx.clearRect(-100, -100, canvas.width+200, canvas.height+200); // 揺れても消えるように広めにクリア

        // グリッド
        ctx.strokeStyle = '#444';
        ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=80) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i, canvas.height); ctx.stroke(); }
        for(let i=0; i<canvas.height; i+=80) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width, i); ctx.stroke(); }

        if (white.visible) {
            // 白丸
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(white.x, white.y, white.radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#ccc';
            ctx.lineWidth = 2;
            ctx.stroke();

            // ① 体力ゲージ（白丸の下に表示）
            const barWidth = 60;
            const barHeight = 8;
            const barX = white.x - barWidth / 2;
            const barY = white.y + white.radius + 15;
            
            // 背景（グレー）
            ctx.fillStyle = '#555';
            ctx.fillRect(barX, barY, barWidth, barHeight);
            
            // 現在HP（色が変わる！）
            const hpPercent = white.hp / MAX_HP;
            if(hpPercent > 0.5) ctx.fillStyle = '#00ff00'; // 緑
            else if(hpPercent > 0.2) ctx.fillStyle = '#ffff00'; // 黄色
            else ctx.fillStyle = '#ff0000'; // 赤（ピンチ！）
            
            ctx.fillRect(barX, barY, barWidth * hpPercent, barHeight);
        }

        // 黒丸
        ctx.fillStyle = 'black';
        ctx.beginPath();
        ctx.arc(black.x, black.y, black.radius, 0, Math.PI * 2);
        ctx.fill();
        // ハイライト
        ctx.fillStyle = '#555';
        ctx.beginPath();
        ctx.arc(black.x - 10, black.y - 10, 5, 0, Math.PI * 2);
        ctx.fill();

        // ヒットエフェクト（リング）
        if (hitStopTimer > 0) {
            ctx.lineWidth = 5;
            if(isKO) {
                // KO時は赤い激しいリング
                ctx.strokeStyle = `rgba(255, 50, 50, ${Math.random()})`; 
                ctx.lineWidth = 10;
            } else {
                ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
            }
            
            ctx.beginPath();
            // 揺れに合わせてリングの位置も調整
            let ringX = (black.x + white.x) / 2;
            let ringY = (black.y + white.y) / 2;
            if(isKO) { ringX = white.x; ringY = white.y; } // KO時は相手中心

            const expansion = isKO ? (KO_HIT_STOP - hitStopTimer) : (NORMAL_HIT_STOP - hitStopTimer) * 2;
            ctx.arc(ringX, ringY, black.radius + 20 + expansion, 0, Math.PI * 2);
            ctx.stroke();
        }

        particles.forEach(p => p.draw(ctx));
        
        ctx.restore(); // 揺れ解除
    }

    update();
</script>
</body>
</html>
"""

components.html(html_code, height=600, scrolling=False)

st.write("### 遊び方")
st.write("1. 黒丸を投げつけて、白丸にぶつけてね！")
st.write("2. 下のゲージがHP")
st.write("3. 気持ちいいヒットストップを体験しよう！")
