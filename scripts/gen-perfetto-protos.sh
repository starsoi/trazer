#!/bin/bash

PERFETTO_REPO_URL="https://github.com/google/perfetto.git"
PERFETTO_TRACE_PROTO_PATH="protos/perfetto/trace"
SCRIPT_DIR=$(dirname -- "$0")
TRAZER_PROTO_PATH="$SCRIPT_DIR/../protos"

tmpdir=$(mktemp -d)

# Clone the Perfetto repository from GitHub to a temporary folder
git clone $PERFETTO_REPO_URL $tmpdir

# Copy all trace-related protos to the project folder
cp -r $tmpdir/$PERFETTO_TRACE_PROTO_PATH $TRAZER_PROTO_PATH

# Remove all non-proto files
find $TRAZER_PROTO_PATH -not -iname "*.proto" -type f -delete

# Cleanup the temporary folder
rm -rf $tmpdir

