# Byteweave CTest helpers (shared by tests/ and examples/)
# Usage:
#   include(ByteweaveCTest)
#
# Provides:
#   bw_public_link_target(<out-var>)
#     - Creates (once) INTERFACE target: byteweave_public (+ alias byteweave::public)
#     - Behavior depends on BYTEWEAVE_CONSUME_MODE:
#         * library:      link to 'byteweave'
#         * header-only:  add include dirs + BYTEWEAVE_HEADER_ONLY=1 (+san if present)
#         * single-header:add dependency on ${BYTEWEAVE_SINGLE_HEADER_TARGET}, and
#                         defines BYTEWEAVE_USE_SINGLE_HEADER=1 and BYTEWEAVE_SINGLE_HEADER="<full path>"
#
#   bw_add_folder_entry(<rel_dir> <label> <prefix>)
#     - Adds an executable from all sources in <rel_dir>
#     - Links it against byteweave_public
#     - Sets rpaths (Apple/Linux), injects PATH for Windows DLLs at test time
#     - Registers a CTest test with LABELS=<label> and working dir=<rel_dir>
#
#   bw_register_test(<target> <rel_dir> <label>)
#     - Registers a CTest test that runs the target's binary
#     - Sets test LABELS and WORKING_DIRECTORY
#     - On Windows shared builds *with* the byteweave DLL target, prepends DLL dir to PATH
#
#   bw_runtime_paths(<target>)
#     - For shared builds, sets friendly rpaths so executables run from the build tree
#       * macOS:  @loader_path
#       * Linux:  $ORIGIN
#       * Windows: (no rpath concept; PATH is handled in bw_register_test)

if(NOT DEFINED BYTEWEAVE_CONSUME_MODE)
  set(BYTEWEAVE_CONSUME_MODE "library")
endif()

function(bw_public_link_target OUT)
  if(NOT TARGET byteweave_public)
    add_library(byteweave_public INTERFACE)

    if(BYTEWEAVE_CONSUME_MODE STREQUAL "library")
      if(NOT TARGET byteweave)
        message(FATAL_ERROR "BYTEWEAVE_CONSUME_MODE=library but target 'byteweave' does not exist.")
      endif()
      target_link_libraries(byteweave_public INTERFACE byteweave)
    elseif(BYTEWEAVE_CONSUME_MODE STREQUAL "header-only")
      target_include_directories(
        byteweave_public INTERFACE "$<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/generated>"
                                   "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>")
      target_compile_definitions(byteweave_public INTERFACE BYTEWEAVE_HEADER_ONLY=1)
      if(TARGET byteweave_san)
        target_link_libraries(byteweave_public INTERFACE byteweave_san)
      endif()
    elseif(BYTEWEAVE_CONSUME_MODE STREQUAL "single-header")
      if(NOT DEFINED BYTEWEAVE_SINGLE_HEADER)
        message(
          FATAL_ERROR
            "BYTEWEAVE_CONSUME_MODE=single-header but BYTEWEAVE_SINGLE_HEADER is undefined.")
      endif()
      # Ensure the single-header is generated before consumers compile.
      if(DEFINED BYTEWEAVE_SINGLE_HEADER_TARGET AND TARGET ${BYTEWEAVE_SINGLE_HEADER_TARGET})
        add_dependencies(byteweave_public ${BYTEWEAVE_SINGLE_HEADER_TARGET})
      else()
        if(TARGET byteweave_single_header)
          add_dependencies(byteweave_public byteweave_single_header)
        else()
          message(
            FATAL_ERROR
              "BYTEWEAVE_CONSUME_MODE=single-header but no 'byteweave_single_header' target found.")
        endif()
      endif()
      target_compile_definitions(
        byteweave_public
        INTERFACE BYTEWEAVE_USE_SINGLE_HEADER=1
                  BYTEWEAVE_SINGLE_HEADER="$<SHELL_PATH:${BYTEWEAVE_SINGLE_HEADER}>")
    else()
      message(
        FATAL_ERROR
          "Invalid BYTEWEAVE_CONSUME_MODE='${BYTEWEAVE_CONSUME_MODE}'. Expected one of: library;header-only;single-header"
      )
    endif()

    # Namespaced alias for convenience
    add_library(byteweave::public ALIAS byteweave_public)
  endif()

  set(${OUT}
      byteweave_public
      PARENT_SCOPE)
