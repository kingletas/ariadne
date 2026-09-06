import html
import json

# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------

PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — Ariadne</title>
<style>
/* Tokens, from 05 Personal/09 UX Guide -- tokens.dtcg.json, web profile.
   Nothing below this block may use a literal colour. */
:root{
 --bg:#FAFAF8; --surface:#F1F2EF; --recessed:#E4E6E1; --rule:#D8DBD6; --hover:#E4E6E1;
 --text:#1A1E1C; --text-2:#616862; --text-3:#868C86;
 --accent:#1F6F5C; --accent-hover:#175A4A; --accent-text:#12463A; --on-accent:#FFFFFF;
 --focus:#1F6F5C; --selection:#CDE6DD; --on-selection:#12463A;
 --caution:#8A6410; --caution-bg:#FBF2DC; --danger-text:#A33A2A;
 /* Rule 9 wants 3:1 on an interactive boundary and --rule gives 1.24:1.
    neutral.500 is the lightest value in the file that clears it. */
 --edge:#868C86;
 --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px;
 --r-sm:4px; --r-md:8px; --r-lg:12px; --r-full:9999px;
 --ring:2px; --ring-offset:2px; --border:1px;
 --control:40px; --touch:44px;
 --ui:'Ubuntu Sans',Cantarell,'Segoe UI Variable','Segoe UI',system-ui,'DejaVu Sans',sans-serif;
 --content:'Atkinson Hyperlegible Next','Atkinson Hyperlegible','Ubuntu Sans',system-ui,sans-serif;
}
@media(prefers-color-scheme:dark){:root{
 --bg:#1A1E1C; --surface:#2E3330; --recessed:#101312; --rule:#454B47; --hover:#454B47;
 --text:#FAFAF8; --text-2:#B0B5AF; --text-3:#868C86;
 --accent-text:#6BB09C; --focus:#6BB09C; --selection:#12463A; --on-selection:#CDE6DD;
 --caution:#E5B84B; --caution-bg:#2E3330; --danger-text:#E88E7B;
 --edge:#868C86;
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
 font:1rem/1.5 var(--content);-webkit-text-size-adjust:100%}

/* Rule 11 -- focus visible on everything focusable, never removed. */
a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible{
 outline:var(--ring) solid var(--focus);outline-offset:var(--ring-offset);border-radius:var(--r-sm)}

.skip{position:absolute;left:var(--s2);top:calc(var(--s2) * -8);z-index:20;
 display:inline-flex;align-items:center;min-height:var(--control);
 background:var(--surface);color:var(--text);border:var(--border) solid var(--edge);
 border-radius:var(--r-sm);padding:var(--s2) var(--s3);font:1rem/1.5 var(--ui)}
.skip:focus{top:var(--s2)}
/* Rule 10 outranks the 40px control token the moment the surface is touched:
   44 is a floor, not an upgrade. */
@media(max-width:767px){#q,.skip{min-height:var(--touch)}}

header{position:sticky;top:0;background:var(--bg);border-bottom:var(--border) solid var(--rule);
 padding:var(--s3) var(--s4);z-index:5}
h1{margin:0 0 var(--s1);font:600 1.5rem/1.333 var(--ui);letter-spacing:-0.01em}
.sub{color:var(--text-2);font:0.875rem/1.429 var(--ui)}
.pos{display:flex;align-items:center;gap:var(--s3);margin-top:var(--s3)}
input[type=range]{flex:1;accent-color:var(--accent);height:var(--touch);margin:0}
.chip{font:600 0.875rem/1.429 var(--ui);background:var(--selection);color:var(--on-selection);
 padding:var(--s2) var(--s3);border-radius:var(--r-full);white-space:nowrap}

main{padding:var(--s4);max-width:760px;margin:0 auto}
.count{color:var(--text-2);font:0.875rem/1.429 var(--ui);margin:0 0 var(--s3)}

.field{display:block;margin:0 0 var(--s3)}
.field span{display:block;font:0.875rem/1.429 var(--ui);color:var(--text-2);margin-bottom:var(--s1)}
#q{width:100%;height:var(--control);font:1rem/1.5 var(--ui);color:var(--text);
 background:var(--surface);border:var(--border) solid var(--edge);border-radius:var(--r-sm);
 padding:0 var(--s3);-webkit-appearance:none}

.filters{display:flex;gap:var(--s2);margin:0 0 var(--s4);flex-wrap:wrap}
.filters button{font:0.875rem/1.429 var(--ui);background:var(--surface);color:var(--text-2);
 border:var(--border) solid var(--edge);border-radius:var(--r-sm);
 min-height:var(--touch);padding:0 var(--s3);cursor:pointer}
.filters button:hover{background:var(--hover);color:var(--text)}
.filters button[aria-pressed=true]{background:var(--selection);color:var(--on-selection);
 border-color:var(--accent);font-weight:600}

/* Rule 5 -- a dense list is a bordered surface with internal rules; under 768px,
   where a row is touched rather than pointed at, it becomes separated cards. */
#list{border:var(--border) solid var(--rule);border-radius:var(--r-md);
 background:var(--surface);overflow:hidden}
.card{padding:var(--s3) var(--s4);border-bottom:var(--border) solid var(--rule)}
.card:last-child{border-bottom:0}
@media(max-width:767px){
 #list{border:0;background:none;border-radius:0}
 .card{background:var(--surface);border:var(--border) solid var(--rule);
  border-radius:var(--r-md);margin-bottom:var(--s2)}
 .card:last-child{border-bottom:var(--border) solid var(--rule)}
}
.name{font-weight:600}
.meta{color:var(--text-2);font:0.875rem/1.429 var(--ui);margin-top:var(--s1)}
.new{color:var(--accent-text);font:600 0.8125rem/1.385 var(--ui);margin-left:var(--s2)}
.kind{font:600 0.8125rem/1.385 var(--ui);border:var(--border) solid var(--rule);
 color:var(--text-2);padding:0 var(--s1);border-radius:var(--r-sm);margin-left:var(--s2)}
