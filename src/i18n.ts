// Langue du site : français ou anglais.
// Choix : ?lang= dans l'adresse > choix enregistré > langue du navigateur (fr… → français, sinon anglais).
// Les textes fixes de index.html portent leur version anglaise en attribut : data-en (texte), data-en-title,
// data-en-aria-label, data-en-alt… ; la version française d'origine est gardée en data-fr* à la première bascule.

export type Lang = 'fr' | 'en';
export type Txt = { fr: string; en: string };

const KEY = 'lang'; // même clé que /recruteur/ : le choix suit d'une page à l'autre
const ATTRS = ['title', 'aria-label', 'alt', 'href'];

function detect(): Lang {
  const q = new URLSearchParams(location.search).get('lang');
  if (q === 'fr' || q === 'en') return q;
  try {
    const s = localStorage.getItem(KEY);
    if (s === 'fr' || s === 'en') return s;
  } catch {
    /* stockage bloqué : on suit le navigateur */
  }
  return (navigator.languages?.[0] ?? navigator.language ?? 'fr').toLowerCase().startsWith('fr') ? 'fr' : 'en';
}

export let lang: Lang = detect();

/** Texte dans la langue courante. */
export const t = (fr: string, en: string): string => (lang === 'fr' ? fr : en);
export const tx = (x: Txt): string => x[lang];

const subs: (() => void)[] = [];
/** Appelé à chaque changement de langue (textes construits par le code). */
export const onLang = (cb: () => void): void => {
  subs.push(cb);
};

/** Textes fixes de la page (attributs data-en*). */
function applyStatic(): void {
  document.documentElement.lang = lang;
  for (const el of document.querySelectorAll<HTMLElement>('[data-en]')) {
    el.dataset.fr ??= el.innerHTML;
    el.innerHTML = lang === 'fr' ? el.dataset.fr : el.dataset.en!;
  }
  for (const a of ATTRS) {
    const en = `data-en-${a}`, fr = `data-fr-${a}`;
    for (const el of document.querySelectorAll<HTMLElement>(`[${en}]`)) {
      if (!el.hasAttribute(fr)) el.setAttribute(fr, el.getAttribute(a) ?? '');
      el.setAttribute(a, el.getAttribute(lang === 'fr' ? fr : en)!);
    }
  }
}

export function setLang(l: Lang): void {
  if (l === lang) return;
  lang = l;
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* pas grave : le choix ne survivra pas au rechargement */
  }
  // l'adresse garde ?lang= seulement si elle l'avait déjà (lien partagé)
  const u = new URL(location.href);
  if (u.searchParams.has('lang')) {
    u.searchParams.set('lang', l);
    history.replaceState(null, '', u);
  }
  applyStatic();
  subs.forEach((cb) => cb());
}

applyStatic();
