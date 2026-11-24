/* Szeneneditor-Dateiverwaltung: nur die sprachneutrale layout.json.
 * Unabhängig vom GameModule, der Prozesssteuerung und dem Spielprotokoll.
 * Absichtlich nur JDK-Klassen; keine JSON-Bibliothek erforderlich.
 */
import com.sun.net.httpserver.HttpExchange;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.charset.CodingErrorAction;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;

final class SceneModule {
    private static final int LIMIT = 64_000;
    private static final Pattern IDENT = Pattern.compile("[A-Za-z][A-Za-z0-9_-]{0,63}");
    private static final Pattern COLOR = Pattern.compile("#[0-9a-fA-F]{6}");
    private final Path gameDir, sourceDir, outputDir, layout;
    SceneModule(Path gameDir, Path editorWeb) {
        this.gameDir = gameDir;
        this.sourceDir = editorWeb.resolve("scene");
        this.outputDir = gameDir.resolve("spielwerk");
        this.layout = outputDir.resolve("layout.json");
    }
    boolean get(HttpExchange ex, String path) throws IOException {
        String filename = switch (path) {
            case "/editor/scene", "/editor/scene/" -> "index.html";
            case "/editor/scene/scene.js" -> "scene.js";
            case "/editor/scene/scene.css" -> "scene.css";
            case "/editor/scene/scene-model.js" -> "scene-model.js";
            default -> null;
        };
        if (filename != null) {
            Path target = sourceDir.resolve(filename);
            if (!Files.isRegularFile(target)) {send(ex,404,"Nicht gefunden");return true;}
            String type = filename.endsWith(".js") ? "text/javascript; charset=utf-8" :
                    filename.endsWith(".css") ? "text/css; charset=utf-8" : "text/html; charset=utf-8";
            send(ex, 200, Files.readAllBytes(target), type);
            return true;
        }
        if (!path.equals("/editor/api/scene") && !path.equals("/game/spielwerk/layout.json")) return false;
        if (Files.isRegularFile(layout) && !Files.isSymbolicLink(layout) &&
                !Files.isSymbolicLink(outputDir) && layout.toRealPath().startsWith(gameDir.toRealPath())) {
            send(ex, 200, Files.readAllBytes(layout), "application/json; charset=utf-8");
        } else if (path.equals("/editor/api/scene")) {
            int[] dimensions = dimensions();
            send(ex, 200, "{\"version\":1,\"width\":"+dimensions[0]+",\"height\":"+dimensions[1]+
                    ",\"background\":\"#12243b\",\"objects\":[]}", "application/json; charset=utf-8");
        } else send(ex,404,"Nicht gefunden");
        return true;
    }
    boolean post(HttpExchange ex, String path) throws IOException {
        if (!path.equals("/editor/api/scene/save")) return false;
        int size;
        try {size = Integer.parseInt(ex.getRequestHeaders().getFirst("Content-Length"));}
        catch (Exception e) {send(ex,411,"Content-Length erforderlich");return true;}
        if (size < 2 || size > LIMIT) {send(ex,413,"Szenendatei zu groß");return true;}
        byte[] bytes = ex.getRequestBody().readNBytes(size);
        if (bytes.length != size) {send(ex,400,"Unvollständige Anfrage");return true;}
        String raw;
        try { raw = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString(); }
        catch (Exception e) {send(ex,400,"Ungültiges UTF-8");return true;}
        try {validate(new JsonParser(raw).parse());}
        catch (IllegalArgumentException e) {send(ex,400,"Ungültiges Szenenformat: "+e.getMessage());return true;}
        if (Files.isSymbolicLink(outputDir) || Files.isSymbolicLink(layout) ||
                !outputDir.toAbsolutePath().normalize().startsWith(gameDir.toAbsolutePath().normalize())) {
            send(ex,403,"Symbolische Links nicht erlaubt");return true;
        }
        Files.createDirectories(outputDir);
        Path temporary = Files.createTempFile(outputDir,".sw-layout-",".json");
        try {
            Files.writeString(temporary,raw,StandardCharsets.UTF_8);
            try {Files.move(temporary,layout,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
            catch (AtomicMoveNotSupportedException e) {Files.move(temporary,layout,StandardCopyOption.REPLACE_EXISTING);}
        } finally {Files.deleteIfExists(temporary);}
        send(ex,200,"Gespeichert");return true;
    }
    private int[] dimensions() {
        int[] result = {640,480};
        Path ini = gameDir.resolve("game.ini");
        if (!Files.isRegularFile(ini)) return result;
        try {
            boolean section = false;
            for (String raw : Files.readAllLines(ini,StandardCharsets.UTF_8)) {
                String line = raw.strip();
                if (line.startsWith("[") && line.endsWith("]")) section = line.equalsIgnoreCase("[game]");
                else if (section && line.contains("=")) {
                    String key = line.substring(0,line.indexOf('=')).strip();
                    String val = line.substring(line.indexOf('=')+1).strip();
                    if (key.equals("width") || key.equals("height")) {
                        try {int n=Integer.parseInt(val);if(n>=200 && n<=2048)result[key.equals("width")?0:1]=n;}
                        catch (NumberFormatException ignored) { }
                    }
                }
            }
        } catch (IOException ignored) { }
        return result;
    }
    private static void validate(Object value) {
        if (!(value instanceof Map<?,?> root)) throw new IllegalArgumentException("Objekt erwartet");
        if (!Integer.valueOf(1).equals(root.get("version"))) throw new IllegalArgumentException("Version 1 erwartet");
        for (String k : List.of("width","height")) {
            Object n=root.get(k);
            if (!(n instanceof Integer i) || i<200 || i>2048) throw new IllegalArgumentException("Spielfeldgröße ungültig");
        }
        if (!(root.get("background") instanceof String color) || !COLOR.matcher(color).matches())
            throw new IllegalArgumentException("Ungültige Hintergrundfarbe");
        if (!(root.get("objects") instanceof List<?> objects) || objects.size()>200)
            throw new IllegalArgumentException("Maximal 200 Objekte erlaubt");
        Set<String> seen = new HashSet<>();
        for (Object item : objects) {
            if (!(item instanceof Map<?,?> object)) throw new IllegalArgumentException("Objekt erwartet");
            Object id=object.get("id"), template=object.get("template"), mode=object.get("mode");
            if (!(id instanceof String name) || !IDENT.matcher(name).matches() || !seen.add(name))
                throw new IllegalArgumentException("Ungültige oder doppelte Objekt-ID");
            if (!(template instanceof String t) || !IDENT.matcher(t).matches())
                throw new IllegalArgumentException("Ungültige Template-ID");
            if (!(mode instanceof String m) || !(m.equals("static") || m.equals("dynamic")))
                throw new IllegalArgumentException("Ungültiger Objektmodus");
            for (String key : List.of("x","y")) {
                Object v=object.get(key);
                if (!(v instanceof Integer n) || Math.abs((long)n)>10000)
                    throw new IllegalArgumentException("Ungültige Koordinate");
            }
        }
    }
    /* Kleiner strikter JSON-Parser. Nur interne Szenendaten, niemals Codeausführung. */
    private static final class JsonParser {
        final String s; int pos, depth;
        JsonParser(String s){this.s=s;}
        Object parse(){Object x=value();white();if(pos!=s.length())bad();return x;}
        void white(){while(pos<s.length() && " \n\t\r".indexOf(s.charAt(pos))>=0)pos++;}
        void bad(){throw new IllegalArgumentException("JSON bei Zeichen "+pos);}
        boolean consume(char c){white();if(pos<s.length() && s.charAt(pos)==c){pos++;return true;}return false;}
        void need(char c){if(!consume(c))bad();}
        Object value(){
            white();if(pos>=s.length())bad();char c=s.charAt(pos);
            if(c=='{' || c=='['){if(++depth>40)bad();Object result=c=='{'?object():array();depth--;return result;}
            if(c=='"')return string();
            if(c=='-' || Character.isDigit(c))return number();
            for (String word : List.of("true","false","null")) if(s.startsWith(word,pos)) {
                pos+=word.length();return word.equals("true")?Boolean.TRUE:word.equals("false")?Boolean.FALSE:null;
            }
            bad();return null;
        }
        Map<String,Object> object(){
            need('{');Map<String,Object> m=new LinkedHashMap<>();if(consume('}'))return m;
            do {white();if(pos>=s.length() || s.charAt(pos)!='"')bad();String key=string();need(':');
                if(m.containsKey(key))bad();m.put(key,value());if(consume('}'))return m;need(',');
            } while(true);
        }
        List<Object> array(){
            need('[');List<Object> a=new ArrayList<>();if(consume(']'))return a;
            do {if(a.size()>2000)bad();a.add(value());if(consume(']'))return a;need(',');}while(true);
        }
        String string(){
            need('"');StringBuilder b=new StringBuilder();
            while(pos<s.length()) {
                char c=s.charAt(pos++);if(c=='"')return b.toString();
                if(c<0x20)bad();
                if(c=='\\'){
                    if(pos>=s.length())bad();char e=s.charAt(pos++);
                    switch(e){case '"','\\','/' -> b.append(e);case 'b' -> b.append('\b');case 'f' -> b.append('\f');
                        case 'n' -> b.append('\n');case 'r' -> b.append('\r');case 't' -> b.append('\t');
                        case 'u' -> {if(pos+4>s.length())bad();try{b.append((char)Integer.parseInt(s.substring(pos,pos+4),16));}
                            catch(NumberFormatException ex){bad();}pos+=4;}
                        default -> bad();}
                }else b.append(c);
            }
            bad();return null;
        }
        Number number(){
            int start=pos;if(s.charAt(pos)=='-')pos++;
            if(pos>=s.length()||!Character.isDigit(s.charAt(pos)))bad();
            if(s.charAt(pos)=='0')pos++;
            else while(pos<s.length() && Character.isDigit(s.charAt(pos)))pos++;
            if(pos<s.length() && ".eE".indexOf(s.charAt(pos))>=0) {
                while(pos<s.length() && "0123456789.+-eE".indexOf(s.charAt(pos))>=0)pos++;
                try{return Double.parseDouble(s.substring(start,pos));}catch(NumberFormatException e){bad();}
            }
            try{return Integer.parseInt(s.substring(start,pos));}catch(NumberFormatException e){bad();}
            return 0;
        }
    }
    private static void send(HttpExchange ex,int code,String text)throws IOException{
        send(ex,code,text.getBytes(StandardCharsets.UTF_8),"text/plain; charset=utf-8");
    }
    private static void send(HttpExchange ex,int code,String text,String mime)throws IOException{
        send(ex,code,text.getBytes(StandardCharsets.UTF_8),mime);
    }
    private static void send(HttpExchange ex,int code,byte[] bytes,String mime)throws IOException{
        ex.getResponseHeaders().set("Content-Type",mime);
        ex.getResponseHeaders().set("Cache-Control","no-store");
        ex.getResponseHeaders().set("X-Content-Type-Options","nosniff");
        ex.sendResponseHeaders(code,bytes.length);
        try(OutputStream stream=ex.getResponseBody()){stream.write(bytes);}
    }
}
