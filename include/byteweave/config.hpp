// Build-time feature toggles (defaults); may be overridden via compiler -D flags.
// In single-header builds the preamble sets BYTEWEAVE_AMALGAMATED=1 before inlining.
#pragma once

#ifndef BYTEWEAVE_HEADER_ONLY
#  define BYTEWEAVE_HEADER_ONLY BYTEWEAVE_AMALGAMATED
#endif

#ifndef BYTEWEAVE_STRICT_DECODING
#  define BYTEWEAVE_STRICT_DECODING 0
#endif

#ifndef BYTEWEAVE_URLSAFE_DEFAULT
#  define BYTEWEAVE_URLSAFE_DEFAULT 0
#endif
