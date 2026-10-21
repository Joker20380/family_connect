package telemost

func labMediaRate(size, header int) {
 labRate.Lock()
 defer labRate.Unlock()
 now:=time.Now()
 if !labCeilingOriginal {
  floor:=now.Add(-2*time.Millisecond)
  if labRate.next.Before(floor){labRate.next=floor}
  labRate.next=labRate.next.Add(time.Duration(size)*time.Second/1048576)
  if delay:=time.Until(labRate.next);delay>0{started:=time.Now();time.Sleep(delay);labRate.WaitNS+=uint64(time.Since(started))}
 }
 labRate.Bytes+=uint64(size)
 labRate.MaxPacket=max(labRate.MaxPacket,size-64)
 labRate.MaxHeader=max(labRate.MaxHeader,header)
}
