package telemost

import (
	"encoding/json"

	"github.com/pion/webrtc/v4"
)

func (session *Session) PerformanceSnapshot() map[string]any {
	result := map[string]any{"send_queue_frames": len(session.sendQueue), "send_queue_capacity": cap(session.sendQueue), "receive_queue_messages": len(session.recvQueue), "carrier": session.Stats()}
	for name, connection := range map[string]*webrtc.PeerConnection{"publisher": session.pcPub.Load(), "subscriber": session.pcSub.Load()} {
		if connection == nil {
			continue
		}
		rows := []map[string]any{}
		for _, statistic := range connection.GetStats() {
			raw, err := json.Marshal(statistic)
			if err != nil {
				continue
			}
			var fields map[string]any
			if json.Unmarshal(raw, &fields) != nil {
				continue
			}
			if fields["type"] == "candidate-pair" && fields["nominated"] != true {
				continue
			}
			switch fields["type"] {
			case "inbound-rtp", "outbound-rtp", "remote-inbound-rtp", "remote-outbound-rtp", "candidate-pair", "transport", "peer-connection":
			default:
				continue
			}
			row := map[string]any{"type": fields["type"]}
			for key, value := range fields {
				switch value.(type) {
				case float64, bool:
					row[key] = value
				}
			}
			rows = append(rows, row)
		}
		result[name] = rows
	}
	return result
}
