package com.familyconnect.app;

final class GatewayPicker {
    private GatewayPicker(){}

    static boolean manual(String transport){return "awg".equals(transport)||"tcp".equals(transport)||"telemost".equals(transport);}

    static String[] targets(String transport){
        java.util.List<String> targets=new java.util.ArrayList<>();
        targets.add("ru");targets.addAll(ControlFriendsCatalog.GATEWAYS);
        return targets.toArray(new String[0]);
    }

    static String[] readinessTargets(String target,String transport){
        return ("telemost".equals(transport)||"auto".equals(transport))&&RestrictedGateway.SECONDARY.equals(target)
            ?new String[]{RestrictedGateway.PRIMARY,RestrictedGateway.SECONDARY}:new String[]{RestrictedGateway.PRIMARY};
    }

    static String target(String country,String gateway,String transport){
        if("ru".equals(country)||ControlFriendsCatalog.explicit(country))return country;
        return ControlFriendsCatalog.explicit(gateway)?gateway:"nl-amsterdam-1";
    }

    static boolean meshSupported(String target){return target==null||"nl".equals(target)||ControlFriendsCatalog.explicit(target);}
    static boolean available(String target,String transport){return !"telemost".equals(transport)||meshSupported(target);}
}
