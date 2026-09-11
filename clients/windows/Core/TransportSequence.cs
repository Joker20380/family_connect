namespace FamilyConnect;
// A connection request visits each activated transport once. Cleanup is a hard boundary.
public static class TransportSequence
{
    public sealed class CleanupException:Exception {}
    public static async Task Run(IEnumerable<string> choices,Func<string,Action,CancellationToken,Task> use,
        Func<string,Task> cleanup,Action<string,bool> report,CancellationToken token)
    {
        foreach(var transport in choices){
            token.ThrowIfCancellationRequested();report(transport,false);
            try{await use(transport,()=>{token.ThrowIfCancellationRequested();report(transport,true);},token);}
            catch(OperationCanceledException) when(token.IsCancellationRequested){}
            catch(Exception){}
            finally{
                report(transport,false);
                try{await cleanup(transport);}catch{throw new CleanupException();}
            }
            token.ThrowIfCancellationRequested();
        }
    }
}
