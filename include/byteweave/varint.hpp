#pragma once
#include <byteweave/export.hpp>
#include <byteweave/types.hpp>
#include <byteweave/config.hpp>
#include <span>

namespace byteweave::varint {

// Varint encode binary->binary (placeholder signature for now).
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API encode_result encode(std::span<const std::byte> in, std::span<std::byte> out) noexcept;

// Varint decode (placeholder signature for now).
// NOTE: Stub implementation; returns status::not_implemented for now.
BW_API decode_result decode(std::span<const std::byte> in, std::span<std::byte> out) noexcept;

} // namespace byteweave::varint

#if BYTEWEAVE_HEADER_ONLY
#  include <byteweave/detail/varint.inl>
#endif
