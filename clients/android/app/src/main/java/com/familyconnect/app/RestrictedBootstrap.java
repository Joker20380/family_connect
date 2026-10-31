package com.familyconnect.app;

import java.util.Arrays;
import java.util.function.LongSupplier;

final class RestrictedBootstrap {
    interface Fetch { byte[] run() throws Exception; }
    static final class Selection {
        final ReadinessImportResult result;
        final String status;
        final boolean authorizationRejected;
        final boolean availabilityFailure;
        final byte[] response;
        Selection(ReadinessImportResult result,String status,boolean rejected,byte[] response){
            this(result,status,rejected,response,false);
        }
        Selection(ReadinessImportResult result,String status,boolean rejected,byte[] response,boolean unavailable){
            this.result=result;this.status=status;authorizationRejected=rejected;this.response=response;
            availabilityFailure=unavailable&&!rejected;
        }
    }
    static byte[] select(byte[] response,boolean availabilityFailure,boolean restoring)throws ConnectivityOrchestrator.Rejected{
        if(availabilityFailure&&(restoring||response==null))
            throw new ConnectivityOrchestrator.Rejected(ConnectivityOrchestrator.Failure.BOOTSTRAP_UNAVAILABLE,true);
        return response==null?null:response.clone();
    }
    static boolean unavailable(Exception failure){
        return FriendsReadinessProtocol.unavailable(failure);
    }
    static Selection refresh(RestrictedCache cache,ReadinessProduct product,OwnerPrewarmReceipt receipt,
            Fetch fetch,Object lock,LongSupplier now)throws Exception{
        byte[] response;
        try{response=fetch.run();}
        catch(Exception failure){
            receipt.failed();
            boolean rejected=failure instanceof FriendsReadinessProtocol.AuthorizationFailure
                ||failure instanceof FriendsReadinessProtocol.ChallengeFailure
                &&((FriendsReadinessProtocol.ChallengeFailure)failure).code==FriendsReadinessProtocol.ChallengeCode.CHALLENGE_UNAUTHORIZED;
            ReadinessImportResult.Code code=rejected?ReadinessImportResult.Code.AUTHORIZATION_REJECTED:ReadinessImportResult.Code.FETCH_FAILED;
            byte[] cached=null;
            boolean retry=false;
            synchronized(lock){
                if(rejected){try{cache.denied();}catch(Exception storage){code=ReadinessImportResult.Code.PERSISTENCE_FAILED;}}
                else if(unavailable(failure)){cached=cached(cache,now.getAsLong());retry=cache.refreshable(now.getAsLong());}
            }
            String status=rejected?"AUTHORIZATION_REJECTED":failure instanceof FriendsReadinessProtocol.ChallengeFailure?
                ((FriendsReadinessProtocol.ChallengeFailure)failure).code.name():"UNAVAILABLE";
            return new Selection(product.failed(receipt,code,now.getAsLong()),cached==null?status:"CACHED_VALID_REFRESH_UNAVAILABLE",rejected,cached,retry);
        }
        try{
            ReadinessImportResult result;
            synchronized(lock){result=product.imported(response,receipt,now.getAsLong());}
            if(result.code()!=ReadinessImportResult.Code.READY){receipt.failed();return new Selection(result,result.code().name(),false,null);}
            receipt.imported(response);
            return new Selection(result,"SUCCESS",false,response.clone());
        }finally{if(response!=null)Arrays.fill(response,(byte)0);}
    }
    private static byte[] cached(RestrictedCache cache,long now)throws Exception{
        return cache.usable(now);
    }
}
