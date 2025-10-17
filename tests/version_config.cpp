#include <byteweave/byteweave.hpp>
#include <cstdio>

int main()
{
#ifndef BYTEWEAVE_VERSION_MAJOR
#  error "BYTEWEAVE_VERSION_MAJOR not defined"
#endif
#ifndef BYTEWEAVE_VERSION_MINOR
#  error "BYTEWEAVE_VERSION_MINOR not defined"
#endif
#ifndef BYTEWEAVE_VERSION_PATCH
#  error "BYTEWEAVE_VERSION_PATCH not defined"
#endif
#ifndef BYTEWEAVE_HEADER_ONLY
#  error "BYTEWEAVE_HEADER_ONLY not defined"
#endif
  std::printf("byteweave %d.%d.%d (HEADER_ONLY=%d)\n",
              (int)BYTEWEAVE_VERSION_MAJOR,
              (int)BYTEWEAVE_VERSION_MINOR,
              (int)BYTEWEAVE_VERSION_PATCH,
              (int)BYTEWEAVE_HEADER_ONLY);
  return 0;
}
