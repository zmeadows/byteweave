cmake_minimum_required(VERSION 3.20)
include(ByteweaveCTest)

file(
  GLOB_RECURSE _EXAMPLE_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "*/main.cpp")

if(_EXAMPLE_MAINS STREQUAL "")
  message(STATUS "[examples] No examples found (*/main.cpp).")
  return()
endif()

foreach(rel_main IN LISTS _EXAMPLE_MAINS)
  get_filename_component(rel_dir "${rel_main}" DIRECTORY)
  bw_add_folder_entry("${rel_dir}" "examples" "ex-")
endforeach()
