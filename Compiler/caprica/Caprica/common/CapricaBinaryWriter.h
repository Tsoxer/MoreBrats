#pragma once

#include <cassert>
#include <cstdint>
#include <limits>
#include <string_view>

#include <common/allocators/ChainedPool.h>
#include <common/ByteSwap.h>
#include <common/FSUtils.h>

namespace caprica {

struct CapricaBinaryWriter {
  Endianness endianness { Endianness::Little };
  explicit CapricaBinaryWriter() = default;
  CapricaBinaryWriter(const CapricaBinaryWriter&) = delete;
  ~CapricaBinaryWriter() = default;

  template <typename F>
  void applyToBuffers(F&& func) {
    for (auto beg = strm.begin(), end = strm.end(); beg != end; ++beg)
      func(beg.data(), beg.size());
  }

  template <typename T>
  void boundWrite(size_t val) {
    assert(val <= std::numeric_limits<T>::max());
    write<T>((T)val);
  }

  template <typename T>
  void write(T val) {
    if constexpr (std::is_same_v<T, int8_t>) {
    strm.make<int8_t>(val);
  
    }
    else if constexpr (std::is_same_v<T, uint8_t>) {
    strm.make<uint8_t>(val);
  
    }
    else if constexpr (std::is_same_v<T, int16_t>) {
    strm.make<int16_t>(endianness == Endianness::Little ? val : byteswap(val));
  
    }
    else if constexpr (std::is_same_v<T, uint16_t>) {
    strm.make<uint16_t>(endianness == Endianness::Little ? val : byteswap(val));
  
    }
    else if constexpr (std::is_same_v<T, int32_t>) {
    strm.make<int32_t>(endianness == Endianness::Little ? val : byteswap(val));
  
    }
    else if constexpr (std::is_same_v<T, uint32_t>) {
    strm.make<uint32_t>(endianness == Endianness::Little ? val : byteswap(val));
  
    }
    else if constexpr (std::is_same_v<T, float>) {
    strm.make<float>(endianness == Endianness::Little ? val : byteswap_float(val));
  
    }
    else if constexpr (std::is_same_v<T, time_t>) {
    static_assert(sizeof(time_t) == 8, "time_t is not 64 bits");
    strm.make<time_t>(endianness == Endianness::Little ? val : byteswap(val));
  
    }
    else if constexpr (std::is_same_v<T, std::string_view>) {
    boundWrite<uint16_t>(val.size());
    if (val.size())
      append(val.data(), val.size());
  
    }
    else if constexpr (std::is_same_v<T, identifier_ref>) {
    boundWrite<uint16_t>(val.size());
    if (val.size())
      append(val.data(), val.size());
  
    }
    else { static_assert(std::is_same_v<T, void>, "Unsupported type"); }
  }


protected:
  allocators::ChainedPool strm { 1024 * 4 };

  void append(const char* __restrict a, size_t size) {
    // ChainedPool will re-order large allocations, so disallow them.
    assert(size < 4096);
    memcpy(strm.allocate(size), a, size);
  }
};

}
