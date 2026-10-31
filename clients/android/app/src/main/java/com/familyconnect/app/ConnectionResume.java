package com.familyconnect.app;

final class ConnectionResume {
    static boolean allowed(boolean requested,boolean permission,String transport) {
        return requested&&permission&&("auto".equals(transport)||"telemost".equals(transport));
    }
}
