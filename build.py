import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE, "src")
OUT = os.path.join(BASE, "index.html")

FILES = {
    "home": "home.html",
    "hojo": "hojo-3d.html",
    "kata": "kata.html",
    "warmup": "warmup.html",
    "glossary": "glossary.html",
    "generator": "generator.html",
}

def read(fn):
    with open(os.path.join(SRC_DIR, fn), encoding="utf-8") as f:
        return f.read()

def extract(tag, html):
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.S)
    return m.group(1) if m else ""

def extract_body(html):
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    return m.group(1) if m else ""

def strip_nav(body):
    return re.sub(r'<nav class="app-nav">.*?</nav>\s*', "", body, flags=re.S)

def strip_script(body):
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", body, re.S)
    body_wo = re.sub(r"<script[^>]*>.*?</script>\s*", "", body, flags=re.S)
    return body_wo, scripts

styles = []
scripts_all = []
views = {}

for key, fn in FILES.items():
    html = read(fn)
    styles.append(f"/* ---- {fn} ---- */\n" + extract("style", html))
    body = extract_body(html)
    body = strip_nav(body)
    body, scr = strip_script(body)
    scripts_all.extend(scr)
    views[key] = body.strip()

# --- fix internal cross-links ---
FILE_TO_VIEW = {v: k for k, v in FILES.items()}
FILE_TO_VIEW["index.html"] = "home"  # home.html's own links still say index.html/hojo-3d.html etc.
FILE_TO_VIEW["hojo-3d.html"] = "hojo"

def fix_home_links(body):
    def repl(m):
        fn = m.group(1)
        view = FILE_TO_VIEW.get(fn)
        if not view:
            return m.group(0)
        return f'href="#{view}" data-view="{view}"'
    return re.sub(r'href="([a-z0-9-]+\.html)"', repl, body)
views["home"] = fix_home_links(views["home"])

def linkify_title(body):
    return re.sub(
        r'<div class="main-title">(.*?)</div>',
        r'<a href="#home" data-view="home" class="logo-link"><div class="main-title">\1</div></a>',
        body, count=1, flags=re.S
    )

for key in views:
    if key != "home":
        views[key] = linkify_title(views[key])

# dedupe the @import font line -- keep only first occurrence
seen_import = False
cleaned_styles = []
for block in styles:
    lines = block.split("\n")
    out_lines = []
    for line in lines:
        if "@import url" in line:
            if seen_import:
                continue
            seen_import = True
        out_lines.append(line)
    cleaned_styles.append("\n".join(out_lines))

