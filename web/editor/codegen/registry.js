/* Öffentliche, bewusst kleine Schnittstelle für eigenständige Schnipselgeneratoren. */
(() => {
  'use strict';
  const entries=new Map();
  window.SpielwerkCodegen=Object.freeze({
    register({id,label,generate,generateScene}) {
      if(!/^[a-z][a-z0-9_-]*$/.test(id)||typeof label!=='string'||typeof generate!=='function'||entries.has(id))
        throw new Error('Ungültiger oder doppelter Sprachgenerator: '+id);
      if(generateScene!==undefined && typeof generateScene!=='function') throw new Error('generateScene muss eine Funktion sein');
      entries.set(id,Object.freeze({id,label,generate,generateScene}));
    },
    get(id){return entries.get(id);},
    list(){return [...entries.values()].map(({id,label})=>({id,label}));}
  });
})();
