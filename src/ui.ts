import { PLACES, TIMES } from './config';
import { sections } from './content';
import { lang, onLang, setLang, t, tx } from './i18n';
import type { Settings, Theme } from './settings';
import { LEVEL_NAMES, type Level, type QualityChoice } from './quality';

interface Handlers {
  time: (id: string) => void;
  theme: (theme: Theme) => void;
  place: (id: string) => void;
  quality: (q: QualityChoice) => void;
  lights: (v: number) => void;
  overview: () => void;
}

/** Barre du haut (rubriques), barre du bas (moment, vue d'ensemble, thème), calques du ciel. */
export function mountHud(
  settings: Settings,
  on: Handlers,
): { setCurrent: (placeId: string | null) => void; setQuality: (choice: QualityChoice, level: Level) => void } {
  // Ciel : un calque par moment, fondu enchaîné
  const skies = document.querySelector<HTMLElement>('#skies')!;
  const skyLayers = TIMES.map((t) => {
    const d = document.createElement('div');
    d.style.background = `linear-gradient(${t.sky[0]}, ${t.sky[1]})`;
    skies.append(d);
    return { d, id: t.id };
  });
  const syncSky = (): void => skyLayers.forEach(({ d, id }) => d.classList.toggle('on', id === settings.time));
  syncSky();

  // Moment de la journée
  const timeBox = document.querySelector<HTMLElement>('#time')!;
  const timeButtons = TIMES.map((t) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'swatch';
    b.style.setProperty('--swatch', t.swatch);
    b.setAttribute('aria-label', tx(t.name));
    b.title = tx(t.name);
    b.addEventListener('click', () => {
      on.time(t.id);
      syncTime();
      syncSky();
    });
    timeBox.append(b);
    return { b, id: t.id };
  });
  const syncTime = (): void => timeButtons.forEach(({ b, id }) => b.setAttribute('aria-pressed', String(id === settings.time)));
  const relabelTime = (): void => timeButtons.forEach(({ b, id }) => {
    const n = tx(TIMES.find((x) => x.id === id)!.name);
    b.setAttribute('aria-label', n);
    b.title = n;
  });
  syncTime();

  // Rubriques (raccourcis vers les lieux)
  const quick = document.querySelector<HTMLElement>('#quick')!;
  const quickButtons = sections().map((s) => {
    const place = PLACES.find((p) => p.section === s.id);
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = s.kicker;
    if (place) b.addEventListener('click', () => on.place(place.id));
    else b.disabled = true;
    quick.append(b);
    return { b, placeId: place?.id, id: s.id };
  });
  const relabelQuick = (): void => {
    const list = sections();
    quickButtons.forEach(({ b, id }) => (b.textContent = list.find((s) => s.id === id)?.kicker ?? ''));
  };

  document.querySelector('#overview')!.addEventListener('click', on.overview);

  // Thème clair / sombre (couleurs des panneaux)
  const themeBtn = document.querySelector<HTMLButtonElement>('#theme')!;
  const syncTheme = (): void => {
    const dark = settings.theme === 'dark';
    themeBtn.setAttribute('aria-pressed', String(dark));
    themeBtn.setAttribute('aria-label', dark ? t('Panneaux clairs', 'Light panels') : t('Panneaux sombres', 'Dark panels'));
    themeBtn.title = themeBtn.getAttribute('aria-label')!;
  };
  themeBtn.addEventListener('click', () => {
    on.theme(settings.theme === 'dark' ? 'light' : 'dark');
    syncTheme();
  });
  syncTheme();

  // Lumières de la ville : bouton lampe → curseur
  const lightsBtn = document.querySelector<HTMLButtonElement>('#lights-btn')!;
  const lightsPop = document.querySelector<HTMLElement>('#lights-pop')!;
  const lightsRange = document.querySelector<HTMLInputElement>('#lights-range')!;
  const lightsVal = document.querySelector<HTMLElement>('#lights-val')!;
  const lightsNote = document.querySelector<HTMLElement>('#lights-note')!;
  const syncLights = (): void => {
    const pct = Math.round(settings.lights * 100);
    lightsRange.value = String(pct);
    lightsVal.textContent = `${pct} %`;
    lightsRange.style.setProperty('--fill', `${pct}%`);
    lightsNote.hidden = settings.time !== 'jour';
  };
  const openLights = (open: boolean): void => {
    lightsPop.hidden = !open;
    lightsBtn.setAttribute('aria-expanded', String(open));
    if (open) syncLights();
  };
  lightsBtn.addEventListener('click', (e) => { e.stopPropagation(); openLights(lightsPop.hidden !== false); });
  lightsRange.addEventListener('input', () => {
    on.lights(Number(lightsRange.value) / 100);
    syncLights();
  });
  document.querySelector('#lights-night')!.addEventListener('click', () => {
    on.time('nuit');
    syncTime();
    syncSky();
    syncLights();
  });
  addEventListener('pointerdown', (e) => {
    if (!lightsPop.hidden && !lightsPop.contains(e.target as Node) && e.target !== lightsBtn && !lightsBtn.contains(e.target as Node)) openLights(false);
  });
  addEventListener('keydown', (e) => e.key === 'Escape' && openLights(false));

  // Qualité du rendu : Auto → Haute → Moyenne → Basse
  const ORDER: QualityChoice[] = ['auto', 'high', 'mid', 'low'];
  const qBtn = document.querySelector<HTMLButtonElement>('#quality-btn')!;
  qBtn.addEventListener('click', () => on.quality(ORDER[(ORDER.indexOf(settings.quality) + 1) % ORDER.length]));
  let qState: [QualityChoice, Level] = [settings.quality, 'high'];
  const syncQuality = (): void => {
    const [choice, level] = qState;
    const name = tx(LEVEL_NAMES[level]).toLowerCase();
    const label = choice === 'auto' ? `${t('Qualité', 'Quality')} : auto (${name})` : `${t('Qualité', 'Quality')} : ${name}`;
    qBtn.title = label;
    qBtn.setAttribute('aria-label', label);
    qBtn.dataset.level = level;
    qBtn.dataset.auto = String(choice === 'auto');
  };

  // Langue : bouton FR/EN (affiche la langue vers laquelle on bascule)
  const langBtn = document.querySelector<HTMLButtonElement>('#lang-btn')!;
  const syncLang = (): void => {
    langBtn.textContent = lang === 'fr' ? 'EN' : 'FR';
    const label = lang === 'fr' ? 'English version' : 'Version française';
    langBtn.title = label;
    langBtn.setAttribute('aria-label', label);
    langBtn.lang = lang === 'fr' ? 'en' : 'fr';
  };
  langBtn.addEventListener('click', () => setLang(lang === 'fr' ? 'en' : 'fr'));
  syncLang();
  onLang(() => {
    relabelTime();
    relabelQuick();
    syncTheme();
    syncQuality();
    syncLang();
  });

  return {
    setQuality: (choice, level) => {
      qState = [choice, level];
      syncQuality();
    },
    setCurrent: (placeId) =>
      quickButtons.forEach(({ b, placeId: id }) => b.setAttribute('aria-current', String(!!placeId && id === placeId))),
  };
}
