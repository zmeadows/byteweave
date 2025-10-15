#include <byteweave/detail/preamble.hpp>

namespace byteweave::varint {

BW_DEF encode_result encode(std::span<const std::byte> in, std::span<std::byte> out) noexcept
{
  (void)in;
  (void)out;
  return {0u, 0u, status::not_implemented};
}

BW_DEF decode_result decode(std::span<const std::byte> in, std::span<std::byte> out) noexcept
{
  (void)in;
  (void)out;
  return {0u, 0u, status::not_implemented};
}

} // namespace byteweave::varint