/* Rule 3 -- the accent means primary action, so a magnitude is drawn in neutrals. */
.bar{display:inline-block;height:var(--s1);background:var(--text-3);border-radius:var(--r-sm);
 vertical-align:middle}
.with{font:0.875rem/1.429 var(--ui);color:var(--text-2);margin-top:var(--s1)}
.lastseen{font:0.875rem/1.429 var(--ui);color:var(--text-2);margin-top:var(--s1)}
.lastseen b{color:var(--text);font-weight:600}
.away{color:var(--caution);font-weight:600}
.strip{display:flex;gap:1px;margin-top:var(--s2);height:var(--s3);align-items:stretch}
.strip i{flex:1 1 0;border-radius:1px;background:var(--recessed)}
.strip i.on{background:var(--text-3)}
.strip i.first{background:var(--text-2);box-shadow:0 0 0 1px var(--text) inset}
.striplab{font:0.8125rem/1.385 var(--ui);color:var(--text-2);margin-top:var(--s1);
 display:flex;justify-content:space-between}
.gloss{margin-top:var(--s2);padding:var(--s2) var(--s3);border-left:2px solid var(--accent);
 background:var(--bg);font:0.875rem/1.429 var(--ui)}
.gloss b{font:600 0.8125rem/1.385 var(--ui);color:var(--text-2);display:block;
 margin-bottom:var(--s1)}
.more{color:var(--text-2);font:0.875rem/1.429 var(--ui);padding:var(--s3);text-align:center}
.empty{color:var(--text-2);font:1rem/1.5 var(--ui);padding:var(--s6) var(--s4);text-align:center}

.recap{border:var(--border) solid var(--accent);border-radius:var(--r-md);
 padding:var(--s3) var(--s4);margin:0 0 var(--s3);background:var(--surface)}
.recap h2{margin:0 0 var(--s1);font:600 1rem/1.5 var(--ui);color:var(--accent-text)}
.recap p{margin:0;font:0.875rem/1.429 var(--ui)}
.recap button{float:right;background:none;border:0;color:var(--text-2);
 font:0.875rem/1.429 var(--ui);cursor:pointer;min-height:var(--touch);padding:0 0 0 var(--s3)}

.warn{border:var(--border) solid var(--caution);border-radius:var(--r-md);
 padding:var(--s2) var(--s3);margin:0 0 var(--s3);background:var(--caution-bg)}
.warn h2{margin:0 0 var(--s1);font:600 0.875rem/1.429 var(--ui);color:var(--caution)}
.warn details{margin:var(--s1) 0 0}
.warn summary{cursor:pointer;font:1rem/1.5 var(--ui);color:var(--text);
 list-style:none;padding:var(--s2) 0;min-height:var(--touch);display:flex;align-items:center}
.warn summary::-webkit-details-marker{display:none}
.warn summary::before{content:"";display:inline-block;width:0;height:0;margin-right:var(--s2);
 border:5px solid transparent;border-left-color:var(--caution);flex:none}
.warn details[open] summary::before{border-left-color:transparent;border-top-color:var(--caution);
 margin-top:var(--s1)}
.warn .said{margin:0 0 var(--s2) var(--s5);font:0.875rem/1.429 var(--ui)}
.warn .past{color:var(--text-2);font:0.875rem/1.429 var(--ui);margin-top:var(--s2)}

.about{border:var(--border) solid var(--rule);border-radius:var(--r-md);
 background:var(--surface);margin:0 0 var(--s3);padding:0 var(--s4)}
.about summary{cursor:pointer;font:600 1rem/1.5 var(--ui);color:var(--text-2);
 padding:var(--s3) 0;list-style:none;min-height:var(--touch);display:flex;align-items:center}
.about summary::-webkit-details-marker{display:none}
.about summary::before{content:"";display:inline-block;width:0;height:0;margin-right:var(--s2);
 border:5px solid transparent;border-left-color:var(--accent);flex:none}
.about[open] summary::before{border-left-color:transparent;border-top-color:var(--accent);
 margin-top:var(--s1)}
.about dl{margin:0 0 var(--s3);font:0.875rem/1.429 var(--ui)}
.about dt{font:600 0.875rem/1.429 var(--ui);color:var(--text-2);margin:var(--s3) 0 var(--s1)}
.about dd{margin:0}
.about .ser{color:var(--accent-text);font-weight:600}
.about table{border-collapse:collapse;width:100%;margin-top:var(--s1)}
.about td{padding:var(--s1) 0;vertical-align:baseline}
.about td.n{text-align:right;padding-right:var(--s3);white-space:nowrap;
 font-variant-numeric:tabular-nums}
.about td.b{color:var(--text-2);font:0.8125rem/1.385 var(--ui)}
.about .note{color:var(--text-2);font:0.8125rem/1.385 var(--ui);margin-top:var(--s2)}

#map{width:100%;height:auto;display:block}
#map line{stroke:var(--text-3);stroke-linecap:round}
#map .lead{fill:none;stroke:var(--rule);stroke-width:1}
#map circle{fill:var(--text-2)}
#map text{font:0.8125rem var(--ui);fill:var(--text)}
.maphint{color:var(--text-2);font:0.875rem/1.429 var(--ui);margin:0 0 var(--s3)}

.dp h3{font:600 0.875rem/1.429 var(--ui);color:var(--text-2);margin:var(--s4) 0 var(--s2);
 border-bottom:var(--border) solid var(--rule);padding-bottom:var(--s1)}
