#pragma once
#include <byteweave/export.hpp>
#include <byteweave/types.hpp>
#include <byteweave/config.hpp>
#include <span>
#include <string_view>

namespace byteweave::base64 {

// Encodes binary -> textual base64 into 'out'.
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API encode_result encode(std::span<const std::byte> in,
                            std::span<std::byte>       out,
                            bool urlsafe = (BYTEWEAVE_URLSAFE_DEFAULT != 0)) noexcept;

// Decodes textual base64 -> binary into 'out'.
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API decode_result decode(std::span<const std::byte> in,
                            std::span<std::byte>       out,
                            bool urlsafe = (BYTEWEAVE_URLSAFE_DEFAULT != 0)) noexcept;

} // namespace byteweave::base64

#if BYTEWEAVE_HEADER_ONLY
#  include <byteweave/detail/base64.inl>
#endif