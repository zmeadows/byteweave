cmake_minimum_required(VERSION 3.20)
enable_testing()
include(ByteweaveCTest)

file(
  GLOB_RECURSE _TEST_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "main.cpp" "test.cpp")

if(_TEST_MAINS STREQUAL "")
  message(STATUS "[tests] No tests found (*/main.cpp or */test.cpp).")
  return()
endif()

foreach(rel_main IN LISTS _TEST_MAINS)
  get_filename_component(rel_dir "${rel_main}" DIRECTORY)
  string(REGEX MATCH "^[^/]+" label "${rel_dir}")
  if(label STREQUAL "") # edge case: entry directly under tests/
    set(label "misc")
  endif()
  bw_add_folder_entry("${rel_dir}" "${label}" "t-")
endforeach()