.dp dl{margin:0}
.dp dt{font-weight:600;margin-top:var(--s2)}
.dp dd{margin:var(--s1) 0 0;color:var(--text-2);font:0.875rem/1.429 var(--ui)}
.dp .rel{color:var(--text)}

.pace{margin:0}
.pace svg{width:100%;height:auto;display:block}
.pace .lab{font:600 0.875rem/1.429 var(--ui);color:var(--text-2);margin:var(--s4) 0 var(--s1);
 display:flex;justify-content:space-between;align-items:baseline;gap:var(--s3)}
.pace .lab .rng{font-weight:400;white-space:nowrap;font-variant-numeric:tabular-nums}
.pace polyline{fill:none;stroke:var(--text-2);stroke-width:1.6;
 stroke-linejoin:round;stroke-linecap:round}
.pace .axis{stroke:var(--rule);stroke-width:1}

#spoilbar{background:var(--caution-bg);color:var(--caution);
 font:600 0.875rem/1.429 var(--ui);padding:var(--s2) var(--s4);text-align:center;
 border-bottom:var(--border) solid var(--caution)}
footer{border-top:var(--border) solid var(--rule);color:var(--text-2);
 font:0.8125rem/1.385 var(--ui);padding:var(--s4);max-width:760px;margin:0 auto}

@media(prefers-reduced-motion:reduce){
 *{animation-duration:0.01ms !important;animation-iteration-count:1 !important;
   transition-duration:0.01ms !important;scroll-behavior:auto !important}
}
</style>
<a class="skip" href="#list">Skip to the list</a>
<div id="spoilbar" hidden>Spoilers on — this page shows the whole book, not just where you are.</div>
<header>
  <h1>__TITLE__</h1>
  <div class="sub">__CONV__</div>
  <div class="pos">
    <input type="range" id="pos" min="1" max="__N__" value="1"
           aria-label="Which chapter you have read up to">
    <span class="chip" id="chip">ch 1</span>
  </div>
  <div class="sub" id="read"></div>
</header>
<main>
  <details class="about" id="about" hidden>
    <summary>What you are in for, over the whole book</summary>
    <div id="aboutBody"></div>
  </details>
  <div class="warn" id="warn" hidden></div>
  <div class="recap" id="recap" hidden></div>
  <p class="count" id="count"></p>
  <label class="field" for="q"><span>Find a name</span>
    <input type="search" id="q" autocomplete="off" inputmode="search"></label>
  <div class="filters" role="group" aria-label="How to view the cast">
    <button id="f-all"  aria-pressed="true">everyone</button>
    <button id="f-away" aria-pressed="false">away a while</button>
    <button id="f-people" aria-pressed="false">people</button>
    <button id="f-places" aria-pressed="false">places</button>
    <button id="f-map" aria-pressed="false">map</button>
    <button id="f-cast" aria-pressed="false">cast list</button>
    <button id="f-pace" aria-pressed="false">pace</button>
    <button id="f-newhere" aria-pressed="false" hidden>new in this book</button>
  </div>
  <div id="list" role="region" aria-label="Who you have met so far" tabindex="-1"></div>
</main>
<footer>
  Built by <b>ariadne</b> from your own copy of the book. Names, counts and
  chapter numbers only &mdash; this page holds no text from the book.
  Nothing after your position is shown.
</footer>
<script>
const D = __DATA__;
let MODE = 'all';
const pos = document.getElementById('pos');
const chip = document.getElementById('chip');
const list = document.getElementById('list');
const countEl = document.getElementById('count');

// Where the reader was when they last closed the page. Everything between
// there and here is what they have read since, and is the only thing a recap
// may talk about: it looks backward by construction.
let MARK = null;
try { const v = localStorage.getItem('ariadne:mark:' + D.title);
      if (v !== null) MARK = +v; } catch(e){}

// A warning is shown one chapter before the chapter it is about, folded shut.
// The keys of D.warn ARE the positions at which each becomes visible, so this
// performs the same `key <= position` test every other view performs and holds
// no threshold arithmetic of its own.
//
// The fold is the whole feature. Every other product in this space makes you
// accept the answer as the price of the warning; here the reader is told that
// something is coming and decides for themselves whether to look.
// A series is laid out as one long book, so every chapter number in the model
// is an index across the whole run. A reader does not think that way: they
// think "book four, chapter three", and a page telling them somebody first
// appeared in chapter 137 of Harry Potter has told them nothing.
//
// These two turn the index back into what the reader has on their shelf.
function bookAt(i){
  const bs = D.books;
  if (!bs || !bs.length) return null;
  for (let k = bs.length - 1; k >= 0; k--) if (i >= bs[k].start) return k;
  return 0;
}
function chLabel(i, withBook){
  const k = bookAt(i);
  if (k === null) return 'chapter ' + (i + 1);
  const b = D.books[k];
  return (withBook === false ? '' : 'book ' + (k+1) + ', ') + 'chapter ' + (i - b.start + 1);
}

