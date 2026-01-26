import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Hit Stop Othello: Variable Damage", layout="wide")

st.title("🍄 重力オセロ：スピード＝破壊力💥")
st.write("ぶつける**スピード**によってダメージが変わるよ！思いっきり投げつけて**大ダメージ**を狙うっち！💪")

html_code = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
    body { 
        margin: 0; overflow: hidden; background-color: #f0f2f6; 
        display: flex; justify-content: center; align-items: center; height: 100vh;
        touch-action: none; font-family: 'Arial Black', sans-serif;
    }
    canvas { 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        background-color: #262730;
        border-radius: 10px;
    }
    #respawnBtn {
        position: absolute; top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        padding: 15px 30px; font-size: 24px; font-weight: bold;
        color: white; background-color: #ff4b4b;
        border: none; border-radius: 50px; cursor: pointer;
        display: none; box-shadow: 0 0 20px rgba(255, 75, 75, 0.6);
        animation: pulse 1.5s infinite; z-index: 10;
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
<button id="respawnBtn" onclick="respawn()">もう一回戦う！🥊</button>

<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const respawnBtn = document.getElementById('respawnBtn');

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if(white.hp > 0 && white.baseX === 0) initPositions();
    }
    window.addEventListener('resize', resizeCanvas);

    // パラメータ
    const GRAVITY = 0.5;
    const FRICTION = 0.98;
    const BOUNCE = 0.7;
    const KO_HIT_STOP = 120;
    const MAX_HP = 100; // HPを細かく計算するために100にする

    // ゲーム状態
    let black = { x: 100, y: 100, vx: 0, vy: 0, radius: 30, isDragging: false };
    let white = { x: 0, y: 0, baseX: 0, baseY: 0, radius: 30, hp: MAX_HP, visible: true };
    let isKO = false;

    function initPositions() {
        white.baseX = window.innerWidth * 0.75;
        white.baseY = window.innerHeight * 0.5;
        white.x = white.baseX; white.y = white.baseY;
        black.x = window.innerWidth * 0.25;
        black.y = window.innerHeight * 0.5;
        black.vx = 0; black.vy = 0;
    }
    
    window.respawn = function() {
        white.hp = MAX_HP; white.visible = true; isKO = false;
        initPositions(); respawnBtn.style.display = 'none';
    };

    setTimeout(() => { resizeCanvas(); initPositions(); }, 100);

    // インタラクション変数
    let dragOffsetX = 0, dragOffsetY = 0, lastMouseX = 0, lastMouseY = 0;
    let hitStopTimer = 0;
    let particles = [];
    let damagePopups = []; // ダメージ数字用
    let screenShakeX = 0, screenShakeY = 0;

    // --- クラス定義 ---
    
    // エフェクト用パーティクル
    class Particle {
        constructor(x, y, isBig, colorOverride) {
            this.x = x; this.y = y;
            const angle = Math.random() * Math.PI * 2;
            const speed = isBig ? Math.random() * 15 + 5 : Math.random() * 5 + 2;
            this.vx = Math.cos(angle) * speed;
            this.vy = Math.sin(angle) * speed;
            this.life = 1.0;
            this.decay = isBig ? Math.random() * 0.01 + 0.005 : Math.random() * 0.05 + 0.02;
            this.color = colorOverride ? colorOverride : (isBig ? `hsl(${Math.random()*60 + 10}, 100%, 60%)` : '#FFD700');
            this.size = isBig ? Math.random() * 8 + 4 : Math.random() * 3 + 2;
        }
        update() {
            this.x += this.vx; this.y += this.vy;
            this.vx *= 0.95; this.vy *= 0.95;
            this.life -= this.decay;
        }
        draw(ctx) {
            ctx.globalAlpha = this.life;
            ctx.fillStyle = this.color;
            ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    // ダメージポップアップ用クラス
    class DamagePopup {
        constructor(x, y, damage, isCritical) {
            this.x = x; this.y = y;
            this.damage = Math.floor(damage);
            this.life = 1.0;
            this.vy = -2; // 上に浮かぶ
            this.isCritical = isCritical;
            this.scale = isCritical ? 1.5 : 1.0;
        }
        update() {
            this.y += this.vy;
            this.vy *= 0.95;
            this.life -= 0.02;
        }
        draw(ctx) {
            ctx.globalAlpha = this.life;
            ctx.fillStyle = this.isCritical ? '#ff0000' : '#ffffff';
            ctx.strokeStyle = 'black';
            ctx.lineWidth = 3;
            ctx.font = `bold ${24 * this.scale}px Arial Black`;
            ctx.textAlign = 'center';
            const text = "-" + this.damage;
            ctx.strokeText(text, this.x, this.y);
            ctx.fillText(text, this.x, this.y);
            ctx.globalAlpha = 1.0;
        }
    }

    // --- 入力処理 ---
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
            dragOffsetX = black.x - pos.x; dragOffsetY = black.y - pos.y;
            black.vx = 0; black.vy = 0; lastMouseX = pos.x; lastMouseY = pos.y;
        }
    }
    function onMove(e) {
        if(e.type === 'touchmove') e.preventDefault();
        if (black.isDragging) {
            const pos = getPointerPos(e);
            black.x = pos.x + dragOffsetX; black.y = pos.y + dragOffsetY;
            black.vx = (pos.x - lastMouseX) * 0.5;
            black.vy = (pos.y - lastMouseY) * 0.5;
            lastMouseX = pos.x; lastMouseY = pos.y;
        }
    }
    function onUp(e) { black.isDragging = false; }
    
    canvas.addEventListener('mousedown', onDown); canvas.addEventListener('mousemove', onMove); canvas.addEventListener('mouseup', onUp);
    canvas.addEventListener('touchstart', onDown, {passive: false}); canvas.addEventListener('touchmove', onMove, {passive: false}); canvas.addEventListener('touchend', onUp);

    // --- メインループ ---
    function update() {
        if (hitStopTimer > 0) {
            hitStopTimer--;
            // ヒットストップ中のシェイク演出（ダメージが大きいほど激しい）
            if (isKO || hitStopTimer > 5) {
                const shakePower = isKO ? 30 * (hitStopTimer/KO_HIT_STOP) : 10;
                screenShakeX = (Math.random() - 0.5) * shakePower;
                screenShakeY = (Math.random() - 0.5) * shakePower;
                white.x = white.baseX + (Math.random() - 0.5) * shakePower * 2;
                white.y = white.baseY + (Math.random() - 0.5) * shakePower * 2;
            }
            if (hitStopTimer <= 0) {
                if (isKO) { white.visible = false; respawnBtn.style.display = 'block'; }
                white.x = white.baseX; white.y = white.baseY;
                screenShakeX = 0; screenShakeY = 0;
            }
            draw();
            requestAnimationFrame(update);
            return;
        }

        if (!black.isDragging) {
            black.vy += GRAVITY;
            black.vx *= FRICTION; black.vy *= FRICTION;
            black.x += black.vx; black.y += black.vy;
            
            // 壁・床の跳ね返り
            if (black.x + black.radius > canvas.width) { black.x = canvas.width - black.radius; black.vx *= -BOUNCE; }
            else if (black.x - black.radius < 0) { black.x = black.radius; black.vx *= -BOUNCE; }
            if (black.y + black.radius > canvas.height) { black.y = canvas.height - black.radius; black.vy *= -BOUNCE; if(Math.abs(black.vy) < GRAVITY) black.vy = 0; } 
            else if (black.y - black.radius < 0) { black.y = black.radius; black.vy *= -BOUNCE; }
        }

        if (white.visible) {
            const dx = black.x - white.x;
            const dy = black.y - white.y;
            const dist = Math.hypot(dx, dy);
            const minDist = black.radius + white.radius;

            if (dist < minDist) {
                // 💥 衝突時の速度（衝撃力）を計算
                const impactSpeed = Math.sqrt(black.vx**2 + black.vy**2);
                
                // ダメージ計算ロジック
                // スピード 2以下 = 最低保証ダメージ(5)
                // スピード 25以上 = 最大ダメージ(50)
                let damage = 0;
                let damageColor = '#ffffff';
                let isCritical = false;

                if (impactSpeed < 2) {
                    damage = 5; // ちょこん
                } else {
                    // 線形補間: speed 2~25 を damage 5~50 にマッピング
                    damage = 5 + ((impactSpeed - 2) / 23) * 45;
                    if (damage > 50) damage = 50;
                }

                // クリティカル判定（ある程度速いとクリティカル演出）
                if (damage > 30) {
                    isCritical = true;
                    damageColor = '#ff0000'; // 赤
                }

                white.hp -= damage;
                
                // ポップアップ生成
                damagePopups.push(new DamagePopup(white.x, white.y - 40, damage, isCritical));

                // ヒットストップ時間もダメージ（速度）に比例させる！
                // 弱=5フレーム, 強=20フレーム
                let stopTime = Math.floor(damage / 2.5); 
                if (stopTime < 5) stopTime = 5;

                // KO判定
                if (white.hp <= 0) {
                    isKO = true;
                    white.hp = 0;
                    hitStopTimer = KO_HIT_STOP; // KOはずっと止まる
                    // KOエフェクト
                    for(let i=0; i<80; i++) particles.push(new Particle(white.x, white.y, true));
                } else {
                    hitStopTimer = stopTime;
                    // 通常エフェクト（ダメージ量に応じてパーティクル数も変える）
                    const pCount = Math.floor(damage / 2) + 5;
                    for(let i=0; i<pCount; i++) {
                        particles.push(new Particle(
                            black.x + (dx/dist)*black.radius,
                            black.y + (dy/dist)*black.radius,
                            false,
                            isCritical ? '#ff4444' : '#FFD700'
                        ));
                    }
                }

                // 反発処理
                const angle = Math.atan2(dy, dx);
                const overlap = minDist - dist;
                black.x += Math.cos(angle) * overlap;
                black.y += Math.sin(angle) * overlap;
                
                // 速度の跳ね返り
                black.vx = Math.cos(angle) * (impactSpeed * 0.8 + 2); // 少し勢いを殺す
                black.vy = Math.sin(angle) * (impactSpeed * 0.8 + 2);
            }
        }

        // 更新処理
        particles = particles.filter(p => p.life > 0);
        particles.forEach(p => p.update());
        
        damagePopups = damagePopups.filter(d => d.life > 0);
        damagePopups.forEach(d => d.update());

        draw();
        requestAnimationFrame(update);
    }

    function draw() {
        ctx.save();
        ctx.translate(screenShakeX, screenShakeY);
        ctx.clearRect(-100, -100, canvas.width+200, canvas.height+200);

        // 床
        ctx.strokeStyle = '#444'; ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=80) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i, canvas.height); ctx.stroke(); }
        for(let i=0; i<canvas.height; i+=80) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width, i); ctx.stroke(); }

        if (white.visible) {
            // 白丸描画
            ctx.fillStyle = 'white'; ctx.beginPath(); ctx.arc(white.x, white.y, white.radius, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#ccc'; ctx.lineWidth = 2; ctx.stroke();

            // HPバー
            const barWidth = 80; const barHeight = 8;
            const barX = white.x - barWidth / 2;
            const barY = white.y + white.radius + 15;
            ctx.fillStyle = '#555'; ctx.fillRect(barX, barY, barWidth, barHeight);
            const hpPercent = white.hp / MAX_HP;
            ctx.fillStyle = hpPercent > 0.5 ? '#00ff00' : (hpPercent > 0.2 ? '#ffff00' : '#ff0000');
            ctx.fillRect(barX, barY, barWidth * hpPercent, barHeight);
        }

        // 黒丸描画
        ctx.fillStyle = 'black'; ctx.beginPath(); ctx.arc(black.x, black.y, black.radius, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#555'; ctx.beginPath(); ctx.arc(black.x - 10, black.y - 10, 5, 0, Math.PI * 2); ctx.fill();

        // エフェクトリング
        if (hitStopTimer > 0) {
            ctx.lineWidth = 5;
            if(isKO) { ctx.strokeStyle = `rgba(255, 50, 50, ${Math.random()})`; ctx.lineWidth = 10; } 
            else { ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)'; }
            
            let ringX = isKO ? white.x : (black.x + white.x) / 2;
            let ringY = isKO ? white.y : (black.y + white.y) / 2;
            const expansion = isKO ? (KO_HIT_STOP - hitStopTimer) : (30 - hitStopTimer) * 2;
            
            ctx.beginPath(); ctx.arc(ringX, ringY, black.radius + 20 + expansion, 0, Math.PI * 2); ctx.stroke();
        }

        particles.forEach(p => p.draw(ctx));
        damagePopups.forEach(d => d.draw(ctx)); // ダメージ数値
        
        ctx.restore();
    }

    update();
</script>
</body>
</html>
"""

components.html(html_code, height=600, scrolling=False)

st.write("---")
st.write("### 🥊 攻略のヒントだっち")
st.write("ただぶつけるだけだと **5ダメージ** しか与えられないっち…💦")
st.write("でも、画面の端から勢いよく投げれば、一撃で **50ダメージ（HP半分！）** を持っていけるよ！")
st.write("コツは、**「掴んで、素早くスワイプして、離す！」** だっち！🍄")
