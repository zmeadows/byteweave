#include <byteweave/detail/preamble.hpp>

namespace byteweave::base64 {

BW_DEF encode_result encode(std::span<const std::byte> in,
                            std::span<std::byte>       out,
                            bool /*urlsafe*/) noexcept
{
  (void)in;
  (void)out;
  return {0u, 0u, status::not_implemented};
}

BW_DEF decode_result decode(std::span<const std::byte> in,
                            std::span<std::byte>       out,
                            bool /*urlsafe*/) noexcept
{
  (void)in;
  (void)out;
  return {0u, 0u, status::not_implemented};
}

} // namespace byteweave::base64