// The one panel here that is about the whole book, and it says so on its own
// summary line. It is folded shut and opened deliberately, the same gesture a
// warning takes, because a reader who has not asked for it should not be shown
// it. What it reports is structure and never plot: how many people, how fast
// they arrive, whether the narration is first person, whether one character
// holds the book. None of that can tell you what happens.
//
// It exists because a synopsis says none of it -- measured at a median of two
// named people against the sixty a book turns out to hold.
function renderAbout(){
  const a = D.about;
  const box = document.getElementById('about');
  if (!a || !a.names) { box.hidden = true; return; }
  let h = '<dl>';
  if (a.series){
    h += '<dt>Part of a series</dt><dd><span class="ser">' + esc(a.series.name) +
         (a.series.position ? ' \u2014 book ' + esc(String(a.series.position)) : '') +
         '</span><div class="note">The file says so. Most do not, and most ' +
         'descriptions do not either.</div></dd>';
  }
  h += '<dt>How many people you will be holding</dt><dd>' +
       '<b>' + a.names + ' names</b> in the whole book, over ' +
       a.words.toLocaleString() + ' words \u2014 about ' + a.hours + ' hours reading';
  if (a.curve){
    h += '<table>';
    const rows = [['0.1','a tenth in'],['0.25','a quarter in'],
                  ['0.5','halfway'],['0.75','three quarters in']];
    for (const [q,label] of rows){
      const pct = a.curve[q], band = (a.band||{})[q];
      const people = Math.round(a.names * pct / 100);
      let note = '';
      if (band){
        const where = pct < band[0] ? 'fewer than most' :
                      pct > band[1] ? 'more than most' : 'about usual';
        note = where + ', corpus middle half ' + band[0].toFixed(0) + '\u2013' +
               band[1].toFixed(0) + '%';
      }
      h += '<tr><td class="n"><b>' + people + '</b></td><td>by ' + label +
           '</td><td class="b">' + note + '</td></tr>';
    }
    h += '</table>';
  }
  h += '</dd>';
  if (a.volumes && a.volumes.length > 1){
    h += '<dt>How the cast grows across the series</dt><dd><table>';
    for (let i = 0; i < a.volumes.length; i++){
      const v = a.volumes[i];
      h += '<tr><td class="n"><b>+' + v.new + '</b></td><td>' + esc(v.title) +
           '</td><td class="b">' + (v.carried ? v.carried + ' already known' : 'the start') +
           '</td></tr>';
    }
    h += '</table><div class="note">Every name new to a volume is somebody to learn ' +
         'while still holding everyone from before it.</div></dd>';
  }
  if (a.person){
    const word = {first:'the first person', mixed:'a mix of first and third',
                  third:'the third person'}[a.person.kind];
    h += '<dt>Told in ' + word + '</dt><dd>' +
         Math.round(a.person.share*100) + '% of the pronouns outside dialogue are ' +
         'I or me.' + (a.person.kind !== 'third'
      ? '<div class="note">So the narrator is rarely named, and any count of who ' +
        'appears most understates them. Nothing here tries to name a lead.</div>' : '') +
         '</dd>';
  }
  if (a.focus && a.focus.refused){
    h += '<dt>Does one person hold it \u2014 not reported</dt><dd>' +
         'This book says <i>he</i> or <i>she</i> about ' + Math.round(a.focus.ratio) +
         ' times for every time it names its most-named person, so whoever a ' +
         'chapter belongs to is mostly a pronoun.' +
         '<div class="note">Counting names would measure who is talked about ' +
         'instead. Above about 15 that answer is wrong more often than right.</div></dd>';
  } else if (a.focus){
    h += '<dt>Does one person hold it</dt><dd>' + esc(a.focus.lead) +
         ' is named most in <b>' + Math.round(a.focus.share*100) + '%</b> of chapters; ' +
         a.focus.owners + ' different people lead one.' +
         '<div class="note">A book with a single protagonist reaches 50\u201360%; ' +
         'one that hands you round a cast sits nearer 12%. Read the ' +
         'share as a floor: two names for one person you have not linked yet split ' +
         'their chapters and make the book look wider than it is.</div></dd>';
  }
  h += '</dl><div class="note">Cast size, pace and narration are structure, not ' +
       'story. Everything else on this page stops at the chapter you are on.</div>';
  document.getElementById('aboutBody').innerHTML = h;
  box.hidden = false;
}

function renderWarn(upto){
  const box = document.getElementById('warn');
  const rows = [];
  for (const k in (D.warn || {})) if (+k <= upto) for (const w of D.warn[k]) rows.push(w);
  if (!rows.length){ box.hidden = true; return; }
  rows.sort((a,b) => a.at - b.at);
  const soon = rows.filter(w => w.at > upto);
  const past = rows.filter(w => w.at <= upto);
  let h = '<h2>Something you left yourself</h2>';
  for (const w of soon){
    h += '<details><summary>Chapter ' + (w.at+1) +
         ' \u2014 there is something here. Show what you wrote?</summary>' +
         '<div class="said">' + esc(w.text) + '</div></details>';
  }
  if (past.length){
    h += '<div class="past">' + past.length +
         (past.length===1 ? ' warning you have already passed' : ' warnings you have already passed') +
         '</div>';
    for (const w of past){
      h += '<details><summary>Chapter ' + (w.at+1) + ' \u2014 already read</summary>' +
           '<div class="said">' + esc(w.text) + '</div></details>';
    }
  }
  box.innerHTML = h;
  box.hidden = false;
}

function recap(upto){
  const box = document.getElementById('recap');
  if (MARK === null || upto <= MARK) { box.hidden = true; return; }
  const fresh = D.entities.filter(e => e.first > MARK && e.first <= upto);
  const back = D.entities.filter(e => {
    if (e.first > MARK) return false;
    const before = e.chapters.filter(c => c <= MARK);
    const after  = e.chapters.filter(c => c > MARK && c <= upto);
    if (!before.length || !after.length) return false;
    return after[0] - before[before.length-1] >= 5;   // a real absence, not a pause
  });
  if (!fresh.length && !back.length) { box.hidden = true; return; }
  const bits = [];
  if (fresh.length) bits.push('<b>' + fresh.length + ' new</b> — ' +
    fresh.slice(0,5).map(e=>esc(e.name)).join(', ') + (fresh.length>5?'…':''));
  if (back.length) bits.push('<b>' + back.length + ' back after a while</b> — ' +
    back.slice(0,5).map(e=>esc(e.name)).join(', ') + (back.length>5?'…':''));
  box.innerHTML = '<button id="recap-x">dismiss</button>' +
    '<h2>Since ' + chLabel(MARK) + ', where you left off</h2><p>' +
    bits.join('<br>') + '</p>';
  box.hidden = false;
  document.getElementById('recap-x').addEventListener('click', () => {
    MARK = upto; box.hidden = true;
    try { localStorage.setItem('ariadne:mark:' + D.title, String(upto)); } catch(e){}
  });
}

