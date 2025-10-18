#include <cstdio>

#if defined(BYTEWEAVE_USE_SINGLE_HEADER)
#  include BYTEWEAVE_SINGLE_HEADER
#else
#  include <byteweave/byteweave.hpp>
#endif

using byteweave::status;

static int expect(const char* name, status got, status want)
{
  if (got != want) {
    std::fprintf(stderr, "%s: got=%u want=%u\n", name, unsigned(got), unsigned(want));
    return 1;
  }
  return 0;
}

int main()
{
  int fail = 0;

  // zero-length spans; APIs ignore inputs in stub phase
  std::span<const std::byte> in{};
  std::span<std::byte>       out{};

  // base64
  fail |= expect("b64.enc", byteweave::base64::encode(in, out).code, status::not_implemented);
  fail |= expect("b64.dec", byteweave::base64::decode(in, out).code, status::not_implemented);

  // hex
  fail |= expect("hex.enc", byteweave::hex::encode(in, out).code, status::not_implemented);
  fail |= expect("hex.dec", byteweave::hex::decode(in, out).code, status::not_implemented);

  // varint
  fail |= expect("var.enc", byteweave::varint::encode(in, out).code, status::not_implemented);
  fail |= expect("var.dec", byteweave::varint::decode(in, out).code, status::not_implemented);

  return fail;
}
