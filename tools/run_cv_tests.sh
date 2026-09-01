#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$(uname -s)" = "Darwin" ]; then
	CXX="${CXX:-clang++}"
else
	CXX="${CXX:-g++}"
fi
cmake -S "$ROOT/native/cv_input" -B "$ROOT/native/cv_input/build" -DCMAKE_CXX_COMPILER="$CXX"
cmake --build "$ROOT/native/cv_input/build"
"$ROOT/native/cv_input/build/sable_cv_tests"
