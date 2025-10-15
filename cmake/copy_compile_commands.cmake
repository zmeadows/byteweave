# cmake/copy_compile_commands.cmake
# Usage (from CMakeLists via custom target):
#   ${CMAKE_COMMAND} -D SRC=<build>/compile_commands.json
#                    -D DST=<source>/compile_commands.json
#                    -P ${CMAKE_SOURCE_DIR}/cmake/copy_compile_commands.cmake

if(NOT DEFINED SRC OR NOT DEFINED DST)
  message(FATAL_ERROR "copy_compile_commands.cmake requires -D SRC=... and -D DST=...")
endif()

# The compile_commands.json is produced at configure/generate time if
# CMAKE_EXPORT_COMPILE_COMMANDS=ON, which is supported by Ninja/Unix Makefiles.
if(NOT EXISTS "${SRC}")
  message(WARNING "compile_commands.json not found at: ${SRC} — was export enabled?")
  return()
endif()

# Copy only if different (avoids touching the file unnecessarily)
execute_process(COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${SRC}" "${DST}"
                RESULT_VARIABLE _rc)

if(_rc EQUAL 0)
  message(STATUS "Copied compile_commands.json to: ${DST}")
else()
  message(WARNING "Failed to copy compile_commands.json (rc=${_rc})")
endif()
