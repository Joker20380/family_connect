package com.familyconnect.app;

final class DiagnosticLauncher {
    interface Host<Component> {
        Component resolve();
        void start(Component component);
    }
    static <Component> boolean open(Host<Component> host) {
        try {
            Component component=host.resolve();
            if(component==null)return false;
            host.start(component);
            return true;
        }catch(RuntimeException unavailable){return false;}
    }
}
