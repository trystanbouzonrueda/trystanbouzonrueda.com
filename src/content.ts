// Contenu des rubriques. Une rubrique = un panneau ouvert depuis un lieu de l'île.
// HTML simple, mis en forme par les classes .cards, .ligne, .badges, .chiffres… de style.css.
import {
  siAnthropic, siApachehadoop, siApachehive, siArgo, siBlender, siC, siCaddy, siCloudflare, siCplusplus, siDebian, siDocker,
  siGit, siGithub, siGnubash, siInstagram, siTiktok, siK3s, siKeycloak, siKubernetes, siLinux, siMariadb, siOllama, siOpnsense, siOpenstreetmap,
  siPfsense, siPhp, siProxmox, siPython, siTailscale, siTalend, siThreedotjs, siTruenas, siTypescript, siUbuntu, siVmware,
  siWireguard,
} from 'simple-icons';
import { lang, type Lang, type Txt } from './i18n';

export interface Section {
  id: string;
  title: string;
  kicker: string; // petite ligne au-dessus du titre
  html: string;
}

const MAIL = 'trystan.bouzon08@gmail.com';
const GITHUB = 'https://github.com/trystanbouzonrueda';
const LINKEDIN = 'https://www.linkedin.com/in/trystan-bouzon-rueda';
const REPO = `${GITHUB}/trystanbouzonrueda.com`;
const BASE = import.meta.env.BASE_URL;

const LIEN = (href: string, txt: string): string => `<a href="${href}" target="_blank" rel="noopener">${txt}</a>`;

/** Logo simple-icons en SVG inline (couleur de la marque). */
const logo = (i: { path: string; hex: string }): string =>
  `<svg viewBox="0 0 24 24" aria-hidden="true" style="fill:#${i.hex}"><path d="${i.path}"/></svg>`;
const badge = (txt: string, i?: { path: string; hex: string }): string => `<span class="badge">${i ? logo(i) : ''}${txt}</span>`;
const tags = (...t: string[]): string => `<div class="tags">${t.map((x) => `<span>${x}</span>`).join('')}</div>`;

/** Pictogrammes au trait (24×24) pour les cartes sans capture. */
const PICTO = {
  data: '<path d="M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3Z"/><path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
  shield: '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
  server: '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01M11 7.5h6M11 16.5h6"/>',
  k8s: '<path d="M12 2.5 20.5 7v10L12 21.5 3.5 17V7L12 2.5Z"/><circle cx="12" cy="12" r="3"/><path d="M12 5v4M12 15v4M5.5 8.5 9 10.5M15 13.5l3.5 2M5.5 15.5 9 13.5M15 10.5l3.5-2"/>',
  net: '<rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-4h12v4"/>',
  web: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01M8 14l-2 2 2 2M16 14l2 2-2 2M13 13l-2 6"/>',
};
const picto = (k: keyof typeof PICTO): string =>
  `<div class="card-picto"><svg viewBox="0 0 24 24" aria-hidden="true">${PICTO[k]}</svg></div>`;


/** Schéma d'architecture : chaîne de 4 blocs reliés par des flèches (titre + sous-titre). */
const flow = (nodes: [string, string][]): string => {
  const W = 360, G = 16, w = (W - G * (nodes.length - 1)) / nodes.length;
  const box = nodes.map(([t, s], i) => {
    const x = i * (w + G);
    const arrow = i < nodes.length - 1 ? `<path class="fl" d="M${x + w + 3} 32h${G - 7}m-4-4 4 4-4 4"/>` : '';
    return `<rect x="${x + 0.75}" y="8.75" width="${w - 1.5}" height="46.5" rx="9"/><text x="${x + w / 2}" y="29" class="t">${t}</text><text x="${x + w / 2}" y="44" class="s">${s}</text>${arrow}`;
  });
  return `<svg class="card-schema" viewBox="0 0 ${W} 64" role="img" aria-label="${nodes.map((n) => n[0]).join(' → ')}">${box.join('')}</svg>`;
};

interface Projet {
  titre: Txt;
  texte: Txt;
  schema?: (l: Lang) => string;
  tags: string[];
  lien?: { href: string; txt: Txt };
  note?: Txt; // remplace « code privé » sous la carte
}

