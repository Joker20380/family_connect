package main

import (
 "context"
 "errors"
 "os"
 "path/filepath"
 "testing"
 "time"
)

func TestLabStartGate(test *testing.T){
 directory:=test.TempDir();path:=filepath.Join(directory,"capacity.json");ctx,cancel:=context.WithTimeout(context.Background(),30*time.Millisecond)
 if err:=labStartGate(ctx,path,func(map[string]any)error{return nil});!errors.Is(err,context.DeadlineExceeded){test.Fatal(err)};cancel()
 ctx,cancel=context.WithTimeout(context.Background(),time.Second);defer cancel();done:=make(chan error,1);go func(){done<-labStartGate(ctx,path,func(map[string]any)error{return nil})}()
 select{case <-done:test.Fatal("started before both-side controller gate");case <-time.After(30*time.Millisecond):}
 if err:=os.WriteFile(filepath.Join(directory,"start.input"),[]byte("both carriers connected"),0600);err!=nil{test.Fatal(err)}
 if err:=<-done;err!=nil{test.Fatal(err)}
}
