// Common API types
#pragma once
#include <cstddef>
#include <cstdint>
#include <span>

namespace byteweave {

enum class status : std::uint8_t {
  ok               = 0,
  invalid_input    = 1,
  output_too_small = 2,
  not_implemented  = 255
};

struct encode_result {
  std::size_t consumed{};
  std::size_t produced{};
  status      code{status::ok};
};

struct decode_result {
  std::size_t consumed{};
  std::size_t produced{};
  status      code{status::ok};
};

} // namespace byteweave
