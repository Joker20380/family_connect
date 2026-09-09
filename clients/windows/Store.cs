using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Security;
namespace FamilyConnect;
internal static class Store
{
    public static string Root=>Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),"FamilyConnect");
    public static string TunnelPath=>Path.Combine(Root,"fc-native.conf.dpapi");
    public static string OwnerPath=>Path.Combine(Root,"owner");
    public static void SecureRoot()
    {
        var dir=Directory.CreateDirectory(Root);
        if((dir.Attributes&FileAttributes.ReparsePoint)!=0)throw new IOException("unsafe store");
        var acl=new DirectorySecurity();acl.SetAccessRuleProtection(true,false);
        foreach(var role in new[]{WellKnownSidType.LocalSystemSid,WellKnownSidType.BuiltinAdministratorsSid})
            acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(role,null),FileSystemRights.FullControl,
                InheritanceFlags.ContainerInherit|InheritanceFlags.ObjectInherit,PropagationFlags.None,AccessControlType.Allow));
        dir.SetAccessControl(acl);
    }
    public static string UserPath(string sid,string suffix)=>Path.Combine(Root,Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(sid)))+suffix);
    public static void Atomic(string path,byte[] bytes)
    {
        var temp=Path.Combine(Root,Guid.NewGuid().ToString("N")+".tmp");
        try{using(var file=new FileStream(temp,FileMode.CreateNew,FileAccess.Write,FileShare.None)){file.Write(bytes);file.Flush(true);}File.Move(temp,path,true);}
        finally{File.Delete(temp);}
    }
    public static byte[] Key(string sid)
    {
        string path=UserPath(sid,".key.dpapi");
        if(!File.Exists(path)){
            var key=new X25519PrivateKeyParameters(new SecureRandom()).GetEncoded();
            try{Atomic(path,ProtectedData.Protect(key,null,DataProtectionScope.CurrentUser));}
            finally{CryptographicOperations.ZeroMemory(key);}
        }
        return ProtectedData.Unprotect(File.ReadAllBytes(path),null,DataProtectionScope.CurrentUser);
    }
    public static string Public(string sid)
    {
        var key=Key(sid);try{return Convert.ToBase64String(new X25519PrivateKeyParameters(key,0).GeneratePublicKey().GetEncoded());}
        finally{CryptographicOperations.ZeroMemory(key);}
    }
    public static void Activate(string sid,string envelope)
    {
        string publicKey=Public(sid);
        var root=Convert.FromBase64String(File.ReadAllText(Path.Combine(AppContext.BaseDirectory,"activation.pub")).Trim());
        var grant=Activation.Verify(envelope,root,publicKey,DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        var key=Key(sid);
        try{Atomic(UserPath(sid,".conf.dpapi"),Native.EncryptTunnel(Encoding.UTF8.GetBytes(Activation.Config(grant,Convert.ToBase64String(key)))));}
        finally{CryptographicOperations.ZeroMemory(key);}
    }
}
