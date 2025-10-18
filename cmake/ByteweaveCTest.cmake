# Byteweave CTest helpers (shared by tests/ and examples/)

cmake_minimum_required(VERSION 3.20)
include_guard(GLOBAL)

# --- public link target resolution -------------------------------------------
# bw_public_link_target(OUT_VAR)
# Produces a target you can always link against:
# - If the real 'byteweave' library exists, returns an INTERFACE target 'byteweave_public'
#   that links to it (so PUBLIC deps/flags propagate).
# - Otherwise, creates 'byteweave_public' as an INTERFACE target with the header-only
#   includes/defines so clients can compile in header-only mode.
function(bw_public_link_target OUT_VAR)
  if(TARGET byteweave_public)
    set(${OUT_VAR}
        byteweave_public
        PARENT_SCOPE)
    return()
  endif()

  add_library(byteweave_public INTERFACE)

  if(TARGET byteweave)
    target_link_libraries(byteweave_public INTERFACE byteweave)
  else()
    target_compile_definitions(byteweave_public INTERFACE BYTEWEAVE_HEADER_ONLY=1)
    # Use SOURCE_DIR/BINARY_DIR from the top-level project that included this module
    if(DEFINED PROJECT_SOURCE_DIR AND DEFINED PROJECT_BINARY_DIR)
      target_include_directories(byteweave_public INTERFACE "${PROJECT_BINARY_DIR}/generated"
                                                            "${PROJECT_SOURCE_DIR}/include")
    endif()
    if(TARGET byteweave_san)
      target_link_libraries(byteweave_public INTERFACE byteweave_san)
    endif()
  endif()

  set(${OUT_VAR}
      byteweave_public
      PARENT_SCOPE)
endfunction()

# --- naming helper ------------------------------------------------------------
# bw_make_target_name(OUT_VAR PREFIX REL_DIR)
# e.g., PREFIX="ex-" REL_DIR="io/csv" -> "ex-io-csv"
function(bw_make_target_name OUT_VAR PREFIX REL_DIR)
  set(_name "${REL_DIR}")
  string(REPLACE "\\" "/" _name "${_name}")
  string(REPLACE "/" "-" _name "${_name}")
  string(REPLACE " " "-" _name "${_name}")
  string(TOLOWER "${_name}" _name)
  set(${OUT_VAR}
      "${PREFIX}${_name}"
      PARENT_SCOPE)
endfunction()

# --- rpaths for shared builds (macOS/Linux) -----------------------------------
# bw_runtime_paths(<target>)
function(bw_runtime_paths target)
  if(NOT TARGET "${target}")
    message(FATAL_ERROR "bw_runtime_paths: target '${target}' does not exist")
  endif()

  if(BYTEWEAVE_BUILD_SHARED)
    if(APPLE)
      set_target_properties("${target}" PROPERTIES BUILD_RPATH "@loader_path" INSTALL_RPATH
                                                                              "@loader_path")
    elseif(UNIX)
      set_target_properties(
        "${target}"
        PROPERTIES SKIP_BUILD_RPATH OFF
                   BUILD_RPATH "\$ORIGIN"
                   INSTALL_RPATH "\$ORIGIN")
    endif()
  endif()
endfunction()

# --- ctest registration --------------------------------------------------------
# bw_register_test(<target> <rel_dir> <labels>)
# <labels> may be a single label or a semicolon-separated list.
function(bw_register_test target rel_dir labels)
  if(NOT TARGET "${target}")
    message(FATAL_ERROR "bw_register_test: target '${target}' does not exist")
  endif()

  add_test(NAME "${target}" COMMAND $<TARGET_FILE:${target}>)

  set_tests_properties("${target}" PROPERTIES LABELS "${labels}" WORKING_DIRECTORY
                                              "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")

  if(WIN32
     AND BYTEWEAVE_BUILD_SHARED
     AND TARGET byteweave)
    set_tests_properties(
      "${target}" PROPERTIES ENVIRONMENT
                             "PATH=$<SHELL_PATH:$<TARGET_FILE_DIR:byteweave>>;$ENV{PATH}")
  endif()
endfunction()

# --- one-stop helper -----------------------------------------------------------
# bw_add_folder_entry(<rel_dir> <label> <prefix>)
# - Gathers all C/C++ sources in <rel_dir>
# - Creates an executable named from <prefix> + sanitized <rel_dir>
# - Links against a resolved public link target (library or header-only)
# - Sets friendly runtime paths (macOS/Linux)
# - Sets VS working directory and registers as a CTest with <label>
function(bw_add_folder_entry rel_dir label prefix)
  # Collect sources under this folder
  file(
    GLOB
    _srces
    CONFIGURE_DEPENDS
    "${rel_dir}/*.c"
    "${rel_dir}/*.cc"
    "${rel_dir}/*.cxx"
    "${rel_dir}/*.cpp")

  if(_srces STREQUAL "")
    message(FATAL_ERROR "bw_add_folder_entry: no sources under '${rel_dir}'")
  endif()

  bw_make_target_name(_tgt "${prefix}" "${rel_dir}")
  add_executable("${_tgt}" ${_srces})
  target_compile_features("${_tgt}" PRIVATE cxx_std_20)

  bw_public_link_target(_pub)
  target_link_libraries("${_tgt}" PRIVATE "${_pub}")

  bw_runtime_paths("${_tgt}")

  set_property(TARGET "${_tgt}" PROPERTY VS_DEBUGGER_WORKING_DIRECTORY
                                         "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")

  bw_register_test("${_tgt}" "${rel_dir}" "${label}")
endfunction()
