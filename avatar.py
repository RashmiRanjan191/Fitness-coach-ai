import html
import streamlit.components.v1 as components

def render_avatar(text: str, height: int = 400):
    safe_text = html.escape(text or "Hello! I'm Kinetic Coach.")
    component = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    font-family: Inter, Arial, sans-serif;
    background: transparent;
}}
.wrapper {{
    width: 100%;
    min-height: {height - 10}px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 18px;
}}
.avatar {{
    width: 190px;
    height: 230px;
    position: relative;
    animation: float 3s ease-in-out infinite;
}}
.head {{
    width: 150px;
    height: 150px;
    border-radius: 50%;
    background: linear-gradient(145deg, #f3c7a6, #d99370);
    position: absolute;
    left: 20px;
    top: 12px;
    box-shadow: inset -8px -10px 0 rgba(0,0,0,.05);
}}
.hair {{
    width: 145px;
    height: 66px;
    background: #1f2937;
    border-radius: 80px 80px 25px 25px;
    position: absolute;
    top: 3px;
    left: 23px;
}}
.eye {{
    width: 15px;
    height: 15px;
    background: #18212b;
    border-radius: 50%;
    position: absolute;
    top: 76px;
    animation: blink 4s infinite;
}}
.eye.left {{ left: 55px; }}
.eye.right {{ right: 55px; }}
.mouth {{
    width: 42px;
    height: 17px;
    border-bottom: 4px solid #7b3f35;
    border-radius: 0 0 50% 50%;
    position: absolute;
    left: 54px;
    top: 108px;
    animation: talk .7s ease-in-out infinite alternate;
}}
.ear {{
    width: 22px;
    height: 35px;
    border-radius: 50%;
    background: #e3a37f;
    position: absolute;
    top: 73px;
}}
.ear.left {{ left: 7px; }}
.ear.right {{ right: 7px; }}
.body {{
    width: 155px;
    height: 110px;
    border-radius: 80px 80px 25px 25px;
    background: linear-gradient(145deg, #1f5f8b, #102a43);
    position: absolute;
    left: 18px;
    top: 135px;
}}
.logo {{
    position: absolute;
    left: 58px;
    top: 38px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255,255,255,.16);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
}}
.bubble {{
    width: min(92%, 500px);
    background: white;
    border: 1px solid #dce7ef;
    border-radius: 18px;
    padding: 14px 16px;
    color: #23384d;
    box-shadow: 0 6px 20px rgba(16,42,67,.08);
    line-height: 1.45;
    font-size: 14px;
}}
button {{
    border: 0;
    border-radius: 999px;
    padding: 9px 15px;
    background: #102a43;
    color: white;
    cursor: pointer;
    font-weight: 700;
}}
button:hover {{ opacity: .9; }}
@keyframes float {{
    0%,100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-7px); }}
}}
@keyframes blink {{
    0%, 46%, 50%, 100% {{ transform: scaleY(1); }}
    48% {{ transform: scaleY(.1); }}
}}
@keyframes talk {{
    from {{ height: 10px; }}
    to {{ height: 20px; }}
}}
</style>
</head>
<body>
<div class="wrapper">
    <div class="avatar">
        <div class="hair"></div>
        <div class="head">
            <div class="ear left"></div>
            <div class="ear right"></div>
            <div class="eye left"></div>
            <div class="eye right"></div>
            <div class="mouth"></div>
        </div>
        <div class="body"><div class="logo">K</div></div>
    </div>
    <div class="bubble">{safe_text}</div>
    <button onclick="speak()">🔊 Speak</button>
</div>
<script>
const text = document.querySelector('.bubble').innerText;
function speak() {{
    if (!('speechSynthesis' in window)) {{
        alert('Speech synthesis is not supported in this browser.');
        return;
    }}
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 0.96;
    u.pitch = 1.02;
    window.speechSynthesis.speak(u);
}}
</script>
</body>
</html>
"""
    components.html(component, height=height, scrolling=False)
