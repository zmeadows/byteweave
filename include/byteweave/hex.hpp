#pragma once
#include <byteweave/export.hpp>
#include <byteweave/types.hpp>
#include <byteweave/config.hpp>
#include <span>

namespace byteweave::hex {

// Hex encode binary -> textual hex into 'out'.
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API encode_result encode(std::span<const std::byte> in,
                            std::span<std::byte>       out,
                            bool                       uppercase = false) noexcept;

// Hex decode textual hex -> binary into 'out'.
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API decode_result decode(std::span<const std::byte> in, std::span<std::byte> out) noexcept;

} // namespace byteweave::hex

#if BYTEWEAVE_HEADER_ONLY
#  include <byteweave/detail/hex.inl>
#endif
