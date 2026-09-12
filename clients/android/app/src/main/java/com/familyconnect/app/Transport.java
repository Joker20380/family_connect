package com.familyconnect.app;
public enum Transport {
    WG("wg"),AWG("awg"),TCP("tcp");
    public final String id;
    Transport(String id){this.id=id;}
    public static Transport parse(String id){for(Transport t:values())if(t.id.equals(id))return t;throw new IllegalArgumentException("Unsupported transport");}
}
