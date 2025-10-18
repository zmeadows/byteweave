cmake_minimum_required(VERSION 3.20)

include(ByteweaveCTest)

# Find all */main.cpp under examples recursively
file(
  GLOB_RECURSE _EXAMPLE_MAINS
  RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
  CONFIGURE_DEPENDS "*/main.cpp")
if(_EXAMPLE_MAINS STREQUAL "")
  message(STATUS "[examples] No examples found (*/main.cpp).")
  return()
endif()

# Unique directories for examples
set(_EXAMPLE_DIRS)
foreach(rel_main IN LISTS _EXAMPLE_MAINS)
  get_filename_component(_dir "${rel_main}" DIRECTORY)
  list(APPEND _EXAMPLE_DIRS "${_dir}")
endforeach()
list(REMOVE_DUPLICATES _EXAMPLE_DIRS)

foreach(rel_dir IN LISTS _EXAMPLE_DIRS)
  bw_add_folder_entry("${rel_dir}" "examples" "ex")
endforeach()
