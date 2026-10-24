package roombroker

import (
    "crypto/sha256"
    "encoding/hex"
    "os"
    "path/filepath"
    "strings"
    "testing"

    "github.com/Joker20380/family_connect/carrier/sessionprofile"
)

func groupTarget(identity Identity) string {
    digest := sha256.Sum256(identity.PublicKey[:])
    return hex.EncodeToString(digest[:16])
}

func groupFixture(test *testing.T) (string, []Identity, func(string, string)) {
    test.Helper()
    directory := test.TempDir()
    if err := os.Chmod(directory, 0700); err != nil { test.Fatal(err) }
    test.Setenv("FC_DIAGNOSTIC_CONTROL_DIR", directory)
    identities := make([]Identity, 4)
    for index := range identities { identities[index].PublicKey[0] = byte(index + 1) }
    put := func(name, value string) {
        test.Helper()
        if err := os.WriteFile(filepath.Join(directory, name), []byte(value), 0600); err != nil { test.Fatal(err) }
    }
    put("speed-target", groupTarget(identities[0]))
    put("speed-profile", "P1")
    put("rtp-pacing", "OFF")
    return directory, identities, put
}

func TestSpeedGroupExactThreeAndSeparateDiagnostics(test *testing.T) {
    directory, identities, put := groupFixture(test)
    group := strings.Join([]string{groupTarget(identities[0]), groupTarget(identities[1]), groupTarget(identities[2])}, "\n")
    put("speed-targets", group+"\n")
    for index, identity := range identities {
        expected := sessionprofile.P1
        if index == 3 { expected = sessionprofile.P0 }
        actual, err := speedPolicy(identity)
        if err != nil || actual != expected { test.Fatal(index, actual, err) }
        if lifecyclePolicy(identity) != (index == 0) { test.Fatal("diagnostic scope expanded", index) }
    }
    put("speed-profile", "P0")
    for _, identity := range identities {
        actual, err := speedPolicy(identity)
        if err != nil || actual != sessionprofile.P0 { test.Fatal(actual, err) }
    }
    put("speed-profile", "P1")
    if err := os.Remove(filepath.Join(directory, "speed-targets")); err != nil { test.Fatal(err) }
    actual, err := speedPolicy(identities[1])
    if err != nil || actual != sessionprofile.P0 { test.Fatal("single-owner fallback changed", actual, err) }
}

func TestSpeedGroupInvalidFailsClosed(test *testing.T) {
    _, identities, put := groupFixture(test)
    owner, tester, other := groupTarget(identities[0]), groupTarget(identities[1]), groupTarget(identities[2])
    cases := map[string]string{
        "wildcard": "*", "bad_hex": owner+"\n"+strings.Repeat("z",32),
        "duplicate": owner+"\n"+owner, "missing_owner": tester+"\n"+other,
        "uppercase": strings.ToUpper(owner), "blank_row": owner+"\n\n"+tester,
        "four_members": strings.Join([]string{owner,tester,other,groupTarget(identities[3])},"\n"),
        "oversize": strings.Repeat("a",100), "comma_list": owner+","+tester,
    }
    for name, value := range cases {
        test.Run(name,func(test *testing.T) {
            put("speed-targets", value)
            for _, identity := range identities {
                actual, err := speedPolicy(identity)
                if err == nil || actual != sessionprofile.P0 { test.Fatal("invalid group accepted", actual, err) }
            }
        })
    }
    put("speed-targets", owner+"\n"+tester)
    put("speed-profile", "P2")
    if _, err := speedPolicy(identities[1]); err == nil { test.Fatal("group enabled experimental P2") }
    put("speed-profile", "P1")
    put("rtp-pacing", "FIXED4M")
    if _, err := speedPolicy(identities[1]); err == nil { test.Fatal("group enabled pacing") }
}

func TestSpeedGroupFileProtection(test *testing.T) {
    directory, identities, put := groupFixture(test)
    group := groupTarget(identities[0])+"\n"+groupTarget(identities[1])
    path := filepath.Join(directory,"speed-targets")
    put("speed-targets",group)
    if _,err := muxOperatorValue("speed-targets"); err == nil { test.Fatal("default 32-byte bound changed") }
    if err := os.Chmod(path,0644); err != nil { test.Fatal(err) }
    if _,err := speedPolicy(identities[1]); err == nil { test.Fatal("unsafe mode accepted") }
    if err := os.Remove(path); err != nil { test.Fatal(err) }
    put("group-source",group)
    if err := os.Symlink(filepath.Join(directory,"group-source"),path); err != nil { test.Fatal(err) }
    if _,err := speedPolicy(identities[1]); err == nil { test.Fatal("symlink accepted") }
    if err := os.Remove(path); err != nil { test.Fatal(err) }
    if err := os.Mkdir(path,0700); err != nil { test.Fatal(err) }
    if _,err := speedPolicy(identities[1]); err == nil { test.Fatal("directory accepted") }
    if err := os.Remove(path); err != nil { test.Fatal(err) }
    put("speed-targets",group)
    if err := os.Chmod(directory,0755); err != nil { test.Fatal(err) }
    if _,err := speedPolicy(identities[1]); err == nil { test.Fatal("unsafe parent accepted") }
}
