#pragma once

#include <common/ByteSwap.h>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

namespace caprica {

struct CapricaBinaryReader {
  Endianness endianness { Endianness::Little };
  explicit CapricaBinaryReader(const std::string& file) : strm(file, std::ifstream::binary) {
    strm.exceptions(std::ifstream::badbit | std::ifstream::failbit);
  }
  CapricaBinaryReader(const CapricaBinaryReader&) = delete;
  ~CapricaBinaryReader() = default;

  bool eof() {
    strm.peek();
    return strm.eof();
  }

  template <typename T>
  T read() {
    if constexpr (std::is_same_v<T, int8_t>) {
    int8_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, uint8_t>) {
    uint8_t val = 0;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, int16_t>) {
    int16_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, uint16_t>) {
    uint16_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, int32_t>) {
    int32_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, uint32_t>) {
    uint32_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, float>) {
    float val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap_float(val);
  
    }
    else if constexpr (std::is_same_v<T, time_t>) {
    static_assert(sizeof(time_t) == 8, "time_t is not 64 bits");
    time_t val;
    strm.read((char*)&val, sizeof(val));
    return endianness == Endianness::Little ? val : byteswap(val);
  
    }
    else if constexpr (std::is_same_v<T, std::string>) {
    auto len = read<uint16_t>();
    std::unique_ptr<char[]> buf(new char[len]);
    strm.read(buf.get(), len);
    return std::string(buf.get(), buf.get() + len);
  
    }
    else { static_assert(std::is_same_v<T, void>, "Unsupported type"); }
  }


protected:
  std::ifstream strm;
};

}
