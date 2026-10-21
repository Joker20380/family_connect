package main

import (
 "context"
 "os"
 "path/filepath"
 "time"
)

func labStartGate(ctx context.Context,path string,emit func(map[string]any)error)error {
 bounded,cancel:=context.WithTimeout(ctx,45*time.Second);defer cancel();started:=time.Now();ticker:=time.NewTicker(20*time.Millisecond);defer ticker.Stop()
 for {if _,err:=os.Stat(filepath.Join(filepath.Dir(path),"start.input"));err==nil{_ = emit(map[string]any{"event":"capacity_start_gate","seconds":time.Since(started).Seconds()});return nil};select{case <-bounded.Done():return bounded.Err();case <-ticker.C:}}
}