// Who shares chapters with whom, drawn as a ring. Positions are alphabetical
// rather than force-directed on purpose: a layout that moves when the reader
// advances makes it impossible to see that anything changed.
function renderMap(upto){
  const assoc = (D.assoc[upto] || []).slice(0, 40);
  if (!assoc.length){
    list.innerHTML = '<div class="empty">Not enough shared chapters yet.</div>';
    return;
  }
  const names = [...new Set(assoc.flatMap(([a,b]) => [a,b]))].sort();
  const N = names.length, R = 150, CX = 320, CY = 245, VW = 640, VH = 490;
  const at = {};
  names.forEach((n,i) => {
    const t = (i / N) * 2 * Math.PI - Math.PI/2;
    at[n] = [CX + R*Math.cos(t), CY + R*Math.sin(t), t];
  });

  // Labels are placed apart, not where their node happens to sit.
  //
  // y = CY + R*sin(t), so dy/dt goes to zero at the top and bottom of the
  // ring: adjacent nodes there are at almost the same height while their
  // labels run horizontally, straight through each other. Three names in
  // Crime and Punishment rendered as one unreadable word.
  //
  // Nudging alone could not fix it. Measured across the ten pages, six carry
  // up to 23 labels a side needing 299px of line height in a ring only 236px
  // tall, so the canvas grew as well. Each side is now spread over the full
  // height, and a label that had to move gets a leader line back to its node.
  const GAP = 15, PAD = 10;
  const place = (side) => {
    const rows = names.filter(n => (Math.cos(at[n][2]) >= 0) === side)
                      .map(n => ({n, y: at[n][1]}))
                      .sort((a,b) => a.y - b.y);
    for (let i = 1; i < rows.length; i++)
      rows[i].y = Math.max(rows[i].y, rows[i-1].y + GAP);
    const over = rows.length ? rows[rows.length-1].y - (VH - PAD) : 0;
    if (over > 0) for (const r of rows) r.y -= over;
    for (let i = rows.length - 2; i >= 0; i--)
      rows[i].y = Math.min(rows[i].y, rows[i+1].y - GAP);
    if (rows.length && rows[0].y < PAD){
      const under = PAD - rows[0].y;
      for (const r of rows) r.y += under;
    }
    const out = {};
    for (const r of rows) out[r.n] = r.y;
    return out;
  };
  const labelY = Object.assign(place(true), place(false));

  const maxJ = Math.max(...assoc.map(e => e[2]));
  let svg = '<svg id="map" viewBox="0 0 ' + VW + ' ' + VH +
            '" role="img" aria-label="who appears with whom">';
  for (const [a,b,j] of assoc){
    const [x1,y1] = at[a], [x2,y2] = at[b];
    svg += '<line x1="'+x1.toFixed(1)+'" y1="'+y1.toFixed(1)+'" x2="'+x2.toFixed(1)+
           '" y2="'+y2.toFixed(1)+'" stroke-width="'+(0.4 + 2.6*j/maxJ).toFixed(2)+
           '" opacity="'+(0.15 + 0.5*j/maxJ).toFixed(2)+'"/>';
  }
  for (const n of names){
    const [x,y,t] = at[n];
    const right = Math.cos(t) >= 0;
    const ly = labelY[n];
    const lx = right ? Math.max(x + 10, CX + R + 14) : Math.min(x - 10, CX - R - 14);
    svg += '<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="3"/>';
    // A leader only where the label had to leave its node, so a tidy ring
    // stays clean and a crowded one stays readable.
    if (Math.abs(ly - y) > 3 || Math.abs(lx - x) > 22)
      svg += '<polyline class="lead" points="'+x.toFixed(1)+','+y.toFixed(1)+' '+
             (right ? (lx-6).toFixed(1) : (lx+6).toFixed(1))+','+ly.toFixed(1)+' '+
             lx.toFixed(1)+','+ly.toFixed(1)+'"/>';
    svg += '<text x="'+lx.toFixed(1)+'" y="'+(ly+4).toFixed(1)+
           '" text-anchor="'+(right?'start':'end')+'">'+esc(n)+'</text>';
  }
  svg += '</svg>';
  list.innerHTML = '<p class="maphint">Who shares chapters with whom, up to chapter ' +
    (upto+1) + '. A thicker line means more chapters together. Nothing past your ' +
    'position is drawn.</p>' + svg;
}

