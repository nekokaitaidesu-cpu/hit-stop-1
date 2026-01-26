import streamlit as st
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="ヒットストップ体験実験室", layout="centered")

st.title("🥊 ヒットストップ体験実験室")
st.caption("桜井政博さんの動画で解説されていた「ヒットストップ」と「振動」の効果を体験するっち！🍄")

# --- サイドバーでパラメータ調整 ---
st.sidebar.header("🔧 設定パラメータ")

hit_stop_duration = st.sidebar.slider(
    "⏱️ ヒットストップ時間 (ミリ秒)",
    min_value=0,
    max_value=500,
    value=150,
    step=10,
    help="攻撃が当たった瞬間に時が止まる長さだっち。"
)

shake_intensity = st.sidebar.slider(
    "🫨 振動の強さ (ピクセル)",
    min_value=0,
    max_value=20,
    value=5,
    step=1,
    help="ヒットストップ中にキャラクターがガクガク揺れる幅だっち。"
)

shake_victim_only = st.sidebar.checkbox(
    "対象のみ揺らす (動画のこだわり)",
    value=True,
    help="動画で言っていた「攻撃側は揺らさず、やられた側だけ揺らす」設定だっち。"
)

st.sidebar.markdown("---")
st.sidebar.info("設定を変えたら、画面内の「RELOAD」ボタンか、攻撃ボタンを押して試してみてね！")

