cmake_minimum_required(VERSION 3.20)

project(
  byteweave
  LANGUAGES CXX
  VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ----------------------------------------------------------------------------
# Options (kept minimal)
# ----------------------------------------------------------------------------
option(BYTEWEAVE_BUILD_LIBRARY "Build the byteweave library target" ON)
option(BYTEWEAVE_BUILD_SHARED "If building the library, build it as SHARED instead of STATIC" OFF)
option(BYTEWEAVE_BUILD_SINGLE_HEADER "Generate the amalgamated single-header target" ON)
option(BYTEWEAVE_BUILD_EXAMPLES "Build example programs (whichever artifacts exist)" OFF)
option(BYTEWEAVE_WARNINGS "Enable common warning flags" ON)
option(BYTEWEAVE_WERROR "Treat warnings as errors" OFF)
option(BYTEWEAVE_WARNINGS_STRICT "Enable extra-strict warnings (conversion, shadow, etc.)" OFF)

# If the user disables both library and single-header, there will be nothing to build.
# We allow it (configure-only) but print a friendly warning.
if(NOT BYTEWEAVE_BUILD_LIBRARY AND NOT BYTEWEAVE_BUILD_SINGLE_HEADER)
  message(
    WARNING
      "Both BYTEWEAVE_BUILD_LIBRARY and BYTEWEAVE_BUILD_SINGLE_HEADER are OFF; no build artifacts will be produced."
  )
endif()

# ----------------------------------------------------------------------------
# Python
# ----------------------------------------------------------------------------

find_package(
  Python3
  COMPONENTS Interpreter
  QUIET)
if(NOT Python3_Interpreter_FOUND)
  set(PYTHON_FOR_TOOLS python3)
else()
  set(PYTHON_FOR_TOOLS ${Python3_EXECUTABLE})
endif()

add_custom_target(
  format
  COMMAND ${PYTHON_FOR_TOOLS} ${CMAKE_SOURCE_DIR}/tools/format.py
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

add_custom_target(
  format-check
  COMMAND ${PYTHON_FOR_TOOLS} ${CMAKE_SOURCE_DIR}/tools/format.py --check
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

if(CMAKE_EXPORT_COMPILE_COMMANDS)
  add_custom_target(
    tidy
    COMMAND ${PYTHON_FOR_TOOLS} ${CMAKE_SOURCE_DIR}/tools/tidy.py --p ${CMAKE_BINARY_DIR}
            --warnings-as-errors
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
else()
  message(STATUS "Enable CMAKE_EXPORT_COMPILE_COMMANDS=ON to use 'tidy' target")
endif()

# ----------------------------------------------------------------------------
# Compile Commands toggles
# ----------------------------------------------------------------------------
option(BYTEWEAVE_EXPORT_COMPILE_COMMANDS "Generate compile_commands.json in build dir" ON)
option(BYTEWEAVE_COPY_COMPILE_COMMANDS "Copy compile_commands.json to project root" OFF)

if(BYTEWEAVE_EXPORT_COMPILE_COMMANDS)
  set(CMAKE_EXPORT_COMPILE_COMMANDS
      ON
      CACHE BOOL "Export compile commands" FORCE)
else()
  set(CMAKE_EXPORT_COMPILE_COMMANDS
      OFF
      CACHE BOOL "Export compile commands" FORCE)
endif()

if(BYTEWEAVE_COPY_COMPILE_COMMANDS)
  add_custom_target(
    copy_compile_commands ALL
    COMMAND
      ${CMAKE_COMMAND} -D SRC=${CMAKE_BINARY_DIR}/compile_commands.json -D
      DST=${CMAKE_SOURCE_DIR}/compile_commands.json -P
      ${CMAKE_CURRENT_SOURCE_DIR}/cmake/copy_compile_commands.cmake
    COMMENT "Copy compile_commands.json to project root"
    VERBATIM)
endif()

# ----------------------------------------------------------------------------
# Generated headers (version/config)
# ----------------------------------------------------------------------------
# Ensure the configured output directory exists across generators/CMake versions.
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/generated/byteweave)

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/include/byteweave/version.hpp.in
               ${CMAKE_CURRENT_BINARY_DIR}/generated/byteweave/version.hpp @ONLY)

set(BYTEWEAVE_GEN_HEADERS ${CMAKE_CURRENT_BINARY_DIR}/generated/byteweave/version.hpp)

# ----------------------------------------------------------------------------
# Library target (optional)
# ----------------------------------------------------------------------------
if(BYTEWEAVE_BUILD_LIBRARY)
  set(_lib_type STATIC)
  if(BYTEWEAVE_BUILD_SHARED)
    set(_lib_type SHARED)
  endif()

  add_library(byteweave ${_lib_type} src/base64.cpp src/hex.cpp src/varint.cpp)

  # Provide a namespaced alias for consumers/exports.
  add_library(byteweave::byteweave ALIAS byteweave)

  # Propagate the existing build-mode to headers/consumers (no new boolean).
  target_compile_definitions(byteweave
                             PUBLIC BYTEWEAVE_BUILD_SHARED=$<BOOL:${BYTEWEAVE_BUILD_SHARED}>)

  # Prefer CURRENT dirs so the project is embeddable via add_subdirectory()
  target_include_directories(byteweave PUBLIC ${CMAKE_CURRENT_BINARY_DIR}/generated
                                              ${CMAKE_CURRENT_SOURCE_DIR}/include)

  target_compile_features(byteweave PUBLIC cxx_std_20)
  target_compile_definitions(byteweave PUBLIC BYTEWEAVE_HEADER_ONLY=0)

  if(BYTEWEAVE_WARNINGS)
    if(MSVC)
      target_compile_options(byteweave PRIVATE /W4)
      if(BYTEWEAVE_WARNINGS_STRICT)
        # Promote a few common diagnostics to level-4 warnings; keep it reasonable.
        target_compile_options(
          byteweave
          PRIVATE
            /permissive- # Stricter conformance mode
            /Zc:__cplusplus # Correct __cplusplus
            /w14242 # 'identifier': conversion, possible loss of data
            /w14254 # 'operator': conversion from 'type1' to 'type2', possible loss of data
            /w14263 # 'function': member function does not override any base class virtual member function
            /w14265 # class has virtual functions, but destructor is not virtual
            /w14287 # unsigned/negative mismatch
        )
      endif()
    else()
      # GCC/Clang baseline
      target_compile_options(byteweave PRIVATE -Wall -Wextra -Wpedantic)
      if(BYTEWEAVE_WARNINGS_STRICT)
        target_compile_options(byteweave PRIVATE -Wconversion -Wsign-conversion -Wshadow)
      endif()
    endif()
  endif()

  if(BYTEWEAVE_WERROR)
    if(MSVC)
      target_compile_options(byteweave PRIVATE /WX)
    else()
      target_compile_options(byteweave PRIVATE -Werror)
    endif()
  endif()

  if(BYTEWEAVE_BUILD_SHARED)
    # Ensure correct dllexport when building the DLL on Windows.
    target_compile_definitions(byteweave PRIVATE BW_BUILDING_DLL=1)
  endif()

  # Visibility: keep symbols lean by default.
  if(NOT MSVC)
    set_target_properties(byteweave PROPERTIES CXX_VISIBILITY_PRESET hidden
                                               VISIBILITY_INLINES_HIDDEN YES)
  endif()

  # Recommended for static->shared consumption on ELF platforms.
  set_target_properties(byteweave PROPERTIES POSITION_INDEPENDENT_CODE ON)
endif()

# ----------------------------------------------------------------------------
# Single-header generation (optional; independent of library)
# ----------------------------------------------------------------------------
if(BYTEWEAVE_BUILD_SINGLE_HEADER)
  # Allow overriding where the single header is written (defaults to the build dir).
  set(BYTEWEAVE_SINGLE_HEADER_OUTDIR
      "${CMAKE_CURRENT_BINARY_DIR}"
      CACHE PATH "Output directory for the single-header artifact")

  # Gather headers as dependencies so the amalgamated file rebuilds when they change.
  # GLOB is fine here because we only use it for dependencies; CONFIGURE_DEPENDS
  # makes CMake re-run if headers are added/removed.
  file(GLOB_RECURSE BYTEWEAVE_PUBLIC_HEADERS CONFIGURE_DEPENDS
       "${CMAKE_CURRENT_SOURCE_DIR}/include/byteweave/*.hpp"
       "${CMAKE_CURRENT_SOURCE_DIR}/include/byteweave/detail/*.inl")

  set(BYTEWEAVE_SINGLE_HEADER
      "${BYTEWEAVE_SINGLE_HEADER_OUTDIR}/byteweave-${PROJECT_VERSION}.single.hpp")

  add_custom_command(
    OUTPUT ${BYTEWEAVE_SINGLE_HEADER}
    COMMAND
      ${PYTHON_FOR_TOOLS} ${CMAKE_CURRENT_SOURCE_DIR}/tools/amalgamate.py --entry
      ${CMAKE_CURRENT_SOURCE_DIR}/include/byteweave/byteweave.hpp --out ${BYTEWEAVE_SINGLE_HEADER}
      --version ${PROJECT_VERSION} --generated ${CMAKE_CURRENT_BINARY_DIR}/generated
    DEPENDS ${BYTEWEAVE_PUBLIC_HEADERS} ${BYTEWEAVE_GEN_HEADERS}
            ${CMAKE_CURRENT_SOURCE_DIR}/tools/amalgamate.py
    COMMENT "Generating single-header amalgamation -> ${BYTEWEAVE_SINGLE_HEADER}"
    VERBATIM)

  add_custom_target(single_header DEPENDS ${BYTEWEAVE_SINGLE_HEADER})
endif()

# ----------------------------------------------------------------------------
# Examples (optional; will build the ones that are possible)
# ----------------------------------------------------------------------------
if(BYTEWEAVE_BUILD_EXAMPLES)
  set(_examples_built FALSE)

  if(TARGET byteweave)
    add_executable(example_lib examples/minimal.cpp)
    target_link_libraries(example_lib PRIVATE byteweave)
    set(_examples_built TRUE)
  endif()

  if(TARGET single_header)
    add_executable(example_single examples/minimal.cpp)
    add_dependencies(example_single single_header)
    target_compile_definitions(
      example_single PRIVATE BYTEWEAVE_USE_SINGLE_HEADER=1
                             BYTEWEAVE_SINGLE_HEADER="${BYTEWEAVE_SINGLE_HEADER}")
    set(_examples_built TRUE)
  endif()

  if(NOT _examples_built)
    message(
      FATAL_ERROR
        "BYTEWEAVE_BUILD_EXAMPLES=ON, but neither the library nor single-header is enabled. Enable BYTEWEAVE_BUILD_LIBRARY or BYTEWEAVE_BUILD_SINGLE_HEADER."
    )
  endif()
endif()

# ----------------------------------------------------------------------------
# Tests (optional)
# ----------------------------------------------------------------------------
option(BYTEWEAVE_BUILD_TESTS "Build and run minimal tests via CTest" ON)

if(BYTEWEAVE_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()

# ----------------------------------------------------------------------------
# Install rules (headers-only + single-header) and CMake package config
# ----------------------------------------------------------------------------
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

# Install public headers
install(DIRECTORY "${PROJECT_SOURCE_DIR}/include/byteweave"
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")

# Install generated version header
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/generated/byteweave/version.hpp"
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/byteweave")

# Install the single-header artifact (versioned filename)
if(BYTEWEAVE_BUILD_SINGLE_HEADER)
  install(FILES "${BYTEWEAVE_SINGLE_HEADER}" DESTINATION "${CMAKE_INSTALL_DATADIR}/byteweave")
endif()
# Package config: byteweaveConfig.cmake and version file
set(_BW_CMAKE_DIR "${CMAKE_INSTALL_LIBDIR}/cmake/byteweave")
write_basic_package_version_file(
  "${PROJECT_BINARY_DIR}/byteweaveConfigVersion.cmake"
  VERSION "${PROJECT_VERSION}"
  COMPATIBILITY SameMajorVersion)

# Use a relocatable, package-aware config so PACKAGE_PREFIX_DIR is set correctly
set(BYTEWEAVE_INCLUDE_INSTALL_DIR "${CMAKE_INSTALL_INCLUDEDIR}")
set(BYTEWEAVE_SHARE_INSTALL_DIR "${CMAKE_INSTALL_DATADIR}/byteweave")

configure_package_config_file(
  "${PROJECT_SOURCE_DIR}/cmake/byteweaveConfig.cmake.in"
  "${PROJECT_BINARY_DIR}/byteweaveConfig.cmake"
  INSTALL_DESTINATION "${_BW_CMAKE_DIR}"
  PATH_VARS BYTEWEAVE_INCLUDE_INSTALL_DIR BYTEWEAVE_SHARE_INSTALL_DIR)

install(FILES "${PROJECT_BINARY_DIR}/byteweaveConfig.cmake"
              "${PROJECT_BINARY_DIR}/byteweaveConfigVersion.cmake" DESTINATION "${_BW_CMAKE_DIR}")
# Optionally include license/readme if present
if(EXISTS "${PROJECT_SOURCE_DIR}/LICENSE")
  install(FILES "${PROJECT_SOURCE_DIR}/LICENSE" DESTINATION "${CMAKE_INSTALL_DATADIR}/byteweave")
endif()
if(EXISTS "${PROJECT_SOURCE_DIR}/README.md")
  install(FILES "${PROJECT_SOURCE_DIR}/README.md" DESTINATION "${CMAKE_INSTALL_DATADIR}/byteweave")
endif()

# ----------------------------------------------------------------------------
# CPack (archives from install rules)
# ----------------------------------------------------------------------------
set(CPACK_PACKAGE_NAME "byteweave")
set(CPACK_PACKAGE_VENDOR "Byteweave")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_CONTACT "maintainers@byteweave.invalid")
set(CPACK_GENERATOR "TGZ;ZIP")
include(CPack)

# ----------------------------------------------------------------------------
# Friendly status summary
# ----------------------------------------------------------------------------
message(STATUS "Byteweave configuration:")
message(STATUS "  BYTEWEAVE_BUILD_LIBRARY        = ${BYTEWEAVE_BUILD_LIBRARY}")
message(STATUS "  BYTEWEAVE_BUILD_SHARED         = ${BYTEWEAVE_BUILD_SHARED}")
message(STATUS "  BYTEWEAVE_BUILD_SINGLE_HEADER  = ${BYTEWEAVE_BUILD_SINGLE_HEADER}")
message(STATUS "  BYTEWEAVE_SINGLE_HEADER_OUTDIR = ${BYTEWEAVE_SINGLE_HEADER_OUTDIR}")
message(STATUS "  BYTEWEAVE_BUILD_EXAMPLES       = ${BYTEWEAVE_BUILD_EXAMPLES}")
message(STATUS "  BYTEWEAVE_WARNINGS             = ${BYTEWEAVE_WARNINGS}")
message(STATUS "  BYTEWEAVE_WERROR               = ${BYTEWEAVE_WERROR}")
message(STATUS "  BYTEWEAVE_WARNINGS_STRICT      = ${BYTEWEAVE_WARNINGS_STRICT}")
