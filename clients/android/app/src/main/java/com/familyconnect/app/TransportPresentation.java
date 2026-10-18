package com.familyconnect.app;

import com.google.gson.JsonObject;

final class TransportPresentation {
    static final String MESH="MESH";

    private TransportPresentation(){}

    static String label(String implementation){
        if("telemost".equals(implementation)||"restricted".equals(implementation))return MESH;
        if("auto".equals(implementation))return "Auto";
        if("awg".equals(implementation))return "AWG 3.1";
        if("wg".equals(implementation))return "WireGuard";
        if("tcp".equals(implementation))return "TCP REALITY";
        return "—";
    }

    static JsonObject diagnostics(){
        JsonObject media=new JsonObject();
        media.addProperty("name",MESH);
        media.addProperty("implementation","restricted");
        media.addProperty("selection_id","telemost");
        media.addProperty("carrier","VP8/RTP");
        media.addProperty("provider","Telemost");
        JsonObject catalog=new JsonObject();
        catalog.addProperty("schema",1);
        catalog.add("restricted",media);
        return catalog;
    }
}
