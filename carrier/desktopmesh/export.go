package desktopmesh

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"strconv"
)

const ExportLimit = 262144
const ExportInputLimit = 4 * ExportLimit

var ErrExportSize = errors.New("diagnostic export exceeds bounded record")

func BoundedExport(raw []byte) ([]byte, error) {
	if len(raw) == 0 || len(raw) > ExportInputLimit {
		return nil, ErrExportSize
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var record map[string]any
	if decoder.Decode(&record) != nil || record == nil || decoder.Decode(new(any)) != io.EOF {
		return nil, ErrExportSize
	}
	if len(raw) <= ExportLimit {
		return bytes.Clone(raw), nil
	}
	if _, exists := record["record_budget"]; exists {
		return nil, ErrExportSize
	}
	omitted := make(map[string]int)
	record["record_budget"] = map[string]any{"limit_bytes": ExportLimit, "untrimmed_bytes": len(raw), "omitted_detail_items": omitted}
	encoded, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}
	encodedSize := len(encoded)
	trim := func(parent map[string]any, field, path string) {
		details, ok := parent[field].([]any)
		if !ok || encodedSize <= ExportLimit {
			return
		}
		removed := 0
		for len(details)-removed > 2 && encodedSize > ExportLimit {
			item, _ := json.Marshal(details[removed+1])
			before, _ := json.Marshal(omitted)
			omitted[path]++
			after, _ := json.Marshal(omitted)
			encodedSize += len(after) - len(before) - len(item) - 1
			removed++
		}
		if removed > 0 {
			retained := make([]any, 1, len(details)-removed)
			retained[0] = details[0]
			parent[field] = append(retained, details[removed+1:]...)
		}
	}
	session := func(value any, path string) {
		entry, _ := value.(map[string]any)
		lifecycle, _ := entry["lifecycle"].(map[string]any)
		trim(lifecycle, "trace", path+".lifecycle.trace")
		boundaries, _ := lifecycle["boundaries"].(map[string]any)
		trim(boundaries, "events", path+".lifecycle.boundaries.events")
		mux, _ := entry["mux_lifecycle"].(map[string]any)
		trim(mux, "events", path+".mux_lifecycle.events")
		trim(mux, "incidents", path+".mux_lifecycle.incidents")
	}
	history, _ := record["restricted_history"].([]any)
	for index, value := range history {
		session(value, "restricted_history["+strconv.Itoa(index)+"]")
	}
	session(record["restricted_session"], "restricted_session")
	trim(record, "events", "events")
	encoded, err = json.Marshal(record)
	if err != nil {
		return nil, err
	}
	if len(encoded) > ExportLimit {
		return nil, ErrExportSize
	}
	return encoded, nil
}