// A cast list rather than a ranked table: the thing readers ask for by name
// is a dramatis personae showing how things stand where they are, not a
// filtered view of the ending. Same data, and the framing is the point.
function renderCast(upto, seen){
  const rel = D.relations || {};
  const groups = [['person','People'], ['place','Places'], ['unknown','Everything else']];
  const assoc = D.assoc[upto] || [];
  const partners = {};
  for (const [a,b,j] of assoc){
    (partners[a] = partners[a] || []).push([b,j]);
    (partners[b] = partners[b] || []).push([a,j]);
  }
  let html = '<div class="dp"><p class="maphint">How things stand at chapter ' +
    (upto+1) + '. Nothing here is drawn from a later chapter.</p>';
  for (const [kind,label] of groups){
    const rows = seen.filter(e => (e.kind||'unknown') === kind)
      .map(e => {
        const upTo = e.chapters.filter(c => c <= upto);
        const uses = e.counts.filter((_,i) => e.chapters[i] <= upto).reduce((a,b)=>a+b,0);
        return {e, uses, appear: upTo.length};
    // Classified entities first, then by how much of them the reader has had.
  //
  // The opening screen is the worst one on the page and it is the one everybody
  // sees. At chapter one nothing has accumulated, so ranking on mentions alone
  // sorts a protagonist and a stray capitalised word by counts of one and two --
  // measured across the ten pages, 39% of the top ten at chapter one is
  // unclassified against 7% at the midpoint, and one book's first screen was
  // entirely noise.
  //
  // This leaks nothing. The kind is already printed on every card, and an
  // entity has to be visible before it can be ordered.
  }).sort((x,y) => {
    const ux = (x.e.kind || 'unknown') === 'unknown';
    const uy = (y.e.kind || 'unknown') === 'unknown';
    if (ux !== uy) return ux ? 1 : -1;
    return y.uses - x.uses;
  });
    if (!rows.length) continue;
    html += '<h3>' + label + ' \\u00b7 ' + rows.length + '</h3><dl>';
    for (const {e,uses,appear} of rows){
      const p = (partners[e.name]||[]).sort((a,b)=>b[1]-a[1]).slice(0,3).map(x=>x[0]);
      const r = (rel[e.name]||[]).filter(x => x.at <= upto);
      const g = (D.glosses||{})[e.name];
      html += '<dt>' + esc(e.name) + '</dt><dd>' +
        'first met in ' + chLabel(e.first) + ' \\u00b7 ' + appear +
        (appear===1?' chapter':' chapters') + ' \\u00b7 ' + uses + ' mentions';
      if (r.length) html += '<br><span class="rel">' +
        r.map(x => esc(x.text) + ' <i>(' + chLabel(x.at) + ')</i>').join('<br>') + '</span>';
      if (p.length) html += '<br>often with ' + p.map(esc).join(', ');
      if (g && g.at <= upto) html += '<br>you wrote: ' + esc(g.text);
      html += '</dd>';
    }
    html += '</dl>';
  }
  list.innerHTML = html + '</div>';
}

// Three counts per chapter, drawn, with no verdict attached to any of them.
// Only chapters the reader has reached are plotted -- the line stops where
// they are, so its shape cannot hint at what the rest of the book does.
//
// Each chart carries its own scale, printed. A shared axis would flatten two
// of the three into nothing, and an unlabelled axis invites the reader to
// compare heights that were never comparable.
function renderPace(upto){
  const rows = (D.pace || []).slice(0, upto + 1);
  if (rows.length < 3){
    list.innerHTML = '<div class="empty">Not enough chapters yet to draw a line.</div>';
    return;
  }
  const series = [
    ['How much of the chapter is dialogue', rows.map(r => r.d), v => v.toFixed(0) + '%'],
    ['People on stage', rows.map(r => r.o), v => String(Math.round(v))],
    ['Met for the first time here', rows.map(r => r.f), v => String(Math.round(v))],
    ['Words in the chapter', rows.map(r => r.w), v => Math.round(v).toLocaleString()],
  ];
  const W = 600, H = 104, PAD = 8;
  let h = '<div class="pace"><p class="maphint">Chapters 1 to ' + (upto+1) +
    '. Nothing past where you are is drawn. These are counts, not a score \u2014 ' +
    'a quiet chapter is a choice somebody made, and no number here can tell you ' +
    'whether it worked.</p>';
  for (const [label, vals, fmt] of series){
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const span = (hi - lo) || 1;
    const pts = vals.map((v,i) => {
      const x = PAD + (vals.length === 1 ? 0 : i * (W - 2*PAD) / (vals.length - 1));
      const y = H - PAD - ((v - lo) / span) * (H - 2*PAD);
      return x.toFixed(1) + ',' + y.toFixed(1);
    }).join(' ');
    // The scale goes in the heading rather than inside the chart. Printed at
    // the top left it sits exactly where a peak lands, and a reader should
    // never have to work out which of two overlapping things they are seeing.
    h += '<div class="lab">' + label +
      '<span class="rng">' + esc(fmt(lo)) + ' to ' + esc(fmt(hi)) + '</span></div>' +
      '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(label) +
      ', ' + esc(fmt(lo)) + ' to ' + esc(fmt(hi)) + ' across ' + vals.length + ' chapters">' +
      '<line class="axis" x1="0" y1="' + (H-PAD) + '" x2="' + W + '" y2="' + (H-PAD) + '"/>' +
      '<polyline points="' + pts + '"/>' +
      '</svg>';
  }
  list.innerHTML = h + '</div>';
}

// How long someone has been gone, judged against how often they normally
// appear rather than against a fixed number of chapters.
//
// A constant does not survive the range of books this runs on. Five chapters
// of War and Peace is about 7,500 words and five of Crime and Punishment is
// about 25,500, and at a flat five chapters the War and Peace page flagged
// 528 of its 533 names -- a filter that fires on 99% of its input is not a
// filter, and a reader learns to ignore the tab rather than the entry.
//
// The presence conditions are a different axis, not a second guess at the
// same one: they ask whether this was somebody you had got to know, because
// a name that appeared twice in chapter three has not been forgotten, it is
// finished.
//
// The 20,000-word floor is the second axis again rather than a third guess:
// unusual-for-them alone flagged Pierre after five chapters, which is correct
// arithmetic and useless advice -- nobody forgets the protagonist over 12,000
// words. Twenty thousand is roughly eighty minutes of reading, which is a gap
// somebody actually returns from having lost the thread. At that floor the
// same page surfaces Dolokhov, Boris and Anatole instead.
//
// What this cannot claim is that it predicts forgetting. It measures an
// absence unusual FOR THAT PERSON that is also long in reading time, which is
// the closest arithmetic gets. No reader has tested it.
const CUM = (function(){
  const c = [0];
  for (const r of (D.pace || [])) c.push(c[c.length-1] + r.w);
  return c;
})();
const LOST_WORDS = 20000;

