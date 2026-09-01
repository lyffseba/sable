cmake_minimum_required(VERSION 3.17)
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
set_target_properties(sable_cv PROPERTIES POSITION_INDEPENDENT_CODE ON)

if (APPLE)
	target_sources(sable_cv PRIVATE src/capture_avf.mm)
	set_source_files_properties(src/capture_avf.mm PROPERTIES
		LANGUAGE OBJCXX
		COMPILE_FLAGS "-fobjc-arc"
	)
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
#   cmake -DSABLE_GODOT_CPP=/path/to/godot-cpp -DGODOTCPP_API_VERSION=4.7 ...
# godot-cpp lives outside this repo. Do not vendor it.
if (DEFINED SABLE_GODOT_CPP AND NOT SABLE_GODOT_CPP STREQUAL "" AND EXISTS "${SABLE_GODOT_CPP}/CMakeLists.txt")
	get_filename_component(SABLE_GODOT_CPP "${SABLE_GODOT_CPP}" ABSOLUTE)

	if (NOT CMAKE_BUILD_TYPE)
		set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
	endif()

	if (CMAKE_BUILD_TYPE STREQUAL "Release" OR CMAKE_BUILD_TYPE STREQUAL "MinSizeRel")
		set(SABLE_GDE_CONFIG "release")
		if (NOT GODOTCPP_TARGET)
			set(GODOTCPP_TARGET "template_release" CACHE STRING "godot-cpp target")
		endif()
	else()
		set(SABLE_GDE_CONFIG "debug")
		if (NOT GODOTCPP_TARGET)
			set(GODOTCPP_TARGET "template_debug" CACHE STRING "godot-cpp target")
		endif()
	endif()

	if (NOT GODOTCPP_API_VERSION AND NOT GODOTCPP_CUSTOM_API_FILE)
		set(GODOTCPP_API_VERSION "4.7" CACHE STRING "Godot API version")
	endif()

	add_subdirectory("${SABLE_GODOT_CPP}" "${CMAKE_BINARY_DIR}/godot-cpp" EXCLUDE_FROM_ALL)

	add_library(cv_input SHARED src/register_types.cpp)
	target_link_libraries(cv_input PRIVATE sable_cv godot-cpp)
	target_compile_definitions(cv_input PRIVATE SABLE_WITH_GODOT_CPP)
	if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
		target_compile_options(cv_input PRIVATE -Wall -Wextra -Wpedantic)
	endif()

	if (APPLE)
		set(SABLE_GDE_OUTPUT "cv_input.macos.${SABLE_GDE_CONFIG}")
	elseif (WIN32)
		set(SABLE_GDE_OUTPUT "cv_input.windows.${SABLE_GDE_CONFIG}.x86_64")
	else()
		set(SABLE_GDE_OUTPUT "cv_input.linux.${SABLE_GDE_CONFIG}.x86_64")
	endif()

	set(SABLE_GDE_BIN "${CMAKE_CURRENT_SOURCE_DIR}/bin")
	file(MAKE_DIRECTORY "${SABLE_GDE_BIN}")

	set_target_properties(cv_input PROPERTIES
		CXX_STANDARD 17
		CXX_EXTENSIONS OFF
		POSITION_INDEPENDENT_CODE ON
		CXX_VISIBILITY_PRESET hidden
		VISIBILITY_INLINES_HIDDEN ON
		PREFIX "lib"
		OUTPUT_NAME "${SABLE_GDE_OUTPUT}"
		LIBRARY_OUTPUT_DIRECTORY "${SABLE_GDE_BIN}"
		RUNTIME_OUTPUT_DIRECTORY "${SABLE_GDE_BIN}"
		ARCHIVE_OUTPUT_DIRECTORY "${SABLE_GDE_BIN}"
	)
	if (APPLE)
		set_target_properties(cv_input PROPERTIES SUFFIX ".dylib")
	endif()
	if (WIN32)
		set_target_properties(cv_input PROPERTIES PREFIX "")
	endif()
endif()
