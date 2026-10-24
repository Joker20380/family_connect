package desktopmesh

import (
	"bytes"
	"encoding/json"
	"io"
	"unicode/utf8"
)

func strictReadinessJSON(raw []byte, limit int, target any) error {
	if len(raw) == 0 || len(raw) > limit || !utf8.Valid(raw) {
		return ReadinessInvalid
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if readinessValue(decoder, 0) != nil || decoder.Decode(new(any)) != io.EOF {
		return ReadinessInvalid
	}
	decoder = json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	decoder.DisallowUnknownFields()
	if decoder.Decode(target) != nil || decoder.Decode(new(any)) != io.EOF {
		return ReadinessInvalid
	}
	return nil
}

func readinessValue(decoder *json.Decoder, depth int) error {
	if depth > 16 {
		return ReadinessInvalid
	}
	token, err := decoder.Token()
	if err != nil {
		return ReadinessInvalid
	}
	switch token {
	case json.Delim('{'):
		seen := make(map[string]bool)
		for decoder.More() {
			key, err := decoder.Token()
			name, valid := key.(string)
			if err != nil || !valid || seen[name] {
				return ReadinessInvalid
			}
			seen[name] = true
			if readinessValue(decoder, depth+1) != nil {
				return ReadinessInvalid
			}
		}
		ending, err := decoder.Token()
		if err != nil || ending != json.Delim('}') {
			return ReadinessInvalid
		}
	case json.Delim('['):
		for decoder.More() {
			if readinessValue(decoder, depth+1) != nil {
				return ReadinessInvalid
			}
		}
		ending, err := decoder.Token()
		if err != nil || ending != json.Delim(']') {
			return ReadinessInvalid
		}
	case json.Delim('}'), json.Delim(']'):
		return ReadinessInvalid
	}
	return nil
}
