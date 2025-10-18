cmake_minimum_required(VERSION 3.20)

if(NOT BYTEWEAVE_BUILD_LIBRARY)
  message(STATUS "Tests skipped: BYTEWEAVE_BUILD_LIBRARY=OFF")
  return()
endif()

enable_testing()

# Discover tests:
# - Any folder under tests/ is a "group" (label), e.g., unit/, roundtrip/, conformance/, ...
# - Each test lives in its own subfolder and has an entry file named main.cpp or test.cpp
# - We don't hard-code group names; we just find entry files anywhere under tests/
file(
  GLOB_RECURSE _TEST_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "main.cpp" "test.cpp")

if(_TEST_MAINS STREQUAL "")
  message(STATUS "[tests] No tests found (*/main.cpp or */test.cpp).")
  return()
endif()

# Turn a relative path into a unique target name: t-<group>-foo-bar
function(_bw_test_target_name OUT REL_DIR)
  string(REPLACE "/" "-" _name "${REL_DIR}")
  string(TOLOWER "${_name}" _name)
  set(${OUT}
      "t-${_name}"
      PARENT_SCOPE)
endfunction()

foreach(rel_main IN LISTS _TEST_MAINS)
  # rel_main might be: "unit/smoke/main.cpp" or "conformance/utf8/illegal/test.cpp"
  get_filename_component(rel_dir "${rel_main}" DIRECTORY)

  # First path segment is the CTest label (group), e.g., "unit", "roundtrip", "conformance"
  string(REGEX MATCH "^[^/]+" label "${rel_dir}")
  if(label STREQUAL "")
    # Edge case: an entry file directly inside tests/ (not recommended). Put under "misc".
    set(label "misc")
  endif()

  # Path without the first segment for nicer names (e.g., "smoke" or "utf8/illegal")
  string(REGEX REPLACE "^[^/]+/" "" short "${rel_dir}")
  if(short STREQUAL "")
    # Edge case: tests/<label>/main.cpp
    set(short "${label}")
  endif()

  _bw_test_target_name(tgt "${label}-${short}")

  # All sources in that test folder (multi-file tests just work)
  file(
    GLOB
    TEST_SRCS
    CONFIGURE_DEPENDS
    "${rel_dir}/*.c"
    "${rel_dir}/*.cc"
    "${rel_dir}/*.cxx"
    "${rel_dir}/*.cpp")

  add_executable(${tgt} ${TEST_SRCS})
  target_compile_features(${tgt} PRIVATE cxx_std_20)
  target_link_libraries(${tgt} PRIVATE byteweave)

  # --- Friendly runtime paths for shared builds ---
  if(BYTEWEAVE_BUILD_SHARED)
    if(WIN32)
      # Copy runtime DLLs next to the test exe (fixes STATUS_DLL_NOT_FOUND on MSVC)
      if(CMAKE_VERSION VERSION_LESS 3.21)
        add_custom_command(
          TARGET ${tgt}
          POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:byteweave>
                  $<TARGET_FILE_DIR:${tgt}>)
      else()
        add_custom_command(
          TARGET ${tgt}
          POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_RUNTIME_DLLS:${tgt}>
                  $<TARGET_FILE_DIR:${tgt}>
          COMMAND_EXPAND_LISTS)
      endif()
    elseif(APPLE)
      set_target_properties(${tgt} PROPERTIES BUILD_RPATH "@loader_path" INSTALL_RPATH
                                                                         "@loader_path")
    else() # Linux/ELF
      set_target_properties(
        ${tgt}
        PROPERTIES SKIP_BUILD_RPATH OFF
                   BUILD_RPATH "\$ORIGIN"
                   INSTALL_RPATH "\$ORIGIN")
    endif()
  endif()

  # Nice UX in Visual Studio
  set_property(TARGET ${tgt} PROPERTY VS_DEBUGGER_WORKING_DIRECTORY
                                      "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")

  # Register test with label + working directory (so local data files resolve)
  add_test(NAME ${tgt} COMMAND $<TARGET_FILE:${tgt}>)
  set_tests_properties(${tgt} PROPERTIES LABELS "${label}" WORKING_DIRECTORY
                                         "${CMAKE_CURRENT_SOURCE_DIR}/${rel_dir}")
endforeach()
