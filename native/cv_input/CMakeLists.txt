cmake_minimum_required(VERSION 3.16)
project(sable_cv_input LANGUAGES CXX)
if (APPLE)
	enable_language(OBJCXX)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(sable_cv STATIC
	src/pipeline.cpp
	src/capture.cpp
	src/cv_input_c_api.cpp
)
target_include_directories(sable_cv PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
find_package(Threads REQUIRED)
target_link_libraries(sable_cv PUBLIC Threads::Threads)

if (APPLE)
	target_sources(sable_cv PRIVATE src/capture_avf.mm)
	set_source_files_properties(src/capture_avf.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")
	target_link_libraries(sable_cv PUBLIC
		"-framework Foundation"
		"-framework AVFoundation"
		"-framework CoreMedia"
		"-framework CoreVideo"
	)
endif()

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
	target_compile_options(sable_cv PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(sable_cv_tests tests/test_aim.cpp)
target_link_libraries(sable_cv_tests PRIVATE sable_cv)
if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
	target_compile_options(sable_cv_tests PRIVATE -Wall -Wextra -Wpedantic)
endif()

enable_testing()
add_test(NAME aim_pipeline COMMAND sable_cv_tests)

# Optional GDExtension shared library when godot-cpp is provided:
#   cmake -DSABLE_GODOT_CPP=/path/to/godot-cpp ...
if (DEFINED SABLE_GODOT_CPP AND EXISTS "${SABLE_GODOT_CPP}/include")
	add_library(cv_input SHARED src/register_types.cpp)
	target_link_libraries(cv_input PRIVATE sable_cv)
	target_include_directories(cv_input PRIVATE ${SABLE_GODOT_CPP}/include)
	target_compile_definitions(cv_input PRIVATE SABLE_WITH_GODOT_CPP)
endif()