const PRIVE: Txt = { fr: 'Code privé · présentation sur demande', en: 'Private code · walkthrough on request' };

const PROJETS: Projet[] = [
  {
    titre: { fr: 'Entrepôt de données hospitalier', en: 'Hospital data warehouse' },
    texte: {
      fr: 'En équipe de 3 au CESI : un entrepôt décisionnel pour un groupe hospitalier, des sources brutes au tableau de bord. Architecture en couches bronze, silver, gold, modèle en étoile, données pseudonymisées (RGPD).',
      en: 'Team of 3 at CESI: a decision-support warehouse for a hospital group, from raw sources to dashboards. Bronze, silver and gold layers, star schema, pseudonymised data (GDPR).',
    },
    schema: (l) => flow([
      ['4 sources', 'SQL · CSV · FTP'],
      ['Talend', 'ETL'],
      ['HDFS · Hive', 'bronze → gold'],
      ['Power BI', l === 'fr' ? 'tableaux de bord' : 'dashboards'],
    ]),
    tags: ['Hadoop · HDFS', 'Hive', 'Talend', 'PostgreSQL', 'Docker', 'Power BI'],
  },
  {
    titre: { fr: 'JANUS et tRHy, applis métier de la mairie', en: 'JANUS and tRHy, city hall business apps' },
    texte: {
      fr: 'Deux applications pour la collectivité où je suis en alternance. JANUS gère les événements municipaux de bout en bout (rôles, validations, temps réel) ; tRHy remplace une vieille appli RH en VB.NET et corrige ses failles. Droits vérifiés côté serveur, chaque règle métier tracée jusque dans les tests.',
      en: 'Two apps for the city council where I work as an apprentice. JANUS runs municipal events end to end (roles, approvals, real time); tRHy replaces an old VB.NET HR tool and fixes its security flaws. Permissions checked server-side, every business rule traced down to the tests.',
    },
    schema: (l) => flow([
      ['React', l === 'fr' ? 'navigateur' : 'browser'],
      ['API Express', 'RBAC · zod'],
      ['PostgreSQL', 'Drizzle ORM'],
      ['Socket.io', l === 'fr' ? 'temps réel' : 'real time'],
    ]),
    tags: ['TypeScript', 'React', 'Express', 'PostgreSQL', 'Socket.io', 'Docker'],
  },
  {
    titre: { fr: 'Homelab', en: 'Homelab' },
    texte: {
      fr: 'Chez moi : pare-feu OPNsense et VLAN, hyperviseur Proxmox sur un serveur rack, Proxmox Backup Server, TrueNAS et Nextcloud. Accessible de partout sans port ouvert, en partie piloté par des agents IA.',
      en: 'At home: OPNsense firewall and VLANs, Proxmox hypervisor on a rack server, Proxmox Backup Server, TrueNAS and Nextcloud. Reachable from anywhere with no open port, partly operated by AI agents.',
    },
    schema: (l) => flow([
      ['Tailscale', l === 'fr' ? 'zéro port ouvert' : 'no open port'],
      ['OPNsense', l === 'fr' ? 'pare-feu · VLAN' : 'firewall · VLAN'],
      ['Proxmox VE', 'VM · LXC'],
      ['TrueNAS · PBS', l === 'fr' ? 'sauv. 3-2-1' : '3-2-1 backup'],
    ]),
    tags: ['Proxmox VE', 'OPNsense', 'TrueNAS', 'Tailscale', 'Claude Code · MCP'],
  },
  {
    titre: { fr: 'EasySave, logiciel de sauvegarde', en: 'EasySave, backup software' },
    texte: {
      fr: 'En équipe de 4 au CESI : sauvegardes complètes et différentielles, chiffrement, travaux en parallèle. J’y ai fait le serveur de logs centralisé (ASP.NET Core dans Docker), la traduction FR/EN et des tests unitaires.',
      en: 'Team of 4 at CESI: full and differential backups, encryption, parallel jobs. I built the centralised log server (ASP.NET Core in Docker), the FR/EN translation and unit tests.',
    },
    schema: (l) => flow([
      ['WPF · MVVM', l === 'fr' ? 'interface' : 'desktop UI'],
      [l === 'fr' ? 'Moteur' : 'Engine', l === 'fr' ? 'complète · diff.' : 'full · diff.'],
      ['CryptoSoft', l === 'fr' ? 'chiffrement' : 'encryption'],
      ['LogServer', 'Docker'],
    ]),
    tags: ['C# · .NET 10', 'WPF', 'ASP.NET Core', 'Docker', 'xUnit'],
    lien: { href: 'https://github.com/Tuture57/Projet-EasySave', txt: { fr: 'Code source sur GitHub', en: 'Source code on GitHub' } },
  },
  {
    titre: { fr: 'Breezy, réseau social léger', en: 'Breezy, lightweight social network' },
    texte: {
      fr: 'Projet de groupe au CESI auquel j’ai participé sur toutes les briques : un réseau social façon X pensé pour les petites connexions. Sept microservices, authentification JWT, médias, déployé sur Kubernetes et supervisé par Prometheus et Grafana.',
      en: 'Group project at CESI where I took part in every layer: an X-style social network built for low-bandwidth use. Seven microservices, JWT auth, media, deployed on Kubernetes and monitored with Prometheus and Grafana.',
    },
    schema: (l) => flow([
      ['Next.js', 'mobile-first'],
      ['Ingress nginx', 'Kubernetes'],
      ['7 services', 'Node · Express'],
      [l === 'fr' ? 'Bases' : 'Databases', 'Mongo · Postgres'],
    ]),
    tags: ['Kubernetes', 'Docker', 'Node.js', 'Next.js', 'MongoDB', 'Prometheus'],
  },
  {
    titre: { fr: 'Activité freelance (projet perso)', en: 'Freelance work (side project)' },
    texte: {
      fr: 'En préparation, à côté de l’alternance : réseau et sécurité, homelab et auto-hébergement, sites web sur mesure, pour les particuliers et les petites structures.',
      en: 'In preparation, alongside my apprenticeship: network and security, homelab and self-hosting, custom websites, for individuals and small organisations.',
    },
    tags: ['Réseau · sécurité', 'Auto-hébergement', 'Sites web'],
    note: { fr: 'Sur devis · passe par la rubrique Contact', en: 'On quote · see the Contact section' },
  },
];

