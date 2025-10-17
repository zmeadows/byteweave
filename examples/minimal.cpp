#include <cstddef>
#include <cstdint>
#include <iostream>
#include <vector>

// BYTEWEAVE_SINGLE_HEADER is a string literal path set by the build.
#if defined(BYTEWEAVE_USE_SINGLE_HEADER)
#  include BYTEWEAVE_SINGLE_HEADER
#else
#  include <byteweave/byteweave.hpp>
#endif

using std::byte;

int main()
{
  // tiny input buffer just to exercise the API
  const std::uint8_t raw[5] = {1, 2, 3, 4, 5};
  std::vector<byte>  in(sizeof(raw));
  for (std::size_t i = 0; i < sizeof(raw); ++i)
    in[i] = static_cast<byte>(raw[i]);

  std::vector<byte> out(64); // arbitrary scratch

  // Base64
  auto e64 = byteweave::base64::encode(in, out);
  auto d64 = byteweave::base64::decode(out, in);
  std::cout << "base64 encode status=" << static_cast<int>(e64.code) << " produced=" << e64.produced
            << "\n";
  std::cout << "base64 decode status=" << static_cast<int>(d64.code) << " produced=" << d64.produced
            << "\n";

  // Hex
  auto ehx = byteweave::hex::encode(in, out, /*uppercase*/ false);
  auto dhx = byteweave::hex::decode(out, in);
  std::cout << "hex encode status=" << static_cast<int>(ehx.code) << " produced=" << ehx.produced
            << "\n";
  std::cout << "hex decode status=" << static_cast<int>(dhx.code) << " produced=" << dhx.produced
            << "\n";

  // Varint (placeholder semantics)
  auto evr = byteweave::varint::encode(in, out);
  auto dvr = byteweave::varint::decode(out, in);
  std::cout << "varint encode status=" << static_cast<int>(evr.code) << " produced=" << evr.produced
            << "\n";
  std::cout << "varint decode status=" << static_cast<int>(dvr.code) << " produced=" << dvr.produced
            << "\n";

  // Treat not_implemented as success for now; this is only a smoke compile/run.
  return 0;
}
