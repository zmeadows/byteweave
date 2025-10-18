#pragma once

// Project headers needed by all .inl implementations
#include <byteweave/config.hpp>
#include <byteweave/export.hpp>
#include <byteweave/types.hpp>

// Common std headers used across inls
#include <cstddef> // IWYU pragma: keep
#include <cstring> // IWYU pragma: keep
#include <span> // IWYU pragma: keep
#include <string_view> // IWYU pragma: keep

#ifndef BW_DEF
#  if BYTEWEAVE_HEADER_ONLY
#    define BW_DEF inline
#  else
#    define BW_DEF
#  endif
#endif
