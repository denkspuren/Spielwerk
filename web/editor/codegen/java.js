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
  }
});
