#pragma once

// Default to 0 when included outside of our build (e.g., single-header)
#if !defined(BYTEWEAVE_BUILD_SHARED)
#  define BYTEWEAVE_BUILD_SHARED 0
#endif

// BW_API marks public symbols. Only decorate when building/using a DLL.
#if defined(_MSC_VER)
#  if BYTEWEAVE_BUILD_SHARED
#    if defined(BW_BUILDING_DLL)
#      define BW_API __declspec(dllexport)
#    else
#      define BW_API __declspec(dllimport)
#    endif
#  else
#    define BW_API
#  endif
#else
// On ELF/Mach-O we generally compile with -fvisibility=hidden;
// expose API only when building a shared library.
#  if BYTEWEAVE_BUILD_SHARED
#    define BW_API __attribute__((visibility("default")))
#  else
#    define BW_API
#  endif
#endif