const projetsHtml = (l: Lang): string =>
  PROJETS.map((p) => `<article class="card card-wide"><div>
    <h3>${p.titre[l]}</h3>
    ${p.schema?.(l) ?? ''}
    <p>${p.texte[l]}</p>
    ${tags(...p.tags)}
    <p class="card-links${p.lien ? '' : ' prive'}">${p.lien ? LIEN(p.lien.href, p.lien.txt[l]) : (p.note ?? PRIVE)[l]}</p></div>
  </article>`).join('\n');

/** Frise façon ligne de métro : stations = étapes. */
const ligne = (color: string, stops: { date: string; titre: string; lieu: string; now?: boolean }[]): string =>
  `<ol class="ligne" style="--ligne:${color}">${stops
    .map((s) => `<li${s.now ? ' class="now"' : ''}><span class="date">${s.date}</span><b>${s.titre}</b><span class="lieu">${s.lieu}</span></li>`)
    .join('')}</ol>`;

// années d'alternance, calculées à l'affichage (depuis 09/2025)
const ALTERNANCE = Math.max(1, Math.floor((Date.now() - new Date(2025, 8, 1).getTime()) / (365.25 * 864e5)));

/** Rubriques dans la langue demandée (langue courante par défaut). */
export const sections = (l: Lang = lang): Section[] => {
  const x = (fr: string, en: string): string => (l === 'fr' ? fr : en);
  const ans = l === 'fr' ? `${ALTERNANCE} an${ALTERNANCE > 1 ? 's' : ''}` : `${ALTERNANCE} year${ALTERNANCE > 1 ? 's' : ''}`;
  const recruteur = `${BASE}recruteur/${l === 'en' ? '?lang=en' : ''}`;
  return [
  {
    id: 'apropos',
    kicker: x('À propos', 'About'),
    title: 'Trystan Bouzon Rueda',
    html: x(
      `<p><strong>Élève ingénieur informatique en 4ᵉ année au CESI</strong>, en alternance comme administrateur systèmes et réseaux à la DSI d'une collectivité.</p>`,
      `<p><strong>Fourth-year computer engineering student at CESI</strong>, working as a systems and network administrator apprentice in a city council IT department.</p>`,
    ) + `
<div class="chiffres">
  <div><b>${ans}</b><span>${x("d'alternance en production", 'of work-study in production')}</span></div>
  <div><b>4</b><span>${x('machines au homelab', 'machines in my homelab')}</span></div>
  <div><b>5</b><span>${x('projets menés', 'projects delivered')}</span></div>
  <div><b>${x('33 000', '33,000')}</b><span>${x('bâtiments dans cette ville', 'buildings in this city')}</span></div>
</div>
` + x(
      `<p>J'administre, je sécurise et je documente une infrastructure en production, de l'annuaire à Kubernetes. Chez moi, je fais tourner un homelab… et ce site, servi depuis un petit serveur à la maison.</p>
<p>Je cherche un <strong>stage de 12 semaines à l'étranger</strong> en <strong>systèmes, réseaux et/ou IA</strong>.</p>`,
      `<p>I run, secure and document production infrastructure, from directory services to Kubernetes. At home I run a homelab… and this website, served from a small server in my flat.</p>
<p>I'm looking for a <strong>12-week internship abroad</strong> in <strong>systems, networking and/or AI</strong>.</p>`,
    ) + `
<p><a class="btn" href="${recruteur}">${x('Version recruteur et CV', 'Recruiter version and resume')}</a></p>`,
  },
  {
    id: 'projets',
    kicker: x('Projets', 'Projects'),
    title: x('Ce que je construis', 'What I build'),
    html: `<div class="cards">
  <article class="card card-star">
    <img src="${BASE}img/projets/portfolio.webp" alt="${x("Vue d'ouverture du portfolio en 3D", 'Opening view of the 3D portfolio')}" width="640" height="389" loading="lazy" />
    <div><span class="ribbon">${x('Premier projet open source', 'First open-source project')}</span>
    <h3>trystanbouzonrueda.com</h3>
    <p>${x(
      "Ma ville reconstruite depuis OpenStreetMap, rendue en 3D dans le navigateur, optimisée jusqu'à diviser les appels de rendu par deux. Auto-hébergée derrière un tunnel Cloudflare, sans port ouvert.",
      'My home city rebuilt from OpenStreetMap, rendered in 3D in the browser and optimised down to half the draw calls. Self-hosted behind a Cloudflare Tunnel, with no open port.',
    )}</p>
    ${tags('Three.js', 'TypeScript', 'Blender · Python', 'OpenStreetMap', 'Caddy')}
    <p class="card-links">${LIEN(REPO, x('Code source sur GitHub', 'Source code on GitHub'))}</p></div>
  </article>
  ${projetsHtml(l)}
</div>`,
  },
  {
    id: 'parcours',
    kicker: x('Parcours', 'Experience'),
    title: x('Expérience', 'Experience'),
    html: `${ligne('#e2001a', [
      { date: '2023', titre: x('Bac STI2D', 'French baccalaureate (STI2D)'), lieu: x('Lycée, Marseille', 'High school, Marseille') },
      { date: '2023 – 2025', titre: x('Prépa ingénieur', 'Engineering preparatory cycle'), lieu: 'CESI' },
      { date: '09/2025', titre: x('Alternance admin systèmes et réseaux', 'Systems & network admin apprentice'), lieu: x('DSI d’une mairie, Plan-de-Cuques', 'City council IT department, Plan-de-Cuques'), now: true },
      { date: x('Prochain arrêt', 'Next stop'), titre: x('Stage de 12 semaines à l’étranger', '12-week internship abroad'), lieu: x('Systèmes, réseaux et/ou IA', 'Systems, networking and/or AI') },
    ])}
<p>${x('Le détail de mon alternance est à l’église de Plan-de-Cuques (rubrique Entreprise).', 'Details of my apprenticeship are at the Plan-de-Cuques church (Company section).')}</p>
<p><a class="btn" href="${BASE}cv/${l === 'fr' ? 'cv-trystan-bouzon-rueda.pdf' : 'Trystan-Bouzon-Rueda-CV-Mobility-EN.pdf'}" download>${x('Télécharger mon CV (PDF)', 'Download my resume (PDF)')}</a></p>`,
  },
  {
    id: 'formation',
    kicker: x('Formation', 'Education'),
    title: x('CESI École d’Ingénieurs', 'CESI School of Engineering'),
    html: `${ligne('#0b5cd5', [
      { date: '06/2023', titre: x('Baccalauréat STI2D', 'French baccalaureate (STI2D)'), lieu: x('Mention assez bien · lycée Antonin Artaud', 'With honours · Antonin Artaud high school') },
      { date: '2023 – 2025', titre: x('Cycle préparatoire, mineure informatique', 'Preparatory cycle, computer science minor'), lieu: 'CESI' },
      { date: '2025 – 2028', titre: x('Diplôme d’ingénieur informatique (alternance)', 'Master’s-level engineering degree in computer science (work-study)'), lieu: 'CESI Aix-en-Provence', now: true },
    ])}
<p>${x(
      'Démarche scientifique (ADS), stockage et Big Data, systèmes et réseaux. Langues : français, anglais.',
      'Research methodology, storage and Big Data, systems and networking. Languages: French, English.',
    )}</p>`,
  },
  {
    id: 'competences',
    kicker: x('Compétences', 'Skills'),
    title: x('Ma boîte à outils', 'My toolbox'),
    html: `<h3>${x('Systèmes et réseaux', 'Systems and networking')}</h3><div class="badges">${badge('Proxmox VE', siProxmox)}${badge('Linux', siLinux)}${badge('Debian', siDebian)}${badge('Ubuntu', siUbuntu)}${badge('VMware', siVmware)}${badge('Windows Server')}${badge('Active Directory · GPO')}${badge('DNS · DHCP')}${badge('VLAN · DMZ · VPN')}</div>
<h3>${x('Cybersécurité', 'Cybersecurity')}</h3><div class="badges">${badge('pfSense', siPfsense)}${badge('OPNsense', siOpnsense)}${badge('Keycloak', siKeycloak)}${badge('WireGuard', siWireguard)}${badge('Tailscale', siTailscale)}${badge('Zabbix')}${badge(x('PRA · sauvegarde 3-2-1', 'DRP · 3-2-1 backup'))}</div>
<h3>${x('DevOps et cloud', 'DevOps and cloud')}</h3><div class="badges">${badge('Docker', siDocker)}${badge('Kubernetes', siKubernetes)}${badge('k3s', siK3s)}${badge('Argo CD', siArgo)}${badge('Git', siGit)}${badge('GitHub', siGithub)}${badge('TrueNAS', siTruenas)}${badge('Caddy', siCaddy)}${badge('Cloudflare', siCloudflare)}</div>
<h3>${x('IA appliquée', 'Applied AI')}</h3><div class="badges">${badge('Claude Code · MCP', siAnthropic)}${badge('Ollama', siOllama)}${badge(x('Agents IA', 'AI agents'))}</div>
<h3>${x('Données', 'Data')}</h3><div class="badges">${badge('Hadoop', siApachehadoop)}${badge('Hive', siApachehive)}${badge('Talend', siTalend)}${badge('MariaDB', siMariadb)}${badge('Power BI')}</div>
<h3>${x('Langages et 3D', 'Languages and 3D')}</h3><div class="badges">${badge('Python', siPython)}${badge('TypeScript', siTypescript)}${badge('Bash', siGnubash)}${badge('PowerShell')}${badge('PHP', siPhp)}${badge('C', siC)}${badge('C++', siCplusplus)}${badge('Three.js', siThreedotjs)}${badge('Blender', siBlender)}${badge('OpenStreetMap', siOpenstreetmap)}</div>`,
  },
  {
    id: 'contact',
    kicker: 'Contact',
    title: x('On se parle ?', 'Let’s talk'),
    html: `<p>${x('Un stage, un projet ou juste une question : écris-moi, je réponds vite.', 'An internship, a project or just a question: drop me a line, I reply fast.')}</p>
<div class="actions">
  <a class="action primary" href="mailto:${MAIL}?subject=${encodeURIComponent(x('Prise de contact depuis trystanbouzonrueda.com', 'Hello from trystanbouzonrueda.com'))}">
    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6.5 8.5 7 8.5-7"/></svg>${x("M'écrire", 'Email me')}</a>
  <button type="button" class="action" data-copy="${MAIL}">
    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/></svg>${x("Copier l'adresse", 'Copy address')}</button>
  <a class="action" href="${LINKEDIN}" target="_blank" rel="noopener">
    <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10v7M8 7v.01M12 17v-4a2 2 0 0 1 4 0v4M12 10v7"/></svg>LinkedIn</a>
</div>
<p class="petit">${MAIL}</p>`,
  },
  {
    id: 'entreprise',
    kicker: x('Entreprise', 'Company'),
    title: x('Mairie de Plan-de-Cuques', 'Plan-de-Cuques town hall'),
    html: x(
      `<p>Depuis septembre 2025, je suis <strong>administrateur systèmes et réseaux en alternance</strong> à la DSI de la mairie de Plan-de-Cuques, la commune voisine de Marseille.</p>`,
      `<p>Since September 2025 I have been a <strong>systems and network administrator apprentice</strong> in the IT department of Plan-de-Cuques town hall, right next to Marseille.</p>`,
    ) + `
<div class="cards offres">
  <article class="card">${picto('server')}<div><h3>${x('Infrastructure', 'Infrastructure')}</h3><p>${x('Administration des serveurs et du réseau : annuaire, services réseau, virtualisation.', 'Server and network administration: directory services, network services, virtualisation.')}</p></div></article>
  <article class="card">${picto('k8s')}<div><h3>${x('Applications internes', 'Internal apps')}</h3><p>${x('Plateforme d’applications métier conteneurisée, authentification unique, déploiement automatisé ; les applis JANUS et tRHy.', 'Containerised business-app platform, single sign-on, automated deployment; the JANUS and tRHy apps.')}</p></div></article>
  <article class="card">${picto('shield')}<div><h3>${x('Au quotidien', 'Day to day')}</h3><p>${x('Tickets jusqu’à la mise en production, documentation technique, mise en service de nouveaux outils internes.', 'Tickets all the way to production, technical documentation, rollout of new internal tools.')}</p></div></article>
</div>`,
  },
  {
    id: 'reseaux',
    kicker: x('Réseaux', 'Socials'),
    title: x('Me suivre', 'Follow me'),
    html: `<p>${x('Touche un logo au-dessus du Dôme, ou choisis ici :', 'Tap a logo above the Dôme, or pick one here:')}</p>
<div class="actions reseaux">
  <a class="action" href="${LINKEDIN}" target="_blank" rel="noopener"><svg class="logo-res" viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="4" fill="#0a66c2"/><path d="M7 10v7M7 7v.01M11 17v-4a2.5 2.5 0 0 1 5 0v4M11 10v7" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg><span><b>LinkedIn</b><small>${x('Parcours et expériences', 'Background and experience')}</small></span></a>
  <a class="action" href="${GITHUB}" target="_blank" rel="noopener">${logo(siGithub).replace('<svg', '<svg class="logo-res"')}<span><b>GitHub</b><small>${x('Le code de ce site', 'The code of this site')}</small></span></a>
  <a class="action" href="https://www.instagram.com/trystanbr/" target="_blank" rel="noopener">${logo(siInstagram).replace('<svg', '<svg class="logo-res"')}<span><b>Instagram</b><small>@trystanbr</small></span></a>
  <a class="action" href="https://www.tiktok.com/@trystanbz" target="_blank" rel="noopener">${logo(siTiktok).replace('<svg', '<svg class="logo-res"')}<span><b>TikTok</b><small>@trystanbz</small></span></a>
</div>`,
  },
  ];
};

/** Une rubrique par son id, dans la langue courante. */
export const sectionById = (id: string | undefined): Section | undefined => (id ? sections().find((s) => s.id === id) : undefined);
