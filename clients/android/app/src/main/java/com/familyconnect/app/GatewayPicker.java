package com.familyconnect.app;

final class GatewayPicker {
    private GatewayPicker(){}

    static boolean manual(String transport){return "awg".equals(transport)||"tcp".equals(transport)||"telemost".equals(transport);}

    static String[] targets(String transport){
        if("telemost".equals(transport))return new String[]{"nl-amsterdam-1","nl-amsterdam-2"};
        return manual(transport)?new String[]{"nl-amsterdam-1","ru","nl-amsterdam-2"}:new String[]{"nl","ru"};
    }

    static String target(String country,String gateway,String transport){
        if("ru".equals(country)&&!"telemost".equals(transport))return "ru";
        if(!manual(transport))return "nl";
        return ControlFriendsCatalog.explicit(gateway)?gateway:"nl-amsterdam-1";
    }
}
