cmake_minimum_required(VERSION 3.20)

if(NOT BYTEWEAVE_BUILD_LIBRARY)
  message(STATUS "Tests skipped: BYTEWEAVE_BUILD_LIBRARY=OFF")
  return()
endif()

add_executable(bw_test_smoke min_smoke.cpp)
target_link_libraries(
  bw_test_smoke
  PRIVATE byteweave)
target_compile_features(bw_test_smoke PRIVATE cxx_std_20)
add_test(NAME bw_test_smoke COMMAND bw_test_smoke)

add_executable(bw_test_version version_config.cpp)
target_link_libraries(
  bw_test_version
  PRIVATE byteweave)
target_compile_features(bw_test_version PRIVATE cxx_std_20)
add_test(NAME bw_test_version COMMAND bw_test_version)
