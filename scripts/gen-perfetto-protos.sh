#!/bin/bash

PERFETTO_REPO_URL="https://github.com/google/perfetto.git"
PERFETTO_TRACE_PROTO_PATH="protos/perfetto/trace"
SCRIPT_DIR=$(dirname -- "$0")
TRAZER_PROTO_PATH="$SCRIPT_DIR/../protos"

tmpdir=$(mktemp -d)

git clone $PERFETTO_REPO_URL $tmpdir
cp -r $tmpdir/$PERFETTO_TRACE_PROTO_PATH $TRAZER_PROTO_PATH
rm -rf $tmpdir

