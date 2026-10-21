"""Observations only: keep every existing protocol-error counter and action."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests/fixtures/speed_candidate'))
from prepare import write,replace

SOURCE=ROOT/'state-client-build/support-automation-20261021/android-source/carrier'


def main():
    path=SOURCE/'tcpforward/mux.go'
    replace(path,'type MuxStats struct {','''type ProtocolErrorCounts struct {
    OpenReplay uint64 `json:"open_replay"`
    UnknownStream uint64 `json:"unknown_stream"`
    OpenState uint64 `json:"open_state"`
    DataState uint64 `json:"data_state"`
    CreditState uint64 `json:"credit_state"`
    FINState uint64 `json:"fin_state"`
    CloseState uint64 `json:"close_state"`
    FrameKind uint64 `json:"frame_kind"`
    DNSReplay uint64 `json:"dns_replay"`
    DNSRole uint64 `json:"dns_role"`
    DNSUnmatched uint64 `json:"dns_unmatched"`
}

func (mux *Mux) protocolErrorLocked(counter *uint64) {
    mux.stats.ProtocolErrors++
    *counter++
}

type MuxStats struct {
    ProtocolErrorReasons ProtocolErrorCounts''')
    replace(path,'if frame.id <= mux.lastID {\n\t\t\tmux.stats.ProtocolErrors++','if frame.id <= mux.lastID {\n\t\t\tmux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.OpenReplay)')
    replace(path,'if stream == nil {\n\t\tmux.stats.ProtocolErrors++','if stream == nil {\n\t\tmux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.UnknownStream)')
    replace(path,'\tinvalid := false\n\tswitch frame.kind {','\tinvalid := false\n\treason := &mux.stats.ProtocolErrorReasons.FrameKind\n\tswitch frame.kind {')
    for kind,field in [('openOK','OpenState'),('openError','OpenState'),('dataFrame','DataState'),('muxWindowUpdate','CreditState'),('finFrame','FINState'),('closeFrame','CloseState')]:
        old='\tcase '+kind+':\n'
        replace(path,old,old+'\t\treason = &mux.stats.ProtocolErrorReasons.'+field+'\n')
    replace(path,'if invalid {\n\t\tmux.stats.ProtocolErrors++','if invalid {\n\t\tmux.protocolErrorLocked(reason)')
    path=SOURCE/'tcpforward/mux_dns.go'
    replace(path,'if id <= mux.dnsLast {\n\t\t\t\tmux.stats.ProtocolErrors++','if id <= mux.dnsLast {\n\t\t\t\tmux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.DNSReplay)')
    replace(path,'default:\n\t\t\tmux.stats.ProtocolErrors++','default:\n\t\t\tmux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.DNSRole)')
    replace(path,'if call == nil || call.done {\n\t\tmux.stats.ProtocolErrors++','if call == nil || call.done {\n\t\tmux.protocolErrorLocked(&mux.stats.ProtocolErrorReasons.DNSUnmatched)')
    path=SOURCE/'sessiondiag/report.go'
    replace(path,'type Report struct {','type Report struct {\n ProtocolErrorReasons tcpforward.ProtocolErrorCounts `json:"protocol_error_reasons"`')
    replace(path,'ProtocolErrors: mux.ProtocolErrors,','ProtocolErrorReasons: mux.ProtocolErrorReasons, ProtocolErrors: mux.ProtocolErrors,')
    test=Path(__file__).with_name('protocol_reasons_test.go')
    write(SOURCE/'tcpforward/protocol_reasons_test.go',test.read_text())


if __name__=='__main__':main()
