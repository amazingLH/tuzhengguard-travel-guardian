"""Lightweight, accessible motion for the travel workbench."""

from html import escape


def hero_html(title: str) -> str:
    return f"""<div class="hero mission-hero">
      <div class="hero-copy"><span class="mission-eyebrow">TUZHENGGUARD / TRAVEL MISSION CONTROL</span>
        <h1>{escape(title)}</h1>
        <p>把行程截图变成 TripGraph，结合真实 FlyAI 与高德 MCP 证据发现衔接、日期、预算、天气和体力风险，并生成可验证 Plan B。</p>
        <div class="mission-tags"><span>行程数字孪生</span><span>证据驱动核验</span><span>可解释 Plan B</span></div>
      </div>
      <div class="travel-cosmos" aria-hidden="true">
        <div class="cosmos-grid"></div><div class="orbit orbit-one"><i></i></div><div class="orbit orbit-two"><i></i></div>
        <span class="cosmos-star star-one">✦</span><span class="cosmos-star star-two">✧</span><span class="cosmos-star star-three">✦</span>
        <div class="travel-bot"><div class="bot-antenna"></div><div class="bot-ears"></div>
          <div class="bot-head"><div class="bot-visor"><i></i><i></i><b></b></div><span class="bot-cheek cheek-left"></span><span class="bot-cheek cheek-right"></span></div>
          <div class="bot-body"><span>✦</span></div><div class="bot-hand"></div><div class="bot-thrust"></div>
        </div><div class="cosmos-platform"></div><div class="cosmos-label">陪你探索每一程</div>
      </div>
    </div>"""


