# Prompts Meshy : île Marseille

## Marche à suivre (Meshy 7.1, nov. 2026)
L'onglet Modèle part d'une image :
1. « Générer une image » (ou Image dans la barre de gauche) : prompt ci-dessous + suffixe
   `, single object centered, three-quarter isometric view, plain white background, full object visible`
2. Envoyer l'image dans Modèle : onglet **Topologie intelligente**, **Texture activée**, Pose désactivée, Résolution Standard.
3. Télécharger en GLB dans ce dossier.

Anciens réglages (Text to 3D) :
- Topology **Triangle**, Target polycount **Low / 10k max** (le David 15k max).
- **PBR désactivé**, texture simple. Style : choisir le plus « cartoon / stylized » proposé.
- Symétrie **Auto** (On pour le Vélodrome et le Mucem).
- Générer 4 variantes, garder celle à la silhouette la plus lisible de loin.
- Export **GLB**, nom de fichier ci-dessous, déposé dans ce dossier.

Negative prompt (toujours le même) :
```
realistic, photorealistic, noisy texture, high detail, tiny details, text, logo, people, ground plane, base plate, terrain, background
```

## Priorité 1 : monuments phares

**notre_dame.glb**
```
Notre-Dame de la Garde basilica in Marseille, miniature low poly stylized building for a tycoon city builder game, Romanesque-Byzantine church with a tall square bell tower topped by a huge golden Virgin and Child statue, alternating white and green striped stone bands, small domes, sitting on a rocky fortress terrace, clean chunky shapes, flat vibrant colors, soft hand-painted look, isometric game asset
```

**velodrome.glb**
```
Orange Velodrome football stadium in Marseille, miniature low poly stylized stadium for a tycoon city builder game, oval bowl with a continuous white undulating wavy roof floating above the stands, sky blue and white seats, bright green pitch with white lines, clean chunky shapes, flat vibrant colors, isometric game asset
```

**david.glb**
```
Statue of David replica from Marseille Prado beach, miniature low poly stylized statue for a tycoon city builder game, standing nude male marble figure in contrapposto pose on a tall square white stone pedestal, smooth white marble, simple readable silhouette, flat colors, isometric game asset
```

## Priorité 2 : décor

**mucem.glb**
```
MuCEM museum in Marseille, miniature low poly stylized building for a tycoon city builder game, perfect square glass cube wrapped in a dark grey concrete lace lattice mesh facade, flat roof terrace, thin footbridge leaving from the roof, clean geometric shapes, flat colors, isometric game asset
```

**fort_saint_jean.glb**
```
Fort Saint-Jean in Marseille, miniature low poly stylized medieval fortress for a tycoon city builder game, beige limestone walls and ramparts, one tall square tower and one round tower, crenellations, clean chunky shapes, flat warm colors, isometric game asset
```

**major.glb**
```
Marseille Cathedral La Major, miniature low poly stylized cathedral for a tycoon city builder game, Byzantine-Roman revival church with several domes and two front towers, horizontal stripes of cream white stone and green-grey stone, clean chunky shapes, flat colors, isometric game asset
```

**chateau_if.glb**
```
Chateau d'If fortress in Marseille, miniature low poly stylized castle for a tycoon city builder game, square beige limestone fortress with three round towers and thick walls, tiny rocky white islet around it, clean chunky shapes, flat warm colors, isometric game asset
```

**dome.glb**
```
Le Dome concert hall in Marseille, miniature low poly stylized building for a tycoon city builder game, large flattened white dome shaped arena like a spaceship, glass entrance band at the base, clean smooth shapes, flat colors, isometric game asset
```

**chateau_borely.glb**
```
Chateau Borely in Marseille, miniature low poly stylized 18th century mansion for a tycoon city builder game, symmetrical cream stone neoclassical facade, grey slate roof, tall windows, small front staircase, clean chunky shapes, flat colors, isometric game asset
```

**navette_frioul.glb**
```
Small blue passenger ferry boat from Marseille to Frioul islands, miniature low poly stylized boat for a tycoon city builder game, bright blue hull, white upper deck cabin with windows, open top deck with railings, clean chunky shapes, flat vibrant colors, isometric game asset
```

**pointu.glb**
```
Traditional Marseille pointu fishing boat, miniature low poly stylized small wooden boat for a tycoon city builder game, pointed bow, colorful hull painted red white and blue stripes, small mast, clean chunky shapes, flat vibrant colors, isometric game asset
```

## Fait à la main (pas besoin de Meshy)
Vieux-Port (quais, ombrière), Corniche et pont de la Fausse-Monnaie, city stade de Jul, parc Borély (allées, bassin), immeubles, arbres, palmiers, voitures, nuages, mouettes, Calanques.

## Lot 2 : refaits par image (le texte → 3D sortait trop réaliste et cassait à la simplification)

**gare_saint_charles.glb**
```
Gare Saint-Charles train station in Marseille, miniature low poly stylized building for a tycoon city builder game, long beige stone station hall with big arched glass roof, grand monumental staircase with statues descending in front, clean chunky shapes, flat warm colors, isometric game asset
```

**pharo.glb**
```
Palais du Pharo in Marseille, miniature low poly stylized palace for a tycoon city builder game, Second Empire mansion with cream stone walls and steep grey slate roofs, small garden terrace, clean chunky shapes, flat colors, isometric game asset
```

**bastide.glb**
```
Provencal bastide country house, miniature low poly stylized building for a tycoon city builder game, ochre walls, pale green shutters, terracotta tile roof, two cypress trees, clean chunky shapes, flat warm colors, isometric game asset
```

**petanque.glb**
```
Petanque court, miniature low poly stylized prop for a tycoon city builder game, rectangular sandy gravel court with wooden border, a few silver boules, a green bench and one plane tree, clean chunky shapes, flat colors, isometric game asset
```

**maison_trois_fenetres.glb**
```
Typical Marseille three-window town house, miniature low poly stylized building for a tycoon city builder game, narrow three storey cream facade, blue wooden shutters, small iron balcony, terracotta tile roof, clean chunky shapes, flat colors, isometric game asset
```

**immeuble_canebiere.glb**
```
Haussmann style apartment building of the Canebiere in Marseille, miniature low poly stylized building for a tycoon city builder game, five storey cream stone facade, black iron balconies, red cafe awning on ground floor, grey zinc roof, clean chunky shapes, flat colors, isometric game asset
```

**immeuble_annees60.glb**
```
1960s Mediterranean apartment block, miniature low poly stylized building for a tycoon city builder game, white and pastel yellow facade, rows of balconies with colorful blinds, flat roof, clean chunky shapes, flat colors, isometric game asset
```
