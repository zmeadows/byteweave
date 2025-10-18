cmake_minimum_required(VERSION 3.20)

# Find all */main.cpp under examples recursively
file(
  GLOB_RECURSE _EXAMPLE_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "*/main.cpp")

if(_EXAMPLE_MAINS STREQUAL "")
  message(STATUS "[examples] No examples found (*/main.cpp).")
  return()
endif()

# Utility: derive a unique target name from a relative directory (ex-io-csv)
function(_bw_target_name_from_rel_dir OUT_VAR REL_DIR)
  string(REPLACE "/" "-" _name "${REL_DIR}")
  string(REPLACE " " "-" _name "${_name}")
  string(TOLOWER "${_name}" _name)
  set(${OUT_VAR}
      "ex-${_name}"
      PARENT_SCOPE)
endfunction()

foreach(rel_main IN LISTS _EXAMPLE_MAINS)
  # rel_main like: "io/csv/main.cpp" -> rel_dir "io/csv"
  get_filename_component(rel_dir "${rel_main}" DIRECTORY)
  _bw_target_name_from_rel_dir(tgt "${rel_dir}")

  # Collect all sources in that example folder (scales to multi-file examples)
  file(
    GLOB
    EX_SRCS
    CONFIGURE_DEPENDS
    "${rel_dir}/*.cpp"
    "${rel_dir}/*.cc"
    "${rel_dir}/*.cxx"
    "${rel_dir}/*.c")

  add_executable(${tgt} ${EX_SRCS})
  target_compile_features(${tgt} PRIVATE cxx_std_20)

  # Prefer linking against the library if present; fall back to the amalgamated header.
  if(TARGET byteweave)
    target_link_libraries(${tgt} PRIVATE byteweave)
  elseif(TARGET single_header)
    add_dependencies(${tgt} single_header)
    target_compile_definitions(${tgt} PRIVATE BYTEWEAVE_USE_SINGLE_HEADER=1
                                              BYTEWEAVE_SINGLE_HEADER="${BYTEWEAVE_SINGLE_HEADER}")
  else()
    message(FATAL_ERROR "No 'byteweave' library or 'single_header' target available.\n"
                        "Enable BYTEWEAVE_BUILD_LIBRARY or BYTEWEAVE_BUILD_SINGLE_HEADER.")
  endif()

  # Friendly runpaths for shared builds so executables run from the build tree.
  if(BYTEWEAVE_BUILD_SHARED)
    set_target_properties(
      ${tgt}
      PROPERTIES SKIP_BUILD_RPATH OFF
                 BUILD_RPATH_USE_ORIGIN ON
                 INSTALL_RPATH_USE_LINK_PATH ON)
  endif()

  # Nice UX for Visual Studio "Run" and debugging in the example folder
  set_property(TARGET ${tgt} PROPERTY VS_DEBUGGER_WORKING_DIRECTORY
                                      "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")

  # Register as a CTest test with label "examples", run from the example's folder
  add_test(NAME ${tgt} COMMAND $<TARGET_FILE:${tgt}>)
  set_tests_properties(
    ${tgt}
    PROPERTIES
      LABELS
      "examples"
      WORKING_DIRECTORY
      "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}"
      # Augment PATH only on Windows (CMake >= 3.16 supports genex in test props)
      ENVIRONMENT
      "$<$<PLATFORM_ID:Windows>:PATH=$<SHELL_PATH:$<TARGET_FILE_DIR:byteweave>>;$ENV{PATH}>")
endforeach()