WORKBENCH_CSS = """
/* A dedicated history column, with a native drawer on compact screens. */
#session-management {box-sizing:border-box;background:linear-gradient(170deg,#f3f0ff,#e8f3ff)!important;border-right:1px solid #cbd9f2!important;padding:18px 14px!important;color:#253651}
#session-management .sidebar-content {gap:14px;padding:12px 16px 20px 0!important}
#session-management h2 {font-size:20px;color:#5641cc;margin:4px 0 12px}
#session-management .prose {color:#53617b;font-size:13px;overflow-wrap:anywhere}
#session-management .block.session-current {padding:12px;background:#ffffff90;border:1px solid #dedaf6;border-radius:12px}
#session-management .session-current strong {color:#35415d}
#session-management #new-session-button {background:linear-gradient(115deg,#6250df,#7751d9)!important;color:white!important;border:0!important;box-shadow:0 6px 16px #6552d526;min-height:44px}
#history-select {background:transparent;border:0;padding:0;min-width:0!important}
#history-select > .wrap:not([data-testid="status-tracker"]) {display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;gap:8px!important;max-height:48vh;overflow-y:auto;overflow-x:hidden;padding:2px;box-sizing:border-box}
#history-select label {width:100%;box-sizing:border-box;min-width:0!important;border:1px solid #d8d9ee!important;background:#ffffffa8!important;border-radius:12px!important;padding:12px 10px!important;transition:border-color .2s,background .2s}
#history-select label:has(input:checked) {background:#e9e3ff!important;border-color:#8970ed!important;box-shadow:0 0 0 1px #8970ed30}
#history-select label {flex:0 0 auto!important}
#history-select label span {min-width:0;white-space:pre-line!important;overflow-wrap:anywhere;font-size:13px!important;color:#35415d!important;line-height:1.65}
#history-select input {accent-color:#7352da;flex-shrink:0}
#session-management .history-help {font-size:12px;color:#68758b}
#session-management .history-tools button {font-size:12px;min-height:34px}
#session-management .history-tools {min-width:0!important;overflow-x:hidden!important}
@media(max-width:768px) {#session-management {width:100%!important;left:-100%!important}}
.mission-hero {display:flex;align-items:center;gap:20px;min-height:240px;padding:28px 32px!important}
.hero-copy {flex:1;min-width:0;position:relative;z-index:1}
.mission-eyebrow {font-size:10px;letter-spacing:2px;color:#9ddded;font-weight:600}
.mission-hero h1 {font-size:clamp(23px,2.6vw,32px);line-height:1.5;margin:12px 0 10px}
.mission-hero p {font-size:14px;max-width:650px;line-height:1.9}
.mission-tags {display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
.mission-tags span {font-size:11px;color:#cae6fa;padding:4px 10px;border:1px solid #8dcfff40;background:#76c6ff10;border-radius:20px}
.travel-cosmos {position:relative;flex:0 0 216px;height:216px;pointer-events:none}
.cosmos-grid {position:absolute;inset:12px;border-radius:50%;background:radial-gradient(circle,#63c4e62b,transparent 66%);border:1px solid #a4e9ff16}
.orbit {position:absolute;border:1px solid #8eddf344;border-radius:50%;inset:15px;transform:rotate(-28deg) scaleY(.62)}
.orbit-two {inset:0 28px;transform:rotate(32deg) scaleY(.72);border-style:dashed;border-color:#b6a6ff44}
.orbit i {position:absolute;width:7px;height:7px;background:#7ce7ff;box-shadow:0 0 15px #7ce7ff;border-radius:50%;left:50%;top:-4px;transform-origin:0 94px;animation:orbit-drift 18s linear infinite}
.orbit-two i {background:#d2b8ff;animation-duration:24s;animation-direction:reverse}
.travel-bot {position:absolute;left:61px;top:47px;width:94px;height:120px;animation:bot-hover 4s ease-in-out infinite}
.bot-head {position:relative;width:92px;height:67px;border-radius:25px;background:linear-gradient(145deg,#f7fcff,#b4d0e6);border:2px solid #e2f6ff;box-shadow:inset -5px -5px 10px #628cb333,0 0 28px #84d9ff30;z-index:2}
.bot-visor {position:absolute;left:12px;right:12px;top:15px;height:35px;background:linear-gradient(130deg,#182b4b,#244d69);border-radius:15px;overflow:hidden;display:flex;align-items:center;justify-content:center;gap:18px}
.bot-visor::after {content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent,#b3efff30,transparent);transform:translateX(-110%);animation:visor-scan 6s ease-in-out infinite}
.bot-visor i {display:block;width:8px;height:13px;border-radius:6px;background:#82ecff;box-shadow:0 0 8px #7ce7ff80;animation:bot-blink 6s ease-in-out infinite}
.bot-visor b {position:absolute;bottom:5px;width:10px;height:4px;border-bottom:2px solid #82ecff;border-radius:0 0 8px 8px}
.bot-cheek {position:absolute;width:8px;height:3px;background:#efa4c0;border-radius:50%;bottom:10px}.cheek-left {left:8px}.cheek-right {right:8px}
.bot-antenna {position:absolute;top:-15px;left:45px;width:3px;height:16px;background:#9acff0}.bot-antenna::after {content:"";position:absolute;top:-5px;left:-3px;width:9px;height:9px;border-radius:50%;background:#aaf2ff;box-shadow:0 0 15px #84eaff;animation:star-pulse 3s infinite}
.bot-ears {position:absolute;top:26px;left:-7px;width:106px;height:20px;background:#96c5df;border:2px solid #c8edff;border-radius:8px}
.bot-body {position:absolute;left:23px;top:65px;width:48px;height:39px;background:linear-gradient(140deg,#e1effc,#93b5d8);border:2px solid #d3eeff;border-radius:12px 12px 20px 20px;text-align:center;color:#5e65bd;z-index:1}
.bot-body span {font-size:23px;line-height:31px}
.bot-hand {position:absolute;top:71px;right:-7px;width:16px;height:30px;background:#c8e4fa;border:2px solid #e1f5ff;border-radius:10px;transform-origin:bottom center;animation:bot-wave 5s ease-in-out infinite}
.bot-thrust {position:absolute;top:103px;left:37px;width:22px;height:19px;border-radius:0 0 50% 50%;background:linear-gradient(#7de9ff99,transparent);filter:blur(3px)}
.cosmos-platform {position:absolute;left:57px;bottom:23px;width:103px;height:18px;border:1px solid #80def95c;border-radius:50%;background:#7ce7ff10;box-shadow:0 0 20px #7ce7ff12;animation:platform-pulse 4s ease-in-out infinite}
.cosmos-label {position:absolute;bottom:0;width:100%;text-align:center;font-size:11px;letter-spacing:2px;color:#bbd6ed}
.cosmos-star {position:absolute;color:#baeafa;font-size:14px;animation:star-pulse 4s ease-in-out infinite}.star-one {top:22px;left:37px}.star-two {top:70px;right:8px;animation-delay:1s}.star-three {bottom:49px;left:11px;font-size:9px;animation-delay:2s}
@keyframes bot-hover {0%,100% {transform:translateY(0) rotate(-2deg)}50% {transform:translateY(-9px) rotate(2deg)}}
@keyframes bot-blink {0%,43%,49%,100% {transform:scaleY(1)}46% {transform:scaleY(.15)}}
@keyframes bot-wave {0%,65%,100% {transform:rotate(-18deg)}72%,86% {transform:rotate(-42deg)}79%,93% {transform:rotate(-12deg)}}
@keyframes visor-scan {0%,60% {transform:translateX(-110%)}90%,100% {transform:translateX(110%)}}
@keyframes orbit-drift {to {rotate:360deg}}
@keyframes star-pulse {0%,100% {opacity:.45}50% {opacity:1}}
@keyframes platform-pulse {0%,100% {transform:scaleX(1);opacity:.5}50% {transform:scaleX(.8);opacity:1}}
@media(max-width:900px) {.mission-hero {padding:24px!important;gap:12px}.travel-cosmos {flex-basis:164px;transform:scale(.82);margin:-18px -20px}.mission-eyebrow {letter-spacing:1px;font-size:9px}}
@media(max-width:640px) {.mission-hero {display:block;min-height:0}.travel-cosmos {width:216px;height:216px;transform:scale(.8);transform-origin:center;margin:-12px auto -24px}.hero-copy {display:contents}.mission-hero h1 {font-size:23px}.mission-hero p {font-size:13px}.mission-tags {margin-top:12px;gap:5px}.mission-eyebrow {font-size:8px}}
@media(prefers-reduced-motion:reduce) {.travel-cosmos * {animation:none!important;transition:none!important}}
"""
