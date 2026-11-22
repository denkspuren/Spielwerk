/* Python-Schnipsel: dieselben JSON-Daten, anderes Ausgabeformat. */
window.SpielwerkCodegen.register({
  id:'python',label:'Python',
  generate({template:t}) {
    const name=t.id.replace(/^sw-/,'').replace(/[^A-Za-z0-9]/g,'_').toUpperCase();
    const h=t.hit;
    return `# Kopiervorlage für Python – wird NICHT automatisch eingefügt.
${name}_VORLAGE = "${t.id}"
${name}_BREITE = ${t.w}
${name}_HOEHE = ${t.h}
${name}_KOLLISION_X = ${h.x}
${name}_KOLLISION_Y = ${h.y}
${name}_KOLLISION_BREITE = ${h.w}
${name}_KOLLISION_HOEHE = ${h.h}

# Beispiel: im Spielstart ausgeben
print(f"CREATE held {${name}_VORLAGE}", flush=True)
print("MOVE held 100 100", flush=True)`;
  }
});
