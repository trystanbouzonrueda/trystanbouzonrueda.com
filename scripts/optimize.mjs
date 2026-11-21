// Optimise les GLB exportés de Blender pour le web.
// Blocs à couleur unie : on retire les normales (three.js fait l'ombrage facetté avec flatShading),
// ce qui permet de fusionner les sommets (÷3 à ÷4), puis quantification + compression meshopt.
// Modèles texturés (Meshy) : normales gardées, textures en webp 1024.
// Usage : node scripts/optimize.mjs entree.glb sortie.glb
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { dedup, prune, quantize, weld, textureCompress, meshopt, joinPrimitives } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const [, , input, output] = process.argv;
await MeshoptDecoder.ready;
await MeshoptEncoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });

const doc = await io.read(input);
let stripped = 0;
for (const mesh of doc.getRoot().listMeshes()) {
  for (const prim of mesh.listPrimitives()) {
    const mat = prim.getMaterial();
    if (mat && !mat.getBaseColorTexture() && prim.getAttribute('NORMAL')) {
      prim.setAttribute('NORMAL', null);
      if (prim.getAttribute('TEXCOORD_0')) prim.setAttribute('TEXCOORD_0', null);
      stripped++;
    }
  }
}
// Palette : couleur unie → couleur de sommet (COLOR_0) + un matériau partagé par rugosité, puis les primitives
// d'un même maillage fusionnées. Un arrondissement passe de ~20 draw calls à 2–3. Les nœuds ne bougent pas
// (lieux cliquables intacts). Gardés à part : matériaux lus par le site (nuit, mer) et texturés.
const KEEP = /^M_(fenetre|fenetre_sombre|lampadaire|jaune|or|mer|cascade|verre|verre_bureau|verre_fonce|vitre_cesi)(\.\d+)?$/;
const shared = new Map();
const paletteOf = (mat) => {
  const key = `${mat.getRoughnessFactor().toFixed(2)}|${mat.getMetallicFactor().toFixed(2)}|${mat.getDoubleSided()}`;
  if (!shared.has(key)) {
    shared.set(key, doc.createMaterial(`palette_${shared.size}`)
      .setBaseColorFactor([1, 1, 1, 1]).setRoughnessFactor(mat.getRoughnessFactor())
      .setMetallicFactor(mat.getMetallicFactor()).setDoubleSided(mat.getDoubleSided()));
  }
  return shared.get(key);
};
const buffer = doc.getRoot().listBuffers()[0];
let joined = 0;
for (const mesh of doc.getRoot().listMeshes()) {
  const groups = new Map();
  for (const prim of mesh.listPrimitives()) {
    const mat = prim.getMaterial();
    if (!mat || mat.getBaseColorTexture() || KEEP.test(mat.getName()) || mat.getAlphaMode() !== 'OPAQUE'
        || mat.getEmissiveFactor().some((x) => x > 0) || prim.getAttribute('COLOR_0') || prim.getMode() !== 4) continue;
    const pos = prim.getAttribute('POSITION');
    const [r, g, b] = mat.getBaseColorFactor(); // déjà linéaire, comme COLOR_0
    const col = new Float32Array(pos.getCount() * 3);
    for (let i = 0; i < pos.getCount(); i++) col.set([r, g, b], i * 3);
    prim.setAttribute('COLOR_0', doc.createAccessor().setType('VEC3').setArray(col).setBuffer(buffer));
    const pal = paletteOf(mat);
    prim.setMaterial(pal);
    const key = `${pal.getName()}|${prim.listSemantics().sort().join()}|${!!prim.getIndices()}`;
    groups.set(key, [...(groups.get(key) ?? []), prim]);
  }
  for (const prims of groups.values()) {
    if (prims.length < 2) continue;
    const merged = joinPrimitives(prims);
    mesh.addPrimitive(merged);
    prims.forEach((p) => { mesh.removePrimitive(p); p.dispose(); });
    joined += prims.length - 1;
  }
}

await doc.transform(
  dedup(),
  weld(),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024] }),
  quantize(),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  prune(),
);
doc.createExtension(EXTMeshoptCompression).setRequired(true);
await io.write(output, doc);
console.log(`${input} -> ${output} : ${stripped} primitives sans normales, ${joined} fusionnées (palette)`);
