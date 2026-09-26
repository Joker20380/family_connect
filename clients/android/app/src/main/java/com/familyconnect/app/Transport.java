package com.familyconnect.app;
public enum Transport {
    WG("wg","WireGuard"),AWG("awg","AmneziaWG"),TCP("tcp","TCP · REALITY");
    public final String id,label;
    Transport(String id,String label){this.id=id;this.label=label;}
    public static Transport parse(String id){for(Transport t:values())if(t.id.equals(id))return t;throw new IllegalArgumentException("Unsupported transport");}
}
