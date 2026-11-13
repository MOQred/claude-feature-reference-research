# YouTube: кадры и расшифровки во встроенном браузере

Всё делается во встроенном браузере (`mcp__Claude_Browser__*`). Скачивать видео нельзя (yt-dlp нет и ставить его не надо). `localhost`-сервер из браузера недоступен, timedtext-API без токена отдаёт пустой ответ. Ниже то, что работает.

## Подводные камни

- **Реклама.** Перед роликом и посреди него идут ролики, они в том же `<video>`. На плеере в это время класс `#movie_player.ad-showing`. Ждать окончания, жать skip; первый тест-кадр однажды поймал рекламу EVE Online. Проверяй каждый кадр глазами.
- **Таймаут инструмента — 45 с.** Длинную съёмку запускай без `await` (функция на `window`, вернуть `'started'`), потом опрашивай `window.__grabDone` отдельными вызовами по ≤40 с.
- **Скачивание.** `<a download>` кладёт файл в `%USERPROFILE%\Downloads`. Иногда файл остаётся `*.tmp` (внутри уже JPEG) — `scripts/take.ps1` подхватывает и `.tmp`, и готовые имена; если готовые имена есть, сортировка по имени, иначе по времени.
- **Субтитры на кадре.** Если в плеере включены субтитры, они впечатаются в кадр — перед съёмкой `p.unloadModule('captions')`.
- **Пустые страницы.** Поиск YouTube и описание ролика иногда не дорисовываются (серые заглушки). Не трать на это время: ищи видео через веб-поиск агентов, транскрипт бери через перехват (ниже), а не через кнопку «Показать расшифровку».
- **Гайды со слайдами.** В видео-гайдах половина кадров — слайды автора. Сначала смотри раскадровку.
- Браузер может быть скрыт, страница всё равно работает. Скриншот `computer`→`screenshot` сохраняется в tool-results и годится для проверки, но для итоговых кадров используй canvas.

## 1. Раскадровка: найти моменты с интерфейсом

На странице ролика:

```js
const pr = document.querySelector('#movie_player').getPlayerResponse();
const spec = pr.storyboards.playerStoryboardSpecRenderer.spec.split('|');
const base = spec[0]; const levels = spec.slice(1).map((s, i) => { const [w,h,count,cols,rows,interval,name,sigh] = s.split('#'); return {i, w:+w, h:+h, count:+count, cols:+cols, rows:+rows, interval:+interval, name, sigh}; });
const L = levels[levels.length - 1]; const pages = Math.ceil(L.count / (L.cols * L.rows));
({tpl: base.replace('$L', L.i).replace('$N', L.name).replace('$M', '{m}') + '&sigh=' + L.sigh, pages, cols: L.cols, rows: L.rows, w: L.w, h: L.h, interval: L.interval, len: pr.videoDetails.lengthSeconds})
```

Потом: `python scripts/sb.py <имя> "<tpl>" <pages> <cols> <rows> <w> <h> <interval> [start end]` → `<имя>_sb.jpg` в текущей папке (запускай из `yt\`), смотри через Read и выбирай секунды. Сам лист раскадровки потом удали.

## 2. Кадры + расшифровка одним заходом

Вставь на странице ролика (функция переживает только до навигации, после `navigate` определи заново), задав префикс и секунды:

```js
window.__grab = async (PREFIX, TIMES) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms)); const p = document.querySelector('#movie_player'); const v = document.querySelector('video');
  const noAd = async () => { for (let i = 0; i < 150 && p.classList.contains('ad-showing'); i++) { document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern, button[id^="skip-button"]')?.click(); await sleep(1000); } };
  p.unloadModule?.('captions'); v.muted = true; p.setPlaybackQualityRange?.('hd1080', 'hd1080'); await v.play().catch(() => {}); await noAd(); await sleep(1500);
  window.__grabDone = [];
  for (const t of TIMES) { v.currentTime = t; await new Promise(r => { v.onseeked = r; setTimeout(r, 8000); }); await sleep(1800); await noAd(); if (Math.abs(v.currentTime - t) > 4) { v.currentTime = t; await sleep(2500); } v.pause(); p.unloadModule?.('captions');
    const c = document.createElement('canvas'); const w = Math.min(1280, v.videoWidth); c.width = w; c.height = Math.round(w * v.videoHeight / v.videoWidth);
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    const a = document.createElement('a'); a.href = c.toDataURL('image/jpeg', 0.88); a.download = `${PREFIX}_${t}.jpg`; document.body.appendChild(a); a.click(); a.remove();
    window.__grabDone.push(`${t}:${v.videoWidth}x${v.videoHeight}`); await sleep(1500); await v.play().catch(() => {}); }
  v.pause(); window.__grabDone.push('END');
  // расшифровка: перехватываем запрос субтитров, который делает сам плеер (с его токеном)
  window.__tt = null;
  if (!window.__ttPatched) { const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function () { if (String(this.__u).includes('timedtext')) this.addEventListener('load', () => { window.__tt = this.responseText; }); return os.apply(this, arguments); };
    const of = window.fetch; window.fetch = async function (u) { const r = await of.apply(this, arguments); try { if (String(u && u.url || u).includes('timedtext')) r.clone().text().then(t => window.__tt = t); } catch (e) {} return r; }; window.__ttPatched = true; }
  p.loadModule?.('captions'); await sleep(500); p.setOption?.('captions', 'track', {languageCode: 'en'});
  for (let i = 0; i < 15 && !window.__tt; i++) await sleep(700);
  p.unloadModule?.('captions');
  let last = -99; window.__ttText = '';
  if (window.__tt) { const j = JSON.parse(window.__tt); window.__ttText = j.events.filter(e => e.segs).map(e => { const s = Math.floor(e.tStartMs / 1000); const tx = e.segs.map(x => x.utf8).join('').replace(/\n/g, ' ').trim(); if (!tx) return ''; if (s - last >= 45) { last = s; return `\n[${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}] ` + tx; } return tx; }).filter(Boolean).join(' '); }
  window.__grabDone.push('TT ' + window.__ttText.length);
};
window.__grab('game_yt', [40, 95, 180]); 'started'
```

Опрос (повторять, пока нет строки `TT …`):

```js
const sleep = ms => new Promise(r => setTimeout(r, ms));
for (let i = 0; i < 40 && !(window.__grabDone || []).some(x => String(x).startsWith('TT')); i++) await sleep(1000);
({done: window.__grabDone, text: (window.__ttText || '').slice(0, 9000)})
```

Если у ролика нет английских субтитров, поменяй `languageCode` (у русских роликов — `ru`); `getPlayerResponse().captions...captionTracks` покажет доступные. Расшифровка приходит с метками времени раз в ~45 с — этого хватает для ссылок.

Затем: `powershell -File scripts/take.ps1 -Prefix game_yt -Times 40,95,180 -Dest <папка>\yt` (из PowerShell вызывай как `& scripts\take.ps1 ...`, чтобы массив чисел разобрался правильно).

## 3. Запасной путь без браузера

Автокадры YouTube в HD (примерно 25/50/75% ролика): `https://i.ytimg.com/vi/<id>/maxres1.jpg`, `maxres2.jpg`, `maxres3.jpg`, плюс обложка `maxresdefault.jpg`. Это картинки, их можно брать curl'ом. Момент не выбрать, но для «как выглядит режим» часто достаточно.
