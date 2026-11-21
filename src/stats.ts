// Statistiques de visite : GoatCounter auto-hébergé (open source, sans cookie, pas de bandeau à afficher).
// Le script et le point de comptage sont servis par le site lui-même (/count.js et /count, relayés par Caddy
// vers le conteneur GoatCounter du serveur) : aucune requête vers un tiers.
// Actif seulement en production sur le vrai domaine, et jamais si le visiteur a demandé « ne pas me suivre ».

const DOMAIN = 'trystanbouzonrueda.com';
/** même clé que le bouton de la page des mentions légales */
const OPT_OUT = 'portfolio.nostats';

interface GC {
  count: (o: { path: string; title?: string; event?: boolean }) => void;
}
const gc = (): GC | undefined => (window as unknown as { goatcounter?: GC }).goatcounter;

const enabled = ((): boolean => {
  if (!import.meta.env.PROD) return false;
  const h = location.hostname;
  if (h !== DOMAIN && h !== `www.${DOMAIN}`) return false;
  const dnt = navigator.doNotTrack === '1' || (navigator as unknown as { globalPrivacyControl?: boolean }).globalPrivacyControl === true;
  // opposition donnée sur la page des mentions légales (droit d'opposition, RGPD art. 21)
  let optedOut = false;
  try {
    optedOut = localStorage.getItem(OPT_OUT) === '1';
  } catch {
    /* stockage bloqué : rien n'est mémorisé, on suit seulement DNT/GPC */
  }
  return !dnt && !optedOut;
})();

const pending: string[] = [];

/** Charge le compteur (une vue de page est comptée à son chargement). */
export function initStats(): void {
  if (!enabled) return;
  const s = document.createElement('script');
  s.async = true;
  s.src = '/count.js';
  s.dataset.goatcounter = `${location.origin}/count`;
  s.addEventListener('load', () => pending.splice(0).forEach(event));
  document.head.append(s);
}

/** Événement nommé (ouverture de rubrique, CV téléchargé, terminal trouvé…). */
export function event(name: string): void {
  if (!enabled) return;
  const g = gc();
  if (!g) {
    if (pending.length < 20) pending.push(name);
    return;
  }
  g.count({ path: name, title: name, event: true });
}