# --- ゲーム画面 (HTML/JS) の埋め込み ---
# Pythonの変数をJSに渡すためにf-stringを使うっち
html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; background-color: #222; color: white; font-family: sans-serif; overflow: hidden; }}
  #game-container {{
    position: relative;
    width: 600px;
    height: 300px;
    background-color: #333;
    border: 2px solid #555;
    margin: 0 auto;
    border-radius: 8px;
  }}
  .character {{
    position: absolute;
    width: 50px;
    height: 50px;
    bottom: 50px;
    border-radius: 4px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 24px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  }}
  #attacker {{ left: 50px; background-color: #ff4b4b; z-index: 2; }} /* Streamlit Red */
  #defender {{ right: 50px; background-color: #4b9bff; z-index: 1; }} /* Streamlit Blue */
  
  #controls {{ text-align: center; margin-top: 10px; }}
  button {{
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
    background-color: #ff4b4b;
    color: white;
    border: none;
    border-radius: 4px;
  }}
  button:hover {{ background-color: #ff2b2b; }}
  
  .impact-effect {{
    position: absolute;
    width: 80px;
    height: 80px;
    background: radial-gradient(circle, rgba(255,255,0,1) 0%, rgba(255,0,0,0) 70%);
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, -50%);
    z-index: 10;
  }}
</style>
</head>
<body>

<div id="game-container">
  <div id="attacker" class="character">👊</div>
  <div id="defender" class="character">😧</div>
  <div id="effect" class="impact-effect"></div>
</div>

<div id="controls">
  <button onclick="startAttack()">アタック！ (Spaceキー)</button>
  <p style="font-size: 12px; color: #aaa;">現在の設定: 停止 {hit_stop_duration}ms / 揺れ {shake_intensity}px</p>
</div>

<script>
  // Pythonから受け取ったパラメータ
  const HIT_STOP_MS = {hit_stop_duration};
  const SHAKE_INTENSITY = {shake_intensity};
  const SHAKE_VICTIM_ONLY = {'true' if shake_victim_only else 'false'};

  const attacker = document.getElementById('attacker');
  const defender = document.getElementById('defender');
  const effect = document.getElementById('effect');
  
  let animationId = null;
  let isAttacking = false;
  let isHitStopping = false;
  
  // 初期位置
  const startX = 50;
  const targetX = 450; // 衝突位置
  let currentX = startX;
  const speed = 15; // 移動速度

  function startAttack() {{
    if (isAttacking) return;
    isAttacking = true;
    currentX = startX;
    attacker.style.left = currentX + 'px';
    defender.style.transform = 'translate(0, 0)';
    attacker.style.transform = 'translate(0, 0)';
    effect.style.opacity = 0;
    
    loop();
  }}

  function loop() {{
    if (isHitStopping) {{
      // ヒットストップ中：振動処理
      // ランダムに位置をずらす（動画の解説通り、元の位置はずらさず描画位置だけずらすイメージ）
      const shakeX = (Math.random() - 0.5) * SHAKE_INTENSITY * 2;
      const shakeY = (Math.random() - 0.5) * SHAKE_INTENSITY * 2;
      
      defender.style.transform = `translate(${{shakeX}}px, ${{shakeY}}px)`;
      
      if (!SHAKE_VICTIM_ONLY) {{
         // 攻撃側も揺らす場合（少し弱めに）
         const attShakeX = (Math.random() - 0.5) * (SHAKE_INTENSITY/2);
         const attShakeY = (Math.random() - 0.5) * (SHAKE_INTENSITY/2);
         attacker.style.transform = `translate(${{attShakeX}}px, ${{attShakeY}}px)`;
      }}
      
      animationId = requestAnimationFrame(loop);
      return;
    }}

    // 移動処理
    currentX += speed;
    
    // 衝突判定（簡易）
    if (currentX >= targetX - 50) {{ // 50は幅
      onHit();
    }} else {{
      attacker.style.left = currentX + 'px';
      
      // 画面外に出たらリセット
      if (currentX > 600) {{
        isAttacking = false;
        currentX = startX;
        attacker.style.left = startX + 'px';
        return; 
      }}
      animationId = requestAnimationFrame(loop);
    }}
  }}

  function onHit() {{
    // 衝突位置に固定
    currentX = targetX - 50; 
    attacker.style.left = currentX + 'px';
    
    // エフェクト表示
    effect.style.left = (targetX - 25) + 'px';
    effect.style.top = (300 - 75) + 'px'; // 高さ調整
    effect.style.opacity = 1;

    // ヒットストップ開始！
    isHitStopping = true;
    
    setTimeout(() => {{
      // ヒットストップ終了
      isHitStopping = false;
      effect.style.opacity = 0;
      defender.style.transform = 'translate(0, 0)';
      attacker.style.transform = 'translate(0, 0)';
      
      // 吹き飛び（簡易アニメ）
      knockback();
    }}, HIT_STOP_MS);
  }}

  function knockback() {{
    // やられた側が少し下がる演出
    defender.style.transition = 'transform 0.2s';
    defender.style.transform = 'translateX(50px) rotate(10deg)';
    
    // 攻撃側はそのまま走り抜ける
    const finishRun = () => {{
      currentX += speed;
      attacker.style.left = currentX + 'px';
      if (currentX < 650) {{
        requestAnimationFrame(finishRun);
      }} else {{
        isAttacking = false;
        defender.style.transition = 'none';
        defender.style.transform = 'translate(0, 0)';
        currentX = startX;
        attacker.style.left = startX + 'px';
      }}
    }};
    finishRun();
  }}

  // スペースキーで攻撃
  document.addEventListener('keydown', (e) => {{
    if (e.code === 'Space') startAttack();
  }});

</script>
</body>
</html>
"""

# HTMLを描画（高さを確保）
components.html(html_code, height=400)

st.write("### 💡 体験のヒント")
st.write(f"""
1.  まずはそのまま**「アタック！」**ボタンを押してみてっち。
2.  左のサイドバーで**「ヒットストップ時間」を 0** にしてみてっち。
    * → ヌルっと通り過ぎて、すごく軽く感じるはずだっち。これが「手応えがない」状態だっち。
3.  **「ヒットストップ時間」を 300ms** くらいに増やしてみてっち。
    * → 「重い！」と感じるはずだっち。これが攻撃力の表現になるっち。
4.  **「対象のみ揺らす」**のチェックを外すと、両方揺れるっち。
    * → 動画で言っていた「自分が揺れると位置ズレして見える」問題がなんとなくわかるかもしれないっち。
""")
