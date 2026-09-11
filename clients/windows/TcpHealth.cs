using System.Net;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Net.Sockets;
namespace FamilyConnect;
internal static class TcpHealth
{
    // No IPC/profile supplied URLs. Probes must never silently use the physical uplink.
    public static async Task Watch(string adapter,CancellationToken token,int? awg=null,bool wireguard=false)
    {
        int failures=0;
        while(true){
            await Task.Delay(TimeSpan.FromSeconds(15),token);
            var results=await Task.WhenAll(Probe(adapter,false,token,awg,wireguard),Probe(adapter,true,token,awg,wireguard));
            failures=results.Any(x=>x)?0:failures+1;
            if(failures==2)return;
        }
    }
    public static async Task<bool> Ready(string adapter,CancellationToken token,int? awg=null,bool wireguard=false){
        for(int i=0;i<2;i++){
            token.ThrowIfCancellationRequested();
            if((await Task.WhenAll(Probe(adapter,false,token,awg,wireguard),Probe(adapter,true,token,awg,wireguard))).Any(x=>x))return true;
            if(i==0)await Task.Delay(TimeSpan.FromSeconds(5),token);
        }return false;
    }
    static async Task<bool> Probe(string adapter,bool second,CancellationToken token,int? awg,bool wireguard)
    {
        using var deadline=CancellationTokenSource.CreateLinkedTokenSource(token);
        deadline.CancelAfter(TimeSpan.FromSeconds(8));
        try {
            if(wireguard){if(adapter!="fc-native")throw new FormatException("WG adapter");}else TcpNetwork.ValidateAdapter(adapter);
#if TCP_SESSION_TEST
            var uri=new Uri("http://198.18.0.1/health/"+(second?"b":"a"));
            var source=IPAddress.Parse("198.18.0.2");
#else
            var uri=new Uri(second?"https://www.gstatic.com/generate_204":"https://1.1.1.1/cdn-cgi/trace");
            var source=IPAddress.Parse(awg is int n?"10.78.0."+n:"10.79.0.2");
#endif
            var nic=NetworkInterface.GetAllNetworkInterfaces().Single(n=>n.Name==adapter);
            var properties=nic.GetIPProperties();
            if(wireguard)source=properties.UnicastAddresses.Select(x=>x.Address).Single(x=>x.AddressFamily==AddressFamily.InterNetwork&&x.ToString().StartsWith("10.77.0.",StringComparison.Ordinal));
            if(!properties.UnicastAddresses.Any(a=>a.Address.Equals(source)))return false;
            int index=properties.GetIPv4Properties().Index;
#if TCP_SESSION_TEST
            if(awg is not null){
                using var udp=new Socket(AddressFamily.InterNetwork,SocketType.Dgram,ProtocolType.Udp);
                udp.SetSocketOption(SocketOptionLevel.IP,(SocketOptionName)31,IPAddress.HostToNetworkOrder(index));udp.Bind(new IPEndPoint(source,0));
                await udp.ConnectAsync(new IPEndPoint(IPAddress.Parse("198.18.0.1"),18765),deadline.Token);
                byte[] request=System.Security.Cryptography.RandomNumberGenerator.GetBytes(32),reply=new byte[64];
                await udp.SendAsync(request,SocketFlags.None,deadline.Token);
                int n=await udp.ReceiveAsync(reply,SocketFlags.None,deadline.Token);return n==request.Length&&request.AsSpan().SequenceEqual(reply.AsSpan(0,n));
            }
#endif
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
