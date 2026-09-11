using System.Net;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Net.Sockets;
namespace FamilyConnect;
internal static class TcpHealth
{
    // No IPC/profile supplied URLs. Probes must never silently use the physical uplink.
    public static async Task Watch(string adapter,CancellationToken token,int? awg=null)
    {
        int failures=0;
        while(true){
            await Task.Delay(TimeSpan.FromSeconds(15),token);
            var results=await Task.WhenAll(Probe(adapter,false,token,awg),Probe(adapter,true,token,awg));
            failures=results.Any(x=>x)?0:failures+1;
            if(failures==2)return;
        }
    }
    static async Task<bool> Probe(string adapter,bool second,CancellationToken token,int? awg)
    {
        using var deadline=CancellationTokenSource.CreateLinkedTokenSource(token);
        deadline.CancelAfter(TimeSpan.FromSeconds(8));
        try {
            TcpNetwork.ValidateAdapter(adapter);
#if TCP_SESSION_TEST
            var uri=new Uri("http://198.18.0.1/health/"+(second?"b":"a"));
            var source=IPAddress.Parse("198.18.0.2");
#else
            var uri=new Uri(second?"https://www.gstatic.com/generate_204":"https://1.1.1.1/cdn-cgi/trace");
            var source=IPAddress.Parse(awg is int n?"10.78.0."+n:"10.79.0.2");
#endif
            var nic=NetworkInterface.GetAllNetworkInterfaces().Single(n=>n.Name==adapter);
            var properties=nic.GetIPProperties();
            if(!properties.UnicastAddresses.Any(a=>a.Address.Equals(source)))return false;
            int index=properties.GetIPv4Properties().Index;
            using var handler=new SocketsHttpHandler{UseProxy=false,UseCookies=false,AllowAutoRedirect=false,MaxResponseHeadersLength=8,
                ConnectCallback=async(context,ct)=>{
                    var socket=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp);
                    try {
                        socket.SetSocketOption(SocketOptionLevel.IP,(SocketOptionName)31 /* Windows IP_UNICAST_IF (not exposed by the .NET enum) */,IPAddress.HostToNetworkOrder(index));
                        socket.Bind(new IPEndPoint(source,0));
                        var addresses=await Dns.GetHostAddressesAsync(context.DnsEndPoint.Host,AddressFamily.InterNetwork,ct);
                        await socket.ConnectAsync(addresses,context.DnsEndPoint.Port,ct);
                        return new NetworkStream(socket,ownsSocket:true);
                    }catch{socket.Dispose();throw;}
                }};
            using var client=new HttpClient(handler){Timeout=Timeout.InfiniteTimeSpan};
            using var response=await client.GetAsync(uri,HttpCompletionOption.ResponseHeadersRead,deadline.Token);
#if TCP_SESSION_TEST
            return response.StatusCode==HttpStatusCode.NoContent;
#else
            if(second)return response.StatusCode==HttpStatusCode.NoContent;
            if(response.StatusCode!=HttpStatusCode.OK)return false;
            await response.Content.LoadIntoBufferAsync(4096,deadline.Token);
            var body=await response.Content.ReadAsStringAsync(deadline.Token);
            return body.Split('\n').Any(line=>line.StartsWith("ip=",StringComparison.Ordinal)&&IPAddress.TryParse(line[3..].Trim(),out _));
#endif
        }catch(OperationCanceledException) when(token.IsCancellationRequested){throw;}
        catch(Exception){return false;}
    }
}