endfunction()

function(_bw_target_name OUT PREFIX REL_DIR)
  string(REPLACE "/" "-" _name "${REL_DIR}")
  string(TOLOWER "${_name}" _name)
  set(${OUT}
      "${PREFIX}-${_name}"
      PARENT_SCOPE)
endfunction()

function(bw_add_folder_entry REL_DIR LABEL PREFIX)
  _bw_target_name(_tgt "${PREFIX}" "${REL_DIR}")

  file(
    GLOB
    SRCS
    CONFIGURE_DEPENDS
    "${REL_DIR}/*.c"
    "${REL_DIR}/*.cc"
    "${REL_DIR}/*.cxx"
    "${REL_DIR}/*.cpp")
  if(SRCS STREQUAL "")
    message(FATAL_ERROR "bw_add_folder_entry: No sources found in '${REL_DIR}'.")
  endif()

  add_executable(${_tgt} ${SRCS})
  target_compile_features(${_tgt} PRIVATE cxx_std_20)

  bw_public_link_target(_pub)
  target_link_libraries(${_tgt} PRIVATE ${_pub})

  bw_runtime_paths(${_tgt})

  # Nice UX for IDEs: run from the folder
  set_property(TARGET ${_tgt} PROPERTY VS_DEBUGGER_WORKING_DIRECTORY
                                       "${CMAKE_CURRENT_SOURCE_DIR}/${REL_DIR}")

  bw_register_test(${_tgt} "${REL_DIR}" "${LABEL}")
endfunction()

function(bw_register_test target rel_dir label)
  if(NOT TARGET "${target}")
    message(FATAL_ERROR "bw_register_test: target '${target}' does not exist.")
  endif()

  # Compute the path to the runtime directory
  get_target_property(_out_dir "${target}" RUNTIME_OUTPUT_DIRECTORY)
  if(NOT _out_dir)
    set(_out_dir "${CMAKE_CURRENT_BINARY_DIR}")
  endif()

  # On Windows shared builds, inject PATH to find the byteweave DLL at test time.
  set(_env "")
  if(WIN32
     AND DEFINED BYTEWEAVE_BUILD_SHARED
     AND BYTEWEAVE_BUILD_SHARED
     AND TARGET byteweave)
    # Determine location of byteweave DLL
    get_target_property(_bw_out_dir byteweave RUNTIME_OUTPUT_DIRECTORY)
    if(NOT _bw_out_dir)
      set(_bw_out_dir "${CMAKE_BINARY_DIR}")
    endif()
    # Prepend DLL dir to PATH
    if(CMAKE_HOST_SYSTEM_NAME STREQUAL "Windows")
      set(_path_sep ";")
    else()
      set(_path_sep ":")
    endif()
    set(_env "PATH=${_bw_out_dir}${_path_sep}$ENV{PATH}")
  endif()

  add_test(NAME "${target}" COMMAND "${target}")
  set_tests_properties("${target}" PROPERTIES LABELS "${label}" WORKING_DIRECTORY
                                              "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")
  if(_env)
    set_tests_properties("${target}" PROPERTIES ENVIRONMENT "${_env}")
  endif()
endfunction()

function(bw_runtime_paths target)
  # Only meaningful for non-Windows shared builds, or if the library exists
  if(TARGET byteweave)
    if(APPLE)
      # Use @loader_path so example/test binaries run directly from build tree
      set_target_properties("${target}" PROPERTIES BUILD_RPATH "@loader_path" INSTALL_RPATH
                                                                              "@loader_path")
    elseif(UNIX)
      # Linux/ELF
      set_target_properties(
        "${target}"
        PROPERTIES SKIP_BUILD_RPATH OFF
                   BUILD_RPATH "\$ORIGIN"
                   INSTALL_RPATH "\$ORIGIN")
    endif()
  endif()
endfunction()
