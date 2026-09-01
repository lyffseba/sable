#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cmake -S "$ROOT/native/cv_input" -B "$ROOT/native/cv_input/build" -DCMAKE_CXX_COMPILER="${CXX:-g++}"
cmake --build "$ROOT/native/cv_input/build"
"$ROOT/native/cv_input/build/sable_cv_tests"
