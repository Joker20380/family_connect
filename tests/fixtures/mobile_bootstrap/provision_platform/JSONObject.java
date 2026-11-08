package org.json;
import com.google.gson.*;
public class JSONObject {
    private final JsonObject value;
    public JSONObject(){value=new JsonObject();}public JSONObject(String raw){value=JsonParser.parseString(raw).getAsJsonObject();}
    public int optInt(String key,int fallback){return value.has(key)?value.get(key).getAsInt():fallback;}
    public JSONObject put(String key,Object input){value.add(key,new Gson().toJsonTree(input));return this;}
    public String toString(){return value.toString();}
}