router_css = """
.view{display:none;}
.view.active{display:block;}

/* ---- minimal traditional redesign: flatten decoration, one accent color ---- */
header{padding:1.3rem 1rem .9rem;}
.main-title{font-size:2rem;letter-spacing:.3em;}
.sub-title{letter-spacing:.05em;}
.dojo-line{letter-spacing:.05em;}

.nav-bar{
  display:flex;align-items:center;justify-content:space-between;gap:.6rem;
  padding:.6rem 1rem;position:relative;z-index:50;
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
}
.nav-toggle{
  display:flex;justify-content:center;align-items:center;
  width:40px;height:40px;padding:0;border:1px solid var(--border);background:var(--card);
  cursor:pointer;flex-shrink:0;
}
.nav-toggle-bar{position:relative;width:20px;height:2px;background:var(--w);transition:transform .15s,opacity .15s,background .15s;}
.nav-toggle-bar::before,.nav-toggle-bar::after{content:"";position:absolute;right:0;width:20px;height:2px;background:var(--w);transition:transform .15s,background .15s;}
.nav-toggle-bar::before{transform:translateY(-6px);}
.nav-toggle-bar::after{transform:translateY(6px);}
.nav-toggle:hover .nav-toggle-bar,.nav-toggle:hover .nav-toggle-bar::before,.nav-toggle:hover .nav-toggle-bar::after{background:var(--gold);}
.nav-toggle[aria-expanded="true"] .nav-toggle-bar{background:transparent;}
.nav-toggle[aria-expanded="true"] .nav-toggle-bar::before{transform:translateY(0) rotate(45deg);}
.nav-toggle[aria-expanded="true"] .nav-toggle-bar::after{transform:translateY(0) rotate(-45deg);}
.nav-toggle:focus-visible{outline:2px solid var(--blue);outline-offset:2px;}

.nav-cta{
  color:var(--card);background:var(--gold);text-decoration:none;font-size:.82rem;font-weight:700;
  padding:.55rem 1.1rem;border:1px solid var(--gold);white-space:nowrap;transition:background .15s,border-color .15s;
}
.nav-cta:hover{background:#7d5b14;border-color:#7d5b14;}
.nav-cta.active{box-shadow:inset 0 0 0 2px var(--red);}
.nav-cta:focus-visible{outline:2px solid var(--blue);outline-offset:2px;}

.nav-dropdown{
  position:absolute;top:100%;right:1rem;
  min-width:200px;max-width:calc(100vw - 2rem);
  background:var(--card);border:1px solid var(--border);
  box-shadow:0 4px 14px rgba(0,0,0,.18);
  z-index:60;
}
.nav-dropdown[hidden]{display:none;}
.nav-dropdown ul{list-style:none;margin:0;padding:.4rem 0;}
.nav-dropdown a{
  display:block;padding:.65rem 1.1rem;color:var(--w);text-decoration:none;font-size:.85rem;
  border-right:3px solid transparent;transition:background .15s,border-color .15s,color .15s;
}
.nav-dropdown a:hover{background:#f3e6c4;border-right-color:var(--gold);color:var(--gold);}
.nav-dropdown a.active{background:#f3e6c4;color:var(--gold);border-right-color:var(--red);font-weight:700;}
.nav-dropdown a:focus-visible{outline:2px solid var(--blue);outline-offset:-2px;background:#f3e6c4;}

@media(max-width:420px){
  .nav-dropdown{right:.5rem;min-width:180px;}
}

header a.logo-link{color:inherit;text-decoration:none;display:inline-block;}
header a.logo-link:hover .main-title{opacity:.75;}
header a.logo-link:focus-visible{outline:2px solid var(--blue);outline-offset:4px;}

.card,.term,.step,.kata,.b-card,.exercise{border-radius:0;}
.card:hover{transform:none;box-shadow:none;}
.cat-btn,.search-box,.reset-btn,.belt-chip,.k-belt,.formal-tag,.s-dur,.weapon-tag{border-radius:0;}
.real-ref .rr-frame{border-radius:0;}
.video-wrap,.video-wrap img{border-radius:0;}
.play-overlay span{border-radius:0;width:auto;height:auto;background:none;box-shadow:none;
  color:#fff;font-size:2.4rem;padding:0;}
.video-wrap:hover .play-overlay span{background:none;transform:none;color:var(--red);}
.s-check{border-radius:0;}

/* ---- parchment texture + faint per-section kanji watermark ---- */
body{
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 15% 20%, rgba(120,90,40,.05) 0%, transparent 42%),
    radial-gradient(circle at 85% 15%, rgba(120,90,40,.04) 0%, transparent 38%),
    radial-gradient(circle at 75% 80%, rgba(120,90,40,.05) 0%, transparent 45%),
    radial-gradient(circle at 25% 85%, rgba(80,60,20,.04) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(0,0,0,.02) 0%, transparent 65%);
  background-attachment:fixed;
}
.view{position:relative;}
.view::before{
  position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
  font-family:'Noto Serif JP',serif;font-size:22rem;line-height:1;white-space:nowrap;
  color:var(--gold);opacity:.07;pointer-events:none;user-select:none;
}
#view-home::before{content:"上地流";}
#view-hojo::before{content:"補助運動";font-size:14rem;}
#view-kata::before{content:"型";}
#view-warmup::before{content:"準備運動";font-size:14rem;}
#view-glossary::before{content:"用語集";}
#view-generator::before{content:"稽古";}
"""