function lostTrack(seen, uses, upto){
  if (seen.length < 4 || uses < 10) return false;
  const gaps = [];
  for (let i = 1; i < seen.length; i++) gaps.push(seen[i] - seen[i-1]);
  gaps.sort((a,b) => a-b);
  const med = gaps[Math.floor(gaps.length/2)] || 0;
  if (!med) return false;
  const last = seen[seen.length-1];
  if ((upto - last) < 3*med) return false;
  // No word counts means no floor to apply, and the relative test stands on
  // its own rather than the whole view silently going empty.
  if (CUM.length < 2) return (upto - last) >= Math.max(3, 3*med);
  return (CUM[upto+1] - CUM[last+1]) >= LOST_WORDS;
}

// Who else was in the room the last time you saw them. The aggregate "often
// with" answers a different question; when you have lost somebody, the useful
// hook is the particular chapter you last met them in.
function alongside(name, ch, limit){
  const out = [];
  for (const e of D.entities){
    if (e.name === name || e.first > ch) continue;
    if (e.chapters.indexOf(ch) >= 0) out.push(e);
    if (out.length > 40) break;
  }
  return out.sort((a,b) => b.total - a.total).slice(0, limit).map(e => e.name);
}

const WPM = 250;
function readingTime(upto){
  const rows = (D.pace || []).slice(0, upto + 1);
  if (!rows.length) return '';
  const words = rows.reduce((a,r) => a + r.w, 0);
  const mins = Math.round(words / WPM);
  const t = mins < 90 ? mins + ' minutes'
          : (mins/60).toFixed(mins < 600 ? 1 : 0) + ' hours';
  return words.toLocaleString() + ' words read \u00b7 about ' + t + ' at ' + WPM + ' wpm';
}

