package telemost

type ConnectionFailure struct {
	Step   string
	Code   string
	Status int
	cause  error
}

func (failure *ConnectionFailure) Error() string { return "telemost connection failed" }
func (failure *ConnectionFailure) Unwrap() error { return failure.cause }

func connectionFailure(step, code string, status int, cause error) error {
	return &ConnectionFailure{Step: step, Code: code, Status: status, cause: cause}
}
