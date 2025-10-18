cmake_minimum_required(VERSION 3.20)

include(ByteweaveCTest)

# Discover tests: look for main.cpp or test.cpp under subfolders
file(
  GLOB_RECURSE _TEST_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "main.cpp" "test.cpp")
if(_TEST_MAINS STREQUAL "")
  message(STATUS "[tests] No tests found (*/main.cpp or */test.cpp).")
  return()
endif()

# Unique directories that contain a test entry
set(_TEST_DIRS)
foreach(rel_main IN LISTS _TEST_MAINS)
  get_filename_component(_dir "${rel_main}" DIRECTORY)
  list(APPEND _TEST_DIRS "${_dir}")
endforeach()
list(REMOVE_DUPLICATES _TEST_DIRS)

foreach(rel_dir IN LISTS _TEST_DIRS)
  # First path segment is the CTest label (group), e.g., "unit", "roundtrip"
  string(REGEX MATCH "^[^/]+" label "${rel_dir}")
  if(label STREQUAL "")
    set(label "misc")
  endif()
  bw_add_folder_entry("${rel_dir}" "${label}" "t")
endforeach()
