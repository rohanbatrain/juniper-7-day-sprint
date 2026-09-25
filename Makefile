# Juniper 7-Day Sprint — thin wrapper over ops/lab.sh
# Override the topology with: make up TOPOLOGY=lab/topologies/day-02-switching.toml
TOPOLOGY ?= lab/topologies/day-01-routing.toml
NODE     ?= r1

.PHONY: help up down status console ssh snapshot restore destroy net-up net-down lint generate

help:
	@ops/lab.sh help

up:            ; ops/lab.sh up $(TOPOLOGY)
down:          ; ops/lab.sh down $(TOPOLOGY)
status:        ; ops/lab.sh status $(TOPOLOGY)
console:       ; ops/lab.sh console $(NODE)
ssh:           ; ops/lab.sh ssh $(NODE)
snapshot:      ; ops/lab.sh snapshot $(NODE) $(NAME)
restore:       ; ops/lab.sh restore $(NODE) $(NAME)
destroy:       ; ops/lab.sh destroy $(TOPOLOGY)
net-up:        ; ops/lab.sh net-up $(TOPOLOGY)
net-down:      ; ops/lab.sh net-down $(TOPOLOGY)
generate:      ; ops/lab.sh generate $(TOPOLOGY)
lint:          ; ops/lab.sh lint
