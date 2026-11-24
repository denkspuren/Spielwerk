/* Sprachneutrales Szenenmodell. Keine Spielprozesse, keine DOM-Abhängigkeit.
 * UMD: gleicher Code im Browser und in Node-Tests.
 */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SpielwerkSceneModel = api;
})(typeof globalThis === 'object' ? globalThis : this, function() {
  'use strict';
  const IDENT = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/;
  const TEMPLATE = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/;
  function fresh(width=640, height=480) {
    return {version:1,width,height,background:'#12243b',objects:[]};
  }
  function validate(input) {
    if (!input || input.version !== 1 || !Array.isArray(input.objects))
      throw Error('Unbekanntes Szenenformat (Version 1 erwartet).');
    if (!Number.isInteger(input.width) || input.width < 200 || input.width > 2048 ||
        !Number.isInteger(input.height) || input.height < 200 || input.height > 2048)
      throw Error('Ungültige Spielfeldgröße (200–2048 Pixel).');
    if (!/^#[0-9a-fA-F]{6}$/.test(input.background))
      throw Error('Ungültige Hintergrundfarbe.');
    if (input.objects.length > 200) throw Error('Höchstens 200 Szenenobjekte.');
    const ids = new Set();
    for (const o of input.objects) {
      if (!o || typeof o.id!=='string' || !IDENT.test(o.id) || ids.has(o.id))
        throw Error('Objekt-IDs müssen eindeutig sein und mit einem Buchstaben beginnen.');
      ids.add(o.id);
      if (typeof o.template!=='string' || !TEMPLATE.test(o.template)) throw Error('Ungültige Template-ID.');
      if (!['static','dynamic'].includes(o.mode)) throw Error('Objektmodus muss statisch oder dynamisch sein.');
      if (!Number.isInteger(o.x) || !Number.isInteger(o.y) ||
          Math.abs(o.x) > 10000 || Math.abs(o.y) > 10000) throw Error('Koordinaten außerhalb des erlaubten Bereichs.');
    }
    return input;
  }
  function nextId(objects, prefix='objekt') {
    const used = new Set(objects.map(o=>o.id));
    let i=1;while(used.has(prefix+i))i++;
    return prefix+i;
  }
  return Object.freeze({fresh, validate, nextId});
});
