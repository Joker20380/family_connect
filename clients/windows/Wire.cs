using System.Buffers.Binary;
using System.IO.Pipes;
using System.Text.Json;
namespace FamilyConnect;
public sealed record Request(string Action, string? Activation=null);
public sealed record Reply(bool Ok, string State, string? Code=null, string? Error=null);
public static class Wire
{
    public const string Pipe="FamilyConnect.Broker.v1";
    public static async Task<T> Read<T>(Stream stream,CancellationToken token)
    {
        byte[] header=new byte[4]; await stream.ReadExactlyAsync(header,token);
        int length=BinaryPrimitives.ReadInt32LittleEndian(header);
        if(length<1 || length>16384)throw new IOException("size");
        byte[] data=new byte[length];await stream.ReadExactlyAsync(data,token);
        return JsonSerializer.Deserialize<T>(data,Activation.Json) ?? throw new IOException("message");
    }
    public static async Task Write<T>(Stream stream,T value,CancellationToken token)
    {
        byte[] data=JsonSerializer.SerializeToUtf8Bytes(value,Activation.Json),header=new byte[4];
        if(data.Length>16384)throw new IOException("size");
        BinaryPrimitives.WriteInt32LittleEndian(header,data.Length);
        await stream.WriteAsync(header,token);await stream.WriteAsync(data,token);await stream.FlushAsync(token);
    }
    public static async Task<Reply> Call(Request request)
    {
        using var timeout=new CancellationTokenSource(TimeSpan.FromSeconds(35));
        using var pipe=new NamedPipeClientStream(".",Pipe,PipeDirection.InOut,PipeOptions.Asynchronous,
            System.Security.Principal.TokenImpersonationLevel.Impersonation);
        await pipe.ConnectAsync(timeout.Token);
        Native.VerifyPipeServer(pipe.SafePipeHandle);
        await Write(pipe,request,timeout.Token);return await Read<Reply>(pipe,timeout.Token);
    }
}
