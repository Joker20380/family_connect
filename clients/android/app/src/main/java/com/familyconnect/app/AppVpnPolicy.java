package com.familyconnect.app;

import java.util.Collection;
import java.util.Collections;
import java.util.Set;
import java.util.TreeSet;

final class AppVpnPolicy {
    enum Mode { ALL, INCLUDE, EXCLUDE }
    final Mode mode;
    final Set<String> included;
    final Set<String> excluded;

    AppVpnPolicy(Mode mode, Collection<String> included, Collection<String> excluded) {
        if(mode==null)throw new IllegalArgumentException("APP_POLICY_INVALID");
        this.mode=mode;this.included=packages(included);this.excluded=packages(excluded);
    }
    static AppVpnPolicy all(){return new AppVpnPolicy(Mode.ALL,Set.of(),Set.of());}
    private static Set<String> packages(Collection<String> source){
        if(source==null||source.size()>4096)throw new IllegalArgumentException("APP_POLICY_INVALID");
        TreeSet<String> result=new TreeSet<>();
        for(String name:source){
            if(name==null||name.length()>255||!name.matches("[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z][A-Za-z0-9_]*)*"))
                throw new IllegalArgumentException("APP_POLICY_INVALID");
            result.add(name);
        }
        return Collections.unmodifiableSet(result);
    }
    Set<String> selected(){return mode==Mode.INCLUDE?included:mode==Mode.EXCLUDE?excluded:Set.of();}
    void requireConnectable(){
        if(mode==Mode.INCLUDE&&included.isEmpty())throw new IllegalArgumentException("APP_POLICY_EMPTY");
    }
    @Override public boolean equals(Object other){
        if(!(other instanceof AppVpnPolicy))return false;
        AppVpnPolicy policy=(AppVpnPolicy)other;
        return mode==policy.mode&&included.equals(policy.included)&&excluded.equals(policy.excluded);
    }
    @Override public int hashCode(){return java.util.Objects.hash(mode,included,excluded);}
}
