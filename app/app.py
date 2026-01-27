import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Hit Stop Othello: Triple Slash", layout="wide")

# --- サイドバー ---
st.sidebar.title("🍄 設定メニュー")

weapon_mode = st.sidebar.radio("武器選択 ⚔️", ("鉄球 (Iron Ball)", "聖剣 (Holy Sword)"))
game_mode = st.sidebar.radio("ゲームモード", ("通常バトル (Normal)", "無限サンドバッグ (Infinite) ♾️"))

if game_mode == "通常バトル (Normal)":
    start_hp = st.sidebar.slider("白丸のHP", 100, 999, 500, step=50) # HP増やした！
    is_infinite_js = "false"
else:
    start_hp = 9999
    is_infinite_js = "true"

if weapon_mode == "鉄球 (Iron Ball)":
    weapon_type_js = "'ball'"
    st.sidebar.info("重力を活かして投げつける「重量級」武器だっち！")
else:
    weapon_type_js = "'sword'"
    st.sidebar.success("120度の広範囲斬撃！最大3ヒットのコンボを決めるっち！")

st.title("🍄 重力オセロ：トリプルスラッシュ編⚔️")
st.write("剣の振りを**120度**に変更！うまく当てると**3回連続**でダメージが入るよ！")

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

    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if(white.hp > 0 && white.baseX === 0) initPositions();
    }
    window.addEventListener('resize', resizeCanvas);

    const GRAVITY = 0.5;
    const FRICTION = 0.98;
    const BOUNCE = 0.7;
    const KO_HIT_STOP = 120;
    
    // ⚔️ 剣の設定
    const SWORD_LENGTH = 160; 
    const SWORD_SWING_ANGLE = 120 * (Math.PI / 180); // 120度をラジアンに
    const SWORD_SPEED = 12; // スイングにかかるフレーム数（速め）

    let black = { 
        x: 100, y: 100, vx: 0, vy: 0, radius: 30, 
        isDragging: false, 
        // 剣用パラメータ
        angle: 0,           // 描画上の現在の角度
        baseAngle: 0,       // 剣の基準向き（マウスの方）
        swingProgress: 0,   // スイング進行度 (0.0 ～ 1.0)
        isSwinging: false,
        hitFlags: [false, false, false], // 3回ヒット管理用
        
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
    }
    
    window.respawn = function() {
        white.hp = MAX_HP; white.visible = true; isKO = false;
        initPositions(); respawnBtn.style.display = 'none';
    };

    setTimeout(() => { resizeCanvas(); initPositions(); }, 100);

    let mouseX = 0, mouseY = 0;
    let hitStopTimer = 0;
    let particles = [];
    let slashEffects = [];
    let damagePopups = [];
    let screenShakeX = 0, screenShakeY = 0;

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
            this.vx *= 0.95; this.vy *= 0.95; this.life -= this.decay;
        }
        draw(ctx) {
            ctx.globalAlpha = this.life; ctx.fillStyle = this.color;
            ctx.beginPath(); ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2); ctx.fill();
            ctx.globalAlpha = 1.0;
        }
    }

    class SlashEffect {
        constructor(x, y, angle) {
            this.x = x; this.y = y; this.angle = angle;
            this.life = 1.0; this.length = Math.max(window.innerWidth, window.innerHeight) * 2.5; 
            this.width = 2;
        }
        update() { this.life -= 0.08; this.width += 4; }
        draw(ctx) {
            ctx.save(); ctx.translate(this.x, this.y); ctx.rotate(this.angle);
            ctx.globalAlpha = this.life; ctx.fillStyle = 'white';
            ctx.shadowBlur = 20; ctx.shadowColor = 'cyan';
            ctx.fillRect(-this.length/2, -this.width/2, this.length, this.width);
            ctx.rotate(Math.PI / 2);
            ctx.fillRect(-this.length/2, -this.width/4, this.length, this.width/2);
            ctx.restore(); ctx.globalAlpha = 1.0;
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
            ctx.font = `bold ${24 * this.scale}px Arial Black`;
            ctx.textAlign = 'center';
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
                black.isDragging = true; black.vx = 0; black.vy = 0;
            }
        } else if (WEAPON_TYPE === 'sword') {
            // スイング開始！
            if (!black.isSwinging) {
                black.isSwinging = true;
                black.swingProgress = 0;
                black.hitFlags = [false, false, false]; // ヒット履歴リセット
                
                // 振り始めの基準角度を確定させる（マウスの方向）
                const dx = pos.x - black.x;
                const dy = pos.y - black.y;
                black.baseAngle = Math.atan2(dy, dx);
            }
        }
    }

    function onMove(e) {
        if(e.type === 'touchmove') e.preventDefault();
        const pos = getPointerPos(e);
        mouseX = pos.x; mouseY = pos.y;
        if (WEAPON_TYPE === 'ball' && black.isDragging) { black.x = pos.x; black.y = pos.y; }
        else if (WEAPON_TYPE === 'sword') { black.targetX = pos.x; black.targetY = pos.y; }
    }
    canvas.addEventListener('mousemove', (e) => {
         if(black.isDragging && WEAPON_TYPE === 'ball') {
             const rect = canvas.getBoundingClientRect();
             const mx = e.clientX - rect.left; const my = e.clientY - rect.top;
             black.vx = (mx - black.x) * 0.5; black.vy = (my - black.y) * 0.5;
             black.x = mx; black.y = my;
         }
    });
    function onUp(e) { black.isDragging = false; }
    
    canvas.addEventListener('mousedown', onDown); canvas.addEventListener('mouseup', onUp); canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('touchstart', onDown, {passive: false}); canvas.addEventListener('touchend', onUp); canvas.addEventListener('touchmove', onMove, {passive: false});

    function update() {
        if (hitStopTimer > 0) {
            hitStopTimer--;
            if (isKO || hitStopTimer > 3) { // 3回ヒットのテンポのために揺れを短く
                const shakePower = isKO ? 30 * (hitStopTimer/KO_HIT_STOP) : (WEAPON_TYPE === 'sword' ? 3 : 10);
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
            draw(); requestAnimationFrame(update); return;
        }

        if (WEAPON_TYPE === 'ball') {
            if (!black.isDragging) {
                black.vy += GRAVITY; black.vx *= FRICTION; black.vy *= FRICTION; black.x += black.vx; black.y += black.vy;
                if (black.x + black.radius > canvas.width) { black.x = canvas.width - black.radius; black.vx *= -BOUNCE; }
                else if (black.x - black.radius < 0) { black.x = black.radius; black.vx *= -BOUNCE; }
                if (black.y + black.radius > canvas.height) { black.y = canvas.height - black.radius; black.vy *= -BOUNCE; if(Math.abs(black.vy) < GRAVITY) black.vy = 0; } 
                else if (black.y - black.radius < 0) { black.y = black.radius; black.vy *= -BOUNCE; }
            }
        } else {
            // 剣の動き
            // 追従（スイング中は少し追従を遅くして「踏ん張り」感を出す）
            const followSpeed = black.isSwinging ? 0.05 : 0.2;
            black.x += (black.targetX - black.x) * followSpeed;
            black.y += (black.targetY - black.y) * followSpeed;
            
            if (black.isSwinging) {
                black.swingProgress += 1.0 / SWORD_SPEED;
                
                // スイング角度計算: -60度 から +60度 へ (合計120度)
                const startAngle = -SWORD_SWING_ANGLE / 2;
                const endAngle = SWORD_SWING_ANGLE / 2;
                
                // イージング（動きにメリハリをつける）
                // 振り始めは遅く、中間は速く
                const t = black.swingProgress;
                const easeT = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                
                const currentOffset = startAngle + (endAngle - startAngle) * easeT;
                black.angle = black.baseAngle + currentOffset;

                if (black.swingProgress >= 1.0) {
                    black.isSwinging = false; // スイング終了
                }
            } else {
                // 通常時はマウスの方を向く
                const dx = black.targetX - black.x;
                const dy = black.targetY - black.y;
                // 待機中は少し揺れる
                const idleAngle = Math.atan2(dy, dx);
                black.baseAngle = idleAngle;
                black.angle = idleAngle + Math.sin(Date.now() / 400) * 0.1; 
            }
        }

        if (white.visible) {
            let isHit = false; let damage = 0; let isCritical = false; let hitX = 0, hitY = 0;

            if (WEAPON_TYPE === 'ball') {
                const dx = black.x - white.x; const dy = black.y - white.y;
                const dist = Math.hypot(dx, dy); const minDist = black.radius + white.radius;
                if (dist < minDist) {
                    isHit = true; hitX = (black.x + white.x) / 2; hitY = (black.y + white.y) / 2;
                    const speed = Math.sqrt(black.vx**2 + black.vy**2);
                    damage = speed < 2 ? 5 : 5 + ((speed - 2) / 20) * 45;
                    if(damage > 50) damage = 50;
                    if(damage > 30) isCritical = true;
                    
                    const angle = Math.atan2(dy, dx); const overlap = minDist - dist;
                    black.x += Math.cos(angle) * overlap; black.y += Math.sin(angle) * overlap;
                    black.vx = Math.cos(angle) * (speed * 0.8 + 2); black.vy = Math.sin(angle) * (speed * 0.8 + 2);
                }
            } else {
                // ⚔️ 3段ヒット判定 ⚔️
                if (black.isSwinging) {
                    const dx = black.x - white.x; const dy = black.y - white.y;
                    const dist = Math.hypot(dx, dy);
                    
                    // リーチ内に入っているか
                    if (dist < SWORD_LENGTH + white.radius) {
                        // 現在のスイング段階 (0, 1, 2)
                        // 0: 始動(0-33%), 1: 中間(33-66%), 2: 終盤(66-100%)
                        let phase = Math.floor(black.swingProgress * 3);
                        if (phase > 2) phase = 2;

                        // まだその段階でヒットしていないならヒット！
                        if (!black.hitFlags[phase]) {
                            // 角度判定も入れる（後ろには当たらない）
                            // 剣の現在の角度と、敵への角度の差が一定以内なら
                            const angleToEnemy = Math.atan2(white.y - black.y, white.x - black.x);
                            let angleDiff = angleToEnemy - black.angle;
                            // 角度の正規化 (-PI ~ PI)
                            while (angleDiff > Math.PI) angleDiff -= Math.PI * 2;
                            while (angleDiff < -Math.PI) angleDiff += Math.PI * 2;
                            
                            // 剣の幅（扇形）の中にいるか？（大体45度以内）
                            if (Math.abs(angleDiff) < Math.PI / 3) {
                                isHit = true;
                                black.hitFlags[phase] = true; // この段階はヒット済みにする
                                hitX = white.x; hitY = white.y;
                                damage = 15; // 1発は軽め（3発で45）
                                isCritical = true;
                            }
                        }
                    }
                }
            }

            if (isHit) {
                if (!IS_INFINITE) white.hp -= damage;
                damagePopups.push(new DamagePopup(white.x, white.y - 40, damage, isCritical));

                if (WEAPON_TYPE === 'sword') {
                    // 斬撃エフェクト（ヒット時の角度で）
                    slashEffects.push(new SlashEffect(white.x, white.y, black.angle));
                }

                if (!IS_INFINITE && white.hp <= 0) {
                    isKO = true; white.hp = 0; hitStopTimer = KO_HIT_STOP;
                    for(let i=0; i<80; i++) particles.push(new Particle(white.x, white.y, true));
                } else {
                    // 連続ヒットのテンポを良くするため、ヒットストップは短めに
                    hitStopTimer = WEAPON_TYPE === 'sword' ? 4 : Math.floor(damage / 2); 
                    if (hitStopTimer < 3) hitStopTimer = 3;
                    const pCount = Math.floor(damage / 3) + 3;
                    for(let i=0; i<pCount; i++) {
                        particles.push(new Particle(hitX, hitY, false, isCritical ? '#00ffff' : '#FFD700'));
                    }
                }
            }
        }

        particles = particles.filter(p => p.life > 0); particles.forEach(p => p.update());
        damagePopups = damagePopups.filter(d => d.life > 0); damagePopups.forEach(d => d.update());
        slashEffects = slashEffects.filter(s => s.life > 0); slashEffects.forEach(s => s.update());
        draw(); requestAnimationFrame(update);
    }

    function draw() {
        ctx.save();
        ctx.translate(screenShakeX, screenShakeY);
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
        } else {
            // ⚔️ 聖剣描画
            ctx.save();
            ctx.translate(black.x, black.y);
            ctx.rotate(black.angle);
            
            ctx.shadowBlur = 15; ctx.shadowColor = '#00ffff'; 
            ctx.fillStyle = '#ccffff';
            ctx.beginPath();
            ctx.moveTo(-10, 0); 
            ctx.lineTo(10, 0);
            ctx.lineTo(0, -SWORD_LENGTH); // 剣先
            ctx.fill();
            
            ctx.shadowBlur = 0; ctx.fillStyle = '#555'; ctx.fillRect(-8, 0, 16, 25);
            ctx.fillStyle = '#888'; ctx.fillRect(-20, -5, 40, 10);
            
            ctx.restore();
        }

        if (hitStopTimer > 0) {
            ctx.lineWidth = 5;
            if(isKO) { ctx.strokeStyle = `rgba(255, 50, 50, ${Math.random()})`; ctx.lineWidth = 10; } 
            else { ctx.strokeStyle = 'rgba(0, 255, 255, 0.8)'; }
            let ringX = isKO ? white.x : (WEAPON_TYPE==='ball' ? (black.x + white.x)/2 : white.x);
            let ringY = isKO ? white.y : (WEAPON_TYPE==='ball' ? (black.y + white.y)/2 : white.y);
            const expansion = isKO ? (KO_HIT_STOP - hitStopTimer) : (30 - hitStopTimer) * 2;
            ctx.beginPath(); ctx.arc(ringX, ringY, black.radius + 20 + expansion, 0, Math.PI * 2); ctx.stroke();
        }

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
                               .replace("__WEAPON_TYPE__", weapon_type_js)

components.html(final_html_code, height=600, scrolling=False)
