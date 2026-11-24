/* Java-Schnipsel: liest nur das sprachneutrale Entwurfsmodell. */
window.SpielwerkCodegen.register({
  id:'java',label:'Java',
  generate({template:t}) {
    const name=t.id.replace(/^sw-/,'').replace(/[^A-Za-z0-9]/g,'_').toUpperCase();
    const h=t.hit;
    return `// Kopiervorlage für eine Java-Klasse – wird NICHT automatisch eingefügt.
static final String ${name}_VORLAGE = "${t.id}";
static final int ${name}_BREITE = ${t.w};
static final int ${name}_HOEHE = ${t.h};
static final int ${name}_KOLLISION_X = ${h.x};
static final int ${name}_KOLLISION_Y = ${h.y};
static final int ${name}_KOLLISION_BREITE = ${h.w};
static final int ${name}_KOLLISION_HOEHE = ${h.h};

// Diese Methode im Spielstart aufrufen.
static void ${name.toLowerCase()}_anlegen() {
    System.out.println("CREATE held " + ${name}_VORLAGE);
    System.out.println("MOVE held 100 100");
}`;
  },
  generateScene({scene}) {
    const lines=scene.objects.filter(o=>o.mode==='dynamic').flatMap(o=>[
      `System.out.println("CREATE ${o.id} ${o.template}");`,
      `System.out.println("MOVE ${o.id} ${o.x} ${o.y}");`,
      `System.out.println("SHOW ${o.id}");`
    ]);
    return '// Kopiervorlage für eine Java-Methode. Keine automatische Änderung.\n'+
      (lines.length?lines.join('\n'):'// Keine dynamischen Objekte in dieser Szene.')+'\n';
  }
});
