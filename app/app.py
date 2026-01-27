import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Hit Stop Othello: Shotgun Added", layout="wide")

# --- サイドバー ---
st.sidebar.title("🍄 設定メニュー")

# 武器選択にショットガンを追加！
weapon_mode = st.sidebar.radio(
    "武器選択 ⚔️",
    ("鉄球 (Iron Ball)", "聖剣 (Holy Sword)", "ショットガン (Shotgun) 🔫")
)
game_mode = st.sidebar.radio("ゲームモード", ("通常バトル (Normal)", "無限サンドバッグ (Infinite) ♾️"))

# パラメータ設定
sword_hit_stop = 5 # 剣のデフォルト

if game_mode == "通常バトル (Normal)":
    start_hp = st.sidebar.slider("白丸のHP", 100, 2000, 800, step=100) # ショットガンは威力が高いのでHP多めに
    is_infinite_js = "false"
else:
    start_hp = 9999
    is_infinite_js = "true"

# JSに渡す武器タイプ設定
if weapon_mode == "鉄球 (Iron Ball)":
    weapon_type_js = "'ball'"
    st.sidebar.info("重力を活かして投げつける「重量級」武器だっち！")
elif weapon_mode == "聖剣 (Holy Sword)":
    weapon_type_js = "'sword'"
    st.sidebar.markdown("---")
    sword_hit_stop = st.sidebar.slider("⚔️ 斬撃の重さ", 0, 20, 5)
    expected_dmg = int(10 + (sword_hit_stop * 1.5))
    st.sidebar.caption(f"威力: {expected_dmg}ダメージ/1hit")
else:
    weapon_type_js = "'shotgun'"
    st.sidebar.success("接近戦最強！近づいて全弾叩き込むだっち！🔫")
    st.sidebar.caption("※クリックで発射。リロード時間があるよ。")

st.title("🍄 重力オセロ：ショットガン参戦！🔫")
st.write("新武器**「ショットガン」**追加！距離が近いほど超ダメージ！近づいてぶっ放すだっち！")