router_js = """
function showView(name){
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  const target = document.getElementById('view-'+name);
  if(!target) return;
  target.classList.add('active');
  document.querySelectorAll('.nav-cta[data-view], #navDropdown a[data-view]').forEach(a=>{
    a.classList.toggle('active', a.dataset.view===name);
  });
  closeNavDropdown();
  window.scrollTo(0,0);
}
function jumpTo(view,id){
  showView(view);
  history.pushState(null,'','#'+view);
  setTimeout(()=>{
    const el=document.getElementById(id);
    if(el) el.scrollIntoView({behavior:'smooth', block:'start'});
  }, 60);
  return false;
}
document.addEventListener('click', function(e){
  const a = e.target.closest('[data-view]');
  if(!a) return;
  e.preventDefault();
  const v = a.dataset.view;
  showView(v);
  history.pushState(null,'','#'+v);
});
window.addEventListener('hashchange', function(){
  const v = (location.hash||'#home').replace('#','');
  if(document.getElementById('view-'+v)) showView(v);
});

const navToggleBtn = document.getElementById('navToggle');
const navDropdownEl = document.getElementById('navDropdown');
function openNavDropdown(){
  if(!navDropdownEl) return;
  navDropdownEl.hidden = false;
  navToggleBtn.setAttribute('aria-expanded','true');
}
function closeNavDropdown(){
  if(!navDropdownEl || navDropdownEl.hidden) return;
  navDropdownEl.hidden = true;
  navToggleBtn.setAttribute('aria-expanded','false');
}
if(navToggleBtn && navDropdownEl){
  navToggleBtn.addEventListener('click', function(e){
    e.stopPropagation();
    if(navDropdownEl.hidden) openNavDropdown(); else closeNavDropdown();
  });
  navDropdownEl.addEventListener('click', function(e){
    if(e.target.closest('[data-view]')) closeNavDropdown();
  });
  document.addEventListener('click', function(e){
    if(navDropdownEl.hidden) return;
    if(navDropdownEl.contains(e.target) || e.target===navToggleBtn || navToggleBtn.contains(e.target)) return;
    closeNavDropdown();
  });
  document.addEventListener('keydown', function(e){
    if(e.key==='Escape' && !navDropdownEl.hidden){
      closeNavDropdown();
      navToggleBtn.focus();
    }
  });
}

(function(){
  const initial = (location.hash||'#home').replace('#','');
  showView(document.getElementById('view-'+initial) ? initial : 'home');
})();
"""

nav_html = """
<div class="nav-bar">
  <button type="button" id="navToggle" class="nav-toggle" aria-expanded="false" aria-controls="navDropdown" aria-label="פתיחת תפריט ניווט">
    <span class="nav-toggle-bar"></span>
  </button>
  <a href="#generator" data-view="generator" class="nav-cta">מחולל אימון</a>
  <div id="navDropdown" class="nav-dropdown" hidden>
    <nav aria-label="ניווט בין דפי האפליקציה">
      <ul>
        <li><a href="#hojo" data-view="hojo">הוג'ו אונדו</a></li>
        <li><a href="#kata" data-view="kata">קאטות</a></li>
        <li><a href="#warmup" data-view="warmup">חימום</a></li>
        <li><a href="#glossary" data-view="glossary">מילון</a></li>
      </ul>
    </nav>
  </div>
</div>
"""

view_order = ["home", "hojo", "kata", "warmup", "glossary", "generator"]
sections_html = "\n".join(
    f'<section class="view{" active" if key=="home" else ""}" id="view-{key}">\n{views[key]}\n</section>'
    for key in view_order
)

final_html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>אוצ'י ריו – מדריך אימון | Uechi-Ryu Training Companion</title>
<style>
{''.join(cleaned_styles)}
{router_css}
.noscript-warn{{background:#1a0808;border:1px solid #3a1010;border-right:4px solid var(--red);margin:1rem auto;max-width:900px;padding:.8rem 1rem;font-size:.8rem;color:#e8b8b0;}}
</style>
</head>
<body>
<noscript><div class="noscript-warn">האפליקציה דורשת JavaScript לניווט בין החלקים. פתחו את הקובץ בדפדפן רגיל (כרום/אדג'/פיירפוקס) ולא בתצוגה מקוצרת.</div></noscript>
{nav_html}
{sections_html}
<script>
{chr(10).join(scripts_all)}
{router_js}
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(final_html)

print("written:", OUT, len(final_html), "chars")
