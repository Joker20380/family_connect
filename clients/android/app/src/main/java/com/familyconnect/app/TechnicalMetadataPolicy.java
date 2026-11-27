package com.familyconnect.app;

import java.util.HashMap;
import java.util.Map;

final class TechnicalMetadataPolicy {
    static final String POLICY="basic-2026-11-v1";
    static final long MAX=9007199254740991L;
    interface Store {
        Map<String,Object> read();
        boolean commit(Map<String,Object> values);
    }
    static final class Ticket {
        final long epoch,sequence;
        final boolean sample;
        Ticket(long epoch,long sequence,boolean sample){this.epoch=epoch;this.sequence=sequence;this.sample=sample;}
    }
    private final Store store;
    private Map<String,Object> state;
    private boolean fault;
    TechnicalMetadataPolicy(Store store){this.store=store;state=new HashMap<>(store.read());}
    private long number(String name){Object value=state.get(name);return value instanceof Long?(Long)value:0;}
    private boolean flag(String name){return Boolean.TRUE.equals(state.get(name));}
    String mode(){return fault?"STORAGE_FAULT":String.valueOf(state.getOrDefault("mode","UNINITIALIZED"));}
    boolean pending(){return flag("revoke_pending");}
    boolean enabled(){return !fault&&"BASIC".equals(mode())&&POLICY.equals(state.get("notice_policy"))&&number("epoch")>0;}
    boolean needsNotice(){return !fault&&"NOTICE_PENDING".equals(mode());}
    boolean faulted(){return fault;}
    void failStorage(){fault=true;}
    private boolean save(Map<String,Object> next){
        if(!store.commit(new HashMap<>(next))){fault=true;return false;}
        state=next;return true;
    }
    boolean initialize(boolean provenFresh,String installation){
        if(installation==null||installation.isEmpty()){fault=true;return false;}
        if(state.containsKey("contract")){
            if(!Integer.valueOf(2).equals(state.get("contract"))||number("epoch")<=0||number("epoch")>MAX||number("sequence")<=0||number("sequence")>MAX){fault=true;return false;}
            if(!installation.equals(state.get("installation"))){
                Map<String,Object> next=new HashMap<>(state);next.put("mode","RESTORED_BLOCKED");return save(next);
            }
            return true;
        }
        long epoch=number("epoch"),sequence=number("sequence");
        if(epoch<0||sequence<0||epoch>MAX||sequence>MAX||pending()&&epoch==0){fault=true;return false;}
        boolean refused=pending()||state.containsKey("enabled")&&!flag("enabled")||epoch>0&&!state.containsKey("enabled");
        Map<String,Object> next=new HashMap<>(state);
        next.put("contract",2);next.put("installation",installation);
        next.put("origin",refused?"LEGACY_REFUSAL":flag("enabled")?"LEGACY_ENABLED":provenFresh?"FRESH":"LEGACY_UNDECIDED");
        next.put("mode",refused?"OFF":"NOTICE_PENDING");next.put("enabled",false);
        next.put("epoch",Math.max(1,epoch));next.put("sequence",Math.max(1,sequence));
        return save(next);
    }
    boolean noticeShown(boolean basisApproved){
        if(!needsNotice()||!basisApproved)return false;
        Map<String,Object> next=new HashMap<>(state);next.put("mode","BASIC");next.put("notice_policy",POLICY);
        return save(next);
    }
    boolean object(){
        if(fault)return false;
        if(pending()||"OFF".equals(mode()))return true;
        long epoch=number("epoch");
        if(epoch<=0||epoch>=MAX){fault=true;return false;}
        Map<String,Object> next=new HashMap<>(state);next.put("mode","OFF");next.put("enabled",false);
        next.put("epoch",epoch+1);next.put("revoke_pending",true);return save(next);
    }
    boolean resumeBasic(boolean basisApproved){
        if(fault||!basisApproved||pending()||!"OFF".equals(mode())||number("epoch")>=MAX)return false;
        Map<String,Object> next=new HashMap<>(state);next.put("epoch",number("epoch")+1);
        next.put("mode","NOTICE_PENDING");next.remove("notice_policy");return save(next);
    }
    Ticket reserve(){
        if(fault||(!enabled()&&!pending())||number("epoch")<=0||number("sequence")>=MAX)return null;
        Map<String,Object> next=new HashMap<>(state);next.put("sequence",number("sequence")+1);
        if(!save(next))return null;
        return new Ticket(number("epoch"),number("sequence"),enabled()&&!pending());
    }
    boolean current(Ticket ticket){return !fault&&ticket.epoch==number("epoch")&&ticket.sample==(enabled()&&!pending());}
    boolean acknowledge(Ticket ticket){
        if(!current(ticket))return false;
        if(ticket.sample)return true;
        Map<String,Object> next=new HashMap<>(state);next.put("revoke_pending",false);return save(next);
    }
}