html_template = """
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
        cursor: crosshair;
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

    const IS_INFINITE = __IS_INFINITE__;
    const MAX_HP = __MAX_HP__;
    const WEAPON_TYPE = __WEAPON_TYPE__;
    const SWORD_HIT_STOP_VAL = __SWORD_HIT_STOP__;

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if(white.hp > 0 && white.baseX === 0) initPositions();
    }
    window.addEventListener('resize', resizeCanvas);

    const GRAVITY = 0.5; const FRICTION = 0.98; const BOUNCE = 0.7;
    const KO_HIT_STOP = 120;
    
    // 武器設定
    const SWORD_LENGTH = 130; const SWORD_SWING_ANGLE = 120 * (Math.PI / 180); const SWORD_SPEED = 12;
    const FIXED_UP_ANGLE = -Math.PI / 2; 
    // 🔫ショットガン設定
    const SHOTGUN_PELLETS = 12; // 弾数
    const SHOTGUN_SPREAD = Math.PI / 5; // 拡散角度(約36度)
    const SHOTGUN_DAMAGE = 8; // 1発のダメージ（全弾命中で96!）
    const SHOTGUN_SPEED = 25; // 弾速
    const SHOTGUN_COOLDOWN = 40; // 連射間隔フレーム

    let black = { 
        x: 100, y: 100, vx: 0, vy: 0, radius: 30, 
        isDragging: false, 
        angle: FIXED_UP_ANGLE, baseAngle: FIXED_UP_ANGLE, swingProgress: 0, isSwinging: false,
        hitFlags: [false, false, false],
        cooldownTimer: 0, // ショットガン用クールダウン
        targetX: 100, targetY: 100
    };
    let white = { x: 0, y: 0, baseX: 0, baseY: 0, radius: 30, hp: MAX_HP, visible: true };
    let isKO = false;

    function initPositions() {
        white.baseX = window.innerWidth * 0.75;
        white.baseY = window.innerHeight * 0.5;
        white.x = white.baseX; white.y = white.baseY;
        black.x = window.innerWidth * 0.25; black.y = window.innerHeight * 0.5;
        black.vx = 0; black.vy = 0; black.targetX = black.x; black.targetY = black.y;
        black.angle = FIXED_UP_ANGLE; black.baseAngle = FIXED_UP_ANGLE;
        black.cooldownTimer = 0;
    }
    
    window.respawn = function() {
        white.hp = MAX_HP; white.visible = true; isKO = false;
        initPositions(); respawnBtn.style.display = 'none';
    };

    setTimeout(() => { resizeCanvas(); initPositions(); }, 100);

    let mouseX = 0, mouseY = 0; let lastMouseX = 0, lastMouseY = 0;
    let hitStopTimer = 0;
    let particles = [];
    let slashEffects = [];
    let damagePopups = [];
    let pellets = []; // 🔫散弾用配列
    let screenShakeX = 0, screenShakeY = 0;

    // --- クラス定義 ---
    class Particle {
        constructor(x, y, isBig, colorOverride) {
            this.x = x; this.y = y;
            const angle = Math.random() * Math.PI * 2;
            const speed = isBig ? Math.random() * 15 + 5 : Math.random() * 5 + 2;
            this.vx = Math.cos(angle) * speed; this.vy = Math.sin(angle) * speed;
            this.life = 1.0;
            this.decay = isBig ? Math.random() * 0.01 + 0.005 : Math.random() * 0.05 + 0.02;
            this.color = colorOverride ? colorOverride : (isBig ? `hsl(${Math.random()*60 + 10}, 100%, 60%)` : '#FFD700');
            this.size = isBig ? Math.random() * 8 + 4 : Math.random() * 3 + 2;
        }
        update() { this.x += this.vx; this.y += this.vy; this.vx *= 0.95; this.vy *= 0.95; this.life -= this.decay; }
        draw(ctx) { ctx.globalAlpha = this.life; ctx.fillStyle = this.color; ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fill(); ctx.globalAlpha = 1.0; }
    }

    class SlashEffect {
        constructor(x, y, angle) {
            this.x = x; this.y = y; this.angle = angle;
            this.life = 1.0; this.length = Math.max(window.innerWidth, window.innerHeight) * 2.5; this.width = 2;
        }
        update() { this.life -= 0.08; this.width += 4; }
        draw(ctx) {
            ctx.save(); ctx.translate(this.x, this.y); ctx.rotate(this.angle);
            ctx.globalAlpha = this.life; ctx.fillStyle = 'white'; ctx.shadowBlur = 20; ctx.shadowColor = 'cyan';
            ctx.fillRect(-this.length/2, -this.width/2, this.length, this.width); ctx.rotate(Math.PI / 2);
            ctx.fillRect(-this.length/2, -this.width/4, this.length, this.width/2);
            ctx.restore(); ctx.globalAlpha = 1.0;
        }
    }

    // 🔫ショットガンの弾クラス
    class Pellet {
        constructor(x, y, angle) {
            this.x = x; this.y = y;
            this.vx = Math.cos(angle) * SHOTGUN_SPEED;
            this.vy = Math.sin(angle) * SHOTGUN_SPEED;
            this.life = 30; // 寿命（フレーム数）
            this.size = 5;
        }
        update() {
            this.x += this.vx; this.y += this.vy;
            this.life--;
        }
        draw(ctx) {
            ctx.fillStyle = '#ffff00'; // 黄色い弾
            ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fill();
            // 軌跡
            ctx.strokeStyle = 'rgba(255, 255, 0, 0.5)'; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.moveTo(this.x, this.y); ctx.lineTo(this.x - this.vx*2, this.y - this.vy*2); ctx.stroke();
        }
    }

    class DamagePopup {
        constructor(x, y, damage, isCritical) {
            this.x = x; this.y = y; this.damage = Math.floor(damage);
            this.life = 1.0; this.vy = -2; this.isCritical = isCritical; this.scale = isCritical ? 1.5 : 1.0;
        }
        update() { this.y += this.vy; this.vy *= 0.95; this.life -= 0.02; }
        draw(ctx) {
            ctx.globalAlpha = this.life;
            ctx.fillStyle = this.isCritical ? '#ff0000' : '#ffffff';
            ctx.strokeStyle = 'black'; ctx.lineWidth = 3;
            ctx.font = `bold ${24 * this.scale}px Arial Black`; ctx.textAlign = 'center';
            const text = this.damage;
            ctx.strokeText(text, this.x, this.y); ctx.fillText(text, this.x, this.y);
            ctx.globalAlpha = 1.0;
        }
    }

    function getPointerPos(e) {
        const rect = canvas.getBoundingClientRect();
        let cx = e.touches ? e.touches[0].clientX : e.clientX;
        let cy = e.touches ? e.touches[0].clientY : e.clientY;
        return { x: cx - rect.left, y: cy - rect.top };
    }

    function onDown(e) {
        if(e.type === 'touchstart') e.preventDefault();
        const pos = getPointerPos(e);
        if (WEAPON_TYPE === 'ball') {
            const dist = Math.hypot(pos.x - black.x, pos.y - black.y);
            if (dist < black.radius * 2.5) { 
                black.isDragging = true; black.vx = 0; black.vy = 0; lastMouseX = pos.x; lastMouseY = pos.y;
            }
        } else if (WEAPON_TYPE === 'sword') {
            if (!black.isSwinging) {
                black.isSwinging = true; black.swingProgress = 0; black.hitFlags = [false, false, false]; black.baseAngle = FIXED_UP_ANGLE;
            }
        } else if (WEAPON_TYPE === 'shotgun') {
            // 🔫ショットガン発射！
            if (black.cooldownTimer <= 0) {
                black.cooldownTimer = SHOTGUN_COOLDOWN; // クールダウン開始
                const baseAngle = Math.atan2(pos.y - black.y, pos.x - black.x);
                
                // マズルフラッシュ（火花）
                for(let i=0; i<20; i++) {
                     particles.push(new Particle(black.x + Math.cos(baseAngle)*30, black.y + Math.sin(baseAngle)*30, false, '#ffaa00'));
                }
                // 画面を少し揺らす（反動）
                hitStopTimer = 4; 

                // 散弾生成
                for (let i = 0; i < SHOTGUN_PELLETS; i++) {
                    // 拡散角度の範囲でランダムに角度をずらす
                    const spread = (Math.random() - 0.5) * SHOTGUN_SPREAD;
                    pellets.push(new Pellet(black.x, black.y, baseAngle + spread));
                }
            }
        }
    }

    function onMove(e) {
        if(e.type === 'touchmove') e.preventDefault();
        const pos = getPointerPos(e);
        mouseX = pos.x; mouseY = pos.y;
        
        if (WEAPON_TYPE === 'ball' && black.isDragging) { 
            black.x = pos.x; black.y = pos.y; 
            black.vx = (pos.x - lastMouseX) * 0.5; black.vy = (pos.y - lastMouseY) * 0.5;
            lastMouseX = pos.x; lastMouseY = pos.y;
        } else if (WEAPON_TYPE === 'sword') { 
            black.targetX = pos.x; black.targetY = pos.y; 
        }
        // ショットガンはマウスの方向を向く（updateで処理）
    }
    function onUp(e) { black.isDragging = false; }
    
    canvas.addEventListener('mousedown', onDown); canvas.addEventListener('mouseup', onUp); canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('touchstart', onDown, {passive: false}); canvas.addEventListener('touchend', onUp); canvas.addEventListener('touchmove', onMove, {passive: false});

    function update() {
        // クールダウン減少
        if (black.cooldownTimer > 0) black.cooldownTimer--;

        if (hitStopTimer > 0) {
            hitStopTimer--;
            // ショットガンのヒットストップは短いが回数が多いので揺れは控えめに
            let baseShake = (WEAPON_TYPE === 'sword' ? 3 : 10);
            if (WEAPON_TYPE === 'shotgun') baseShake = 5;

            const shakePower = isKO ? 30 * (hitStopTimer/KO_HIT_STOP) : baseShake;
            screenShakeX = (Math.random() - 0.5) * shakePower;
            screenShakeY = (Math.random() - 0.5) * shakePower;
            white.x = white.baseX + (Math.random() - 0.5) * shakePower * 2;
            white.y = white.baseY + (Math.random() - 0.5) * shakePower * 2;
            
            if (hitStopTimer <= 0) {
                if (isKO) { white.visible = false; respawnBtn.style.display = 'block'; }
                white.x = white.baseX; white.y = white.baseY;
                screenShakeX = 0; screenShakeY = 0;
            }
            // 🔫散弾はヒットストップ中も動かす！（これが気持ちよさの秘訣）
            if (!isKO) {
                 pellets.forEach(p => p.update());
                 checkPelletCollisions(); // 後述の関数
            }
            draw(); requestAnimationFrame(update); return;
        }

        // --- プレイヤーの動き ---
        if (WEAPON_TYPE === 'ball') {
            if (!black.isDragging) {
                black.vy += GRAVITY; black.vx *= FRICTION; black.vy *= FRICTION; black.x += black.vx; black.y += black.vy;
                if (black.x + black.radius > canvas.width) { black.x = canvas.width - black.radius; black.vx *= -BOUNCE; }
                else if (black.x - black.radius < 0) { black.x = black.radius; black.vx *= -BOUNCE; }
                if (black.y + black.radius > canvas.height) { black.y = canvas.height - black.radius; black.vy *= -BOUNCE; if(Math.abs(black.vy) < GRAVITY) black.vy = 0; } 
                else if (black.y - black.radius < 0) { black.y = black.radius; black.vy *= -BOUNCE; }
            }
        } else if (WEAPON_TYPE === 'sword') {
            const followSpeed = black.isSwinging ? 0.05 : 0.2;
            black.x += (black.targetX - black.x) * followSpeed; black.y += (black.targetY - black.y) * followSpeed;
            if (black.isSwinging) {
                black.swingProgress += 1.0 / SWORD_SPEED;
                const startAngle = FIXED_UP_ANGLE - SWORD_SWING_ANGLE / 2; const endAngle = FIXED_UP_ANGLE + SWORD_SWING_ANGLE / 2;
                const t = black.swingProgress; const easeT = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                black.angle = startAngle + (endAngle - startAngle) * easeT;
                if (black.swingProgress >= 1.0) { black.isSwinging = false; }
            } else {
                black.baseAngle = FIXED_UP_ANGLE; black.angle = FIXED_UP_ANGLE + Math.sin(Date.now() / 400) * 0.05; 
            }
        } else if (WEAPON_TYPE === 'shotgun') {
            // ショットガンはマウスの方向を向く
            black.angle = Math.atan2(mouseY - black.y, mouseX - black.x);
        }

        // --- 弾の更新 ---
        pellets.forEach(p => p.update());
        pellets = pellets.filter(p => p.life > 0);

        // --- 当たり判定 ---
        if (white.visible) {
            // 鉄球と剣の判定（既存コード）
            checkMeleeCollisions();
            // ショットガンの判定
            checkPelletCollisions();
        }

        particles = particles.filter(p => p.life > 0); particles.forEach(p => p.update());
        damagePopups = damagePopups.filter(d => d.life > 0); damagePopups.forEach(d => d.update());
        slashEffects = slashEffects.filter(s => s.life > 0); slashEffects.forEach(s => s.update());
        draw(); requestAnimationFrame(update);
    }

    // 🔫散弾の当たり判定関数（分離した）
    function checkPelletCollisions() {
        if (!white.visible) return;
        let hitCountInFrame = 0;
        pellets.forEach(p => {
            if (p.life <= 0) return;
            const dist = Math.hypot(p.x - white.x, p.y - white.y);
            if (dist < white.radius + p.size) {
                // ヒット！
                p.life = 0; // 弾消滅
                hitCountInFrame++;
                if (!IS_INFINITE) white.hp -= SHOTGUN_DAMAGE;
                damagePopups.push(new DamagePopup(p.x, p.y - 20, SHOTGUN_DAMAGE, false));
                
                // エフェクト（小さい火花）
                for(let i=0; i<3; i++) particles.push(new Particle(p.x, p.y, false, '#ffaa00'));

                // KO判定
                 if (!IS_INFINITE && white.hp <= 0 && !isKO) {
                    isKO = true; white.hp = 0; hitStopTimer = KO_HIT_STOP;
                    for(let i=0; i<80; i++) particles.push(new Particle(white.x, white.y, true));
                }
            }
        });
        // 弾が当たったら短いヒットストップをかける（ダダダ感）
        if (hitCountInFrame > 0 && !isKO) {
            // 複数当たっても1フレームに設定することで、連続ヒットでガガガッと止まる
             hitStopTimer = 2; 
        }
    }

    // 鉄球と剣の当たり判定（既存コードを関数化）
    function checkMeleeCollisions() {
         let isHit = false; let damage = 0; let isCritical = false; let hitX = 0, hitY = 0;
         // (略: 既存の鉄球・剣の判定ロジックはそのままここに入る)
         if (WEAPON_TYPE === 'ball') {
            const dx = black.x - white.x; const dy = black.y - white.y;
            const dist = Math.hypot(dx, dy); const minDist = black.radius + white.radius;
            if (dist < minDist) {
                isHit = true; hitX = (black.x + white.x) / 2; hitY = (black.y + white.y) / 2;
                const speed = Math.sqrt(black.vx**2 + black.vy**2);
                damage = speed < 2 ? 5 : 5 + ((speed - 2) / 20) * 45; if(damage > 50) damage = 50; if(damage > 30) isCritical = true;
                const angle = Math.atan2(dy, dx); const overlap = minDist - dist;
                black.x += Math.cos(angle) * overlap; black.y += Math.sin(angle) * overlap;
                black.vx = Math.cos(angle) * (speed * 0.8 + 2); black.vy = Math.sin(angle) * (speed * 0.8 + 2);
            }
        } else if (WEAPON_TYPE === 'sword') {
            if (black.isSwinging) {
                const dx = black.x - white.x; const dy = black.y - white.y;
                const dist = Math.hypot(dx, dy);
                if (dist < SWORD_LENGTH + white.radius) {
                    let phase = Math.floor(black.swingProgress * 3);
                    if (phase > 2) phase = 2;
                    if (!black.hitFlags[phase]) {
                        const angleToEnemy = Math.atan2(white.y - black.y, white.x - black.x);
                        let angleDiff = angleToEnemy - black.angle;
                        while (angleDiff > Math.PI) angleDiff -= Math.PI * 2; while (angleDiff < -Math.PI) angleDiff += Math.PI * 2;
                        if (Math.abs(angleDiff) < Math.PI / 7) {
                            isHit = true; black.hitFlags[phase] = true; hitX = white.x; hitY = white.y;
                            damage = 10 + (SWORD_HIT_STOP_VAL * 1.5); isCritical = true;
                        }
                    }
                }
            }
        }
        if (isHit) {
            if (!IS_INFINITE) white.hp -= damage;
            damagePopups.push(new DamagePopup(white.x, white.y - 40, damage, isCritical));
            if (WEAPON_TYPE === 'sword') slashEffects.push(new SlashEffect(white.x, white.y, black.angle));
            if (!IS_INFINITE && white.hp <= 0) {
                isKO = true; white.hp = 0; hitStopTimer = KO_HIT_STOP;
                for(let i=0; i<80; i++) particles.push(new Particle(white.x, white.y, true));
            } else {
                hitStopTimer = WEAPON_TYPE === 'sword' ? SWORD_HIT_STOP_VAL : Math.floor(damage / 2); 
                if (hitStopTimer < 3 && WEAPON_TYPE === 'ball') hitStopTimer = 3; 
                const pCount = Math.floor(damage / 3) + 3;
                for(let i=0; i<pCount; i++) particles.push(new Particle(hitX, hitY, false, isCritical ? '#00ffff' : '#FFD700'));
            }
        }
    }


    function draw() {
        ctx.save(); ctx.translate(screenShakeX, screenShakeY);
        ctx.clearRect(-100, -100, canvas.width+200, canvas.height+200);
        ctx.strokeStyle = '#444'; ctx.lineWidth = 1;
        for(let i=0; i<canvas.width; i+=80) { ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i, canvas.height); ctx.stroke(); }
        for(let i=0; i<canvas.height; i+=80) { ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width, i); ctx.stroke(); }

        if (white.visible) {
            ctx.fillStyle = 'white'; ctx.beginPath(); ctx.arc(white.x, white.y, white.radius, 0, Math.PI * 2); ctx.fill();
            ctx.strokeStyle = '#ccc'; ctx.lineWidth = 2; ctx.stroke();
            const barWidth = 80; const barHeight = 8;
            const barX = white.x - barWidth / 2; const barY = white.y + white.radius + 15;
            ctx.fillStyle = '#555'; ctx.fillRect(barX, barY, barWidth, barHeight);
            if (IS_INFINITE) {
                ctx.fillStyle = '#00ffff'; ctx.fillRect(barX, barY, barWidth, barHeight);
                ctx.fillStyle = '#fff'; ctx.font = '12px Arial'; ctx.textAlign = 'center'; ctx.fillText("∞", white.x, barY + 9);
            } else {
                const hpPercent = white.hp / MAX_HP;
                ctx.fillStyle = hpPercent > 0.5 ? '#00ff00' : (hpPercent > 0.2 ? '#ffff00' : '#ff0000');
                ctx.fillRect(barX, barY, barWidth * hpPercent, barHeight);
            }
        }

        if (WEAPON_TYPE === 'ball') {
            ctx.fillStyle = 'black'; ctx.beginPath(); ctx.arc(black.x, black.y, black.radius, 0, Math.PI * 2); ctx.fill();
            ctx.fillStyle = '#555'; ctx.beginPath(); ctx.arc(black.x - 10, black.y - 10, 5, 0, Math.PI * 2); ctx.fill();
        } else if (WEAPON_TYPE === 'sword') {
            ctx.save(); ctx.translate(black.x, black.y); ctx.rotate(black.angle);
            ctx.shadowBlur = 15; ctx.shadowColor = '#00ffff'; ctx.fillStyle = '#ccffff';
            ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(0, 10); ctx.lineTo(SWORD_LENGTH, 0); ctx.fill();
            ctx.shadowBlur = 0; ctx.fillStyle = '#555'; ctx.fillRect(0, -8, 25, 16); ctx.fillStyle = '#888'; ctx.fillRect(5, -20, 10, 40); ctx.restore();
        } else if (WEAPON_TYPE === 'shotgun') {
            // 🔫ショットガン描画（黒丸が銃口を向く）
            ctx.save(); ctx.translate(black.x, black.y); ctx.rotate(black.angle);
            ctx.fillStyle = 'black'; ctx.beginPath(); ctx.arc(0, 0, black.radius, 0, Math.PI * 2); ctx.fill();
            // 銃口（赤い印）
            ctx.fillStyle = '#ff5555'; ctx.beginPath(); ctx.arc(black.radius-5, 0, 8, 0, Math.PI*2); ctx.fill();
             // クールダウン表示（円グラフ）
            if(black.cooldownTimer > 0) {
                 ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
                 ctx.beginPath(); ctx.moveTo(0,0);
                 ctx.arc(0, 0, black.radius, -Math.PI/2, -Math.PI/2 + (Math.PI*2 * (black.cooldownTimer/SHOTGUN_COOLDOWN)), false);
                 ctx.fill();
            }
            ctx.restore();
        }

        if (hitStopTimer > 0) {
            ctx.lineWidth = 5;
            if(isKO) { ctx.strokeStyle = `rgba(255, 50, 50, ${Math.random()})`; ctx.lineWidth = 10; } 
            else { 
                if (WEAPON_TYPE === 'ball') ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
                else if (WEAPON_TYPE === 'sword') ctx.strokeStyle = 'rgba(0, 255, 255, 0.8)';
                else ctx.strokeStyle = 'rgba(255, 100, 0, 0.8)'; // ショットガンはオレンジ
            }
            let ringX = isKO ? white.x : (WEAPON_TYPE==='ball' ? (black.x + white.x)/2 : white.x);
            let ringY = isKO ? white.y : (WEAPON_TYPE==='ball' ? (black.y + white.y)/2 : white.y);
            const expansion = isKO ? (KO_HIT_STOP - hitStopTimer) : (30 - hitStopTimer) * 2;
            ctx.beginPath(); ctx.arc(ringX, ringY, black.radius + 20 + expansion, 0, Math.PI * 2); ctx.stroke();
        }

        // 🔫散弾描画
        pellets.forEach(p => p.draw(ctx));
        particles.forEach(p => p.draw(ctx));
        slashEffects.forEach(s => s.draw(ctx));
        damagePopups.forEach(d => d.draw(ctx));
        ctx.restore();
    }

    update();
</script>
</body>
</html>
"""

final_html_code = html_template.replace("__IS_INFINITE__", is_infinite_js) \
                               .replace("__MAX_HP__", str(start_hp)) \
                               .replace("__WEAPON_TYPE__", weapon_type_js) \
                               .replace("__SWORD_HIT_STOP__", str(sword_hit_stop))

components.html(final_html_code, height=600, scrolling=False)
