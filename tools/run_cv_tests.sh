#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/native/cv_input/build"
mkdir -p "$BUILD_DIR"

if command -v cmake >/dev/null 2>&1; then
  cmake -S "$ROOT/native/cv_input" -B "$BUILD_DIR" -DCMAKE_CXX_COMPILER="${CXX:-g++}"
  cmake --build "$BUILD_DIR"
else
  CXX_BIN="${CXX:-$(command -v clang++ || command -v g++)}"
  "$CXX_BIN" -std=c++17 -Wall -Wextra \
    -I "$ROOT/native/cv_input/include" \
    "$ROOT/native/cv_input/src/pipeline.cpp" \
    "$ROOT/native/cv_input/src/capture.cpp" \
    "$ROOT/native/cv_input/src/cv_input_c_api.cpp" \
    "$ROOT/native/cv_input/tests/test_aim.cpp" \
    -o "$BUILD_DIR/sable_cv_tests"
fi

"$BUILD_DIR/sable_cv_tests"
