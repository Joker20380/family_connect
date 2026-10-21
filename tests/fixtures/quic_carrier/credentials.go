package labquic

import (
 "crypto/ed25519"
 "crypto/rand"
 "crypto/x509"
 "crypto/x509/pkix"
 "encoding/json"
 "encoding/pem"
 "math/big"
 "time"
)

func EphemeralCredentials() ([2][]byte,error) {
 var result [2][]byte
 public,private,err:=ed25519.GenerateKey(rand.Reader);if err!=nil{return result,err}
 now:=time.Now();root:=&x509.Certificate{SerialNumber:big.NewInt(1),Subject:pkix.Name{CommonName:"Family QUIC isolated test CA"},NotBefore:now.Add(-time.Minute),NotAfter:now.Add(time.Hour),IsCA:true,BasicConstraintsValid:true,KeyUsage:x509.KeyUsageCertSign|x509.KeyUsageDigitalSignature}
 rootDER,err:=x509.CreateCertificate(rand.Reader,root,root,public,private);if err!=nil{return result,err}
 authority:=string(pem.EncodeToMemory(&pem.Block{Type:"CERTIFICATE",Bytes:rootDER}))
 for index,name:=range []string{"quic-client.lab.invalid","quic-server.lab.invalid"}{
  public,key,err:=ed25519.GenerateKey(rand.Reader);if err!=nil{return result,err}
  leaf:=&x509.Certificate{SerialNumber:big.NewInt(int64(index+2)),Subject:pkix.Name{CommonName:name},DNSNames:[]string{name},NotBefore:now.Add(-time.Minute),NotAfter:now.Add(time.Hour),KeyUsage:x509.KeyUsageDigitalSignature,ExtKeyUsage:[]x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth,x509.ExtKeyUsageServerAuth}}
  certificate,err:=x509.CreateCertificate(rand.Reader,leaf,root,public,private);if err!=nil{return result,err};encoded,err:=x509.MarshalPKCS8PrivateKey(key);if err!=nil{return result,err}
  result[index],err=json.Marshal(Credentials{Authority:authority,Certificate:string(pem.EncodeToMemory(&pem.Block{Type:"CERTIFICATE",Bytes:certificate})),PrivateKey:string(pem.EncodeToMemory(&pem.Block{Type:"PRIVATE KEY",Bytes:encoded}))});if err!=nil{return result,err}
 }
 return result,nil
}
