// Pages simples (version recruteur) : compteur de visites et téléchargements de CV.
import { event, initStats } from './stats';

initStats();
document.addEventListener('click', (e) => {
  const a = (e.target as HTMLElement).closest<HTMLAnchorElement>('a[download]');
  if (a) event(`cv/${a.pathname.split('/').pop()}`);
});