function render(){
  // With spoilers on the position stops bounding the views. The bar at the top
  // is not decoration: a page that quietly behaved differently would be worse
  // than one that spoils, because the reader could not tell which they had.
  const n = +pos.value, upto = D.spoil ? (D.chapters - 1) : (n - 1);
  const bk = bookAt(n - 1);
  chip.textContent = (bk === null) ? ('ch ' + n)
    : ('bk ' + (bk+1) + ' \u00b7 ch ' + (n - D.books[bk].start));
  document.getElementById('read').textContent = readingTime(upto);
  // The spoiler rule: an entity is visible only if its first chapter is at or
  // before where the reader is. Nothing else is consulted.
  const seen = D.entities.filter(e => e.first <= upto);
  const fresh = seen.filter(e => e.first === upto).length;
  let tail = fresh + ' new in this chapter';
  if (D.books && D.books.length > 1){
    const b = D.books[bookAt(upto)];
    const carried = seen.filter(e => e.first < b.start).length;
    tail = carried + ' carried in from earlier books \\u00b7 ' + tail;
  }
  countEl.textContent = seen.length + ' of ' + D.entities.length + ' met \\u00b7 ' + tail;
  recap(upto);
  renderWarn(upto);
  if (MODE === 'pace'){
    countEl.textContent = (upto+1) + ' of ' + D.chapters + ' chapters';
    renderPace(upto);
    return;
  }
  if (MODE === 'cast'){
    countEl.textContent = seen.length + ' of ' + D.entities.length + ' met';
    renderCast(upto, seen);
    return;
  }
  if (MODE === 'map'){
    countEl.textContent = seen.length + ' of ' + D.entities.length + ' met';
    renderMap(upto);
    return;
  }
  const assoc = D.assoc[upto] || [];
  const partners = {};
  for (const [a,b,j] of assoc){
    (partners[a] = partners[a] || []).push([b,j]);
    (partners[b] = partners[b] || []).push([a,j]);
  }
  let scored = seen.map(e => {
    const upTo = e.chapters.filter(c => c <= upto);
    const uses = e.counts.filter((_,i) => e.chapters[i] <= upto)
                         .reduce((a,b)=>a+b,0);
    // How long since the reader last met them. This is the whole reason a
    // reader forgets somebody: they left in chapter 9 and came back in 41.
    const last = upTo.length ? upTo[upTo.length-1] : -1;
    return {e, uses, appear: upTo.length, last: last,
            away: last < 0 ? 0 : upto - last,
            lost: last < 0 ? false : lostTrack(upTo, uses, upto)};
  }).sort((x,y) => y.uses - x.uses);
  // Accents are stripped from both sides. Most of the corpus is translated,
  // so a reader who types "natasha" is looking for "Natasha" spelled with an
  // acute, and a search that answers "no name here matches that" is worse
  // than no search at all.
  const q = fold(document.getElementById('q').value || '');
  if (q) scored = scored.filter(s => fold(s.e.name).indexOf(q) >= 0);
  // Ranked by how much of the book they have had, not by how long they have
  // been gone: a 200-chapter absence usually means somebody who left early and
  // never returned, while the person actually worth reminding you about is the
  // one you have read a great deal of and not seen lately. Sorting by gap
  // length surfaces the first and buries the second.
  if (MODE === 'away')   scored = scored.filter(s => s.lost);
  // Somebody a series reader has met before this volume is a different kind of
  // problem from somebody introduced in it: the first needs reminding, the
  // second needs learning. Nothing else here can tell them apart.
  if (MODE === 'newhere' && D.books){
    const k = bookAt(upto), b = D.books[k];
    const end = b.start + b.chapters - 1;
    scored = scored.filter(s => s.e.first >= b.start && s.e.first <= end);
  }
  // A reminder list of two hundred people is not a reminder. The everyone tab
  // still holds all of them; what is capped is the number shown at once, and
  // the count of the rest is stated rather than dropped silently.
  const CAP = 25;
  const hidden = (MODE === 'away' && scored.length > CAP) ? scored.length - CAP : 0;
  if (hidden) scored = scored.slice(0, CAP);
  if (MODE === 'people') scored = scored.filter(s => s.e.kind === 'person');
  if (MODE === 'places') scored = scored.filter(s => s.e.kind === 'place');
  const max = scored.length ? scored[0].uses : 1;
  list.innerHTML = scored.length ? scored.map(({e,uses,appear,away,last,lost}) => {
    const w = Math.max(3, Math.round(90 * uses / max));
    const p = (partners[e.name]||[]).slice(0,3).map(x=>x[0]);
    const kind = (e.kind && e.kind !== 'unknown')
      ? '<span class="kind">' + e.kind + '</span>' : '';
    // What the reader wrote, and when. Shown only once they have reached the
    // chapter they wrote it at -- a note made at chapter 30 is a spoiler to
    // the same reader at chapter 10 on a re-read.
    const g = (D.glosses || {})[e.name];
    const gloss = (g && g.at <= upto)
      ? '<div class="gloss"><b>you wrote, at chapter ' + (g.at+1) + '</b>' +
        esc(g.text) + '</div>' : '';
    const wordsAway = (CUM.length > 1 && last >= 0)
      ? (CUM[upto+1] - CUM[last+1]) : 0;
    const gone = lost
      ? '<div class="meta"><span class="away">not seen for ' + away +
        ' chapters</span> \\u00b7 ' + Math.round(wordsAway/1000) +
        'k words, longer than usual for them</div>' +
        '<div class="lastseen">last met in <b>' + chLabel(last) + '</b>' +
        (alongside(e.name, last, 4).length
          ? ', alongside ' + alongside(e.name, last, 4).map(esc).join(', ') : '') +
        '</div>' : '';
    // One cell per chapter the reader has reached. Nothing past the position
    // is drawn at all -- the strip ends where the reader is, so it cannot
    // hint at whether somebody returns later.
    const inCh = new Set(e.chapters.filter(c => c <= upto));
    // Rule 13 -- presence is drawn in colour, so the same fact is stated in
    // words for anyone the colour does not reach.
    let strip = '<div class="strip" role="img" aria-label="In ' + appear +
      ' of the ' + (upto+1) + ' chapters you have read">';
    for (let c = 0; c <= upto; c++) {
      const cls = (c === e.first) ? 'first' : (inCh.has(c) ? 'on' : '');
      strip += '<i class="' + cls + '"></i>';
    }
    strip += '</div><div class="striplab"><span>' + chLabel(0) + '</span><span>' +
             chLabel(upto) + '</span></div>';
    return '<div class="card"><div><span class="name">' + esc(e.name) + '</span>' +
      (e.first === upto ? '<span class="new">NEW</span>' : '') + kind + '</div>' +
      '<div class="meta">first met in ' + chLabel(e.first) +
      ' \\u00b7 ' + appear + (appear===1?' chapter':' chapters') +
      ' \\u00b7 ' + uses + ' mentions <span class="bar" style="width:' + w + 'px"></span></div>' +
      gone + gloss +
      (p.length ? '<div class="with">often with ' + p.map(esc).join(', ') + '</div>' : '') +
      strip +
      '</div>';
  }).join('') + (hidden ? '<div class="more">and ' + hidden +
      ' more you have not seen lately \\u2014 these are the ones you have read most of' +
      '</div>' : '')
    : '<div class="empty">' + (q ? 'No name here matches that.'
        : MODE === 'away' ? 'Nobody you have lost track of yet.'
        : MODE === 'newhere' ? 'Nobody new so far in this book.'
        : 'Nobody here.') + '</div>';
}
function fold(s){
  return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
}
function esc(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
for (const m of ['all','away','people','places','map','cast','pace','newhere']) {
  document.getElementById('f-'+m).addEventListener('click', () => {
    MODE = m;
    for (const o of ['all','away','people','places','map','cast','pace','newhere'])
      document.getElementById('f-'+o).setAttribute('aria-pressed', String(o===m));
    render();
  });
}
if (D.books && D.books.length > 1) document.getElementById('f-newhere').hidden = false;
renderAbout();
if (D.spoil) document.getElementById('spoilbar').hidden = false;
pos.addEventListener('input', render);
document.getElementById('q').addEventListener('input', render);
try{ const k='ariadne:'+D.title; const v=localStorage.getItem(k);
     if(v){ pos.value=v; }
     pos.addEventListener('change',()=>{
       localStorage.setItem(k, pos.value);
       // The mark only ever moves forward, and only once the reader has been
       // shown what happened since it.
       if (MARK === null) { MARK = +pos.value - 1;
         localStorage.setItem('ariadne:mark:'+D.title, String(MARK)); }
     }); }catch(e){}
render();
</script>
"""


def render_page(m):
    return (
        PAGE.replace("__TITLE__", html.escape(m["title"]))
        .replace(
            "__CONV__",
            html.escape(
                "%d chapters · %s · %s quotes" % (m["chapters"], m["convention"], m["quotes"])
            ),
        )
        .replace("__N__", str(m["chapters"]))
        .replace("__DATA__", json.dumps(m, ensure_ascii=False))
    )
