package roombroker

import (
    "crypto/sha256"
    "encoding/hex"
    "os"
    "path/filepath"
    "testing"
    "github.com/Joker20380/family_connect/carrier/sessionprofile"
)

func TestSpeedOwnerScopeAndP0Return(test *testing.T) {
    directory := test.TempDir()
    if err:=os.Chmod(directory,0700);err!=nil { test.Fatal(err) }
    test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR",directory)
    var owner, other Identity
    owner.PublicKey[0]=42;other.PublicKey[0]=43
    hash:=sha256.Sum256(owner.PublicKey[:])
    put:=func(name,value string) { test.Helper();if err:=os.WriteFile(filepath.Join(directory,name),[]byte(value),0600);err!=nil {test.Fatal(err)} }
    put("speed-target",hex.EncodeToString(hash[:16]));put("rtp-pacing","OFF")
    for _, mode:=range []string{"P0","P1","P2","P0"} {
        put("speed-profile",mode)
        expected,_:=sessionprofile.Parse(mode)
        actual,err:=speedPolicy(owner);if err!=nil || actual!=expected {test.Fatal(mode,actual,err)}
        actual,err=speedPolicy(other);if err!=nil || actual!=sessionprofile.P0 {test.Fatal("other user changed",actual,err)}
    }
    put("speed-profile","P2");put("rtp-pacing","FIXED4M")
    if _,err:=speedPolicy(owner);err==nil {test.Fatal("hidden pacing permitted")}
    put("rtp-pacing","OFF");put("speed-target","bad")
    if _,err:=speedPolicy(owner);err==nil {test.Fatal("unscoped profile permitted")}
    put("speed-profile","unknown")
    if _,err:=speedPolicy(owner);err==nil {test.Fatal("unknown accepted")}
}
