#pragma once
#include <cstdint>
#include <cstring>
#include <strings.h>
#include <cassert>
#include <cstdlib>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <immintrin.h>
#define __declspec(x)
#define __assume(x) do { if (!(x)) __builtin_unreachable(); } while(0)
#define __debugbreak() __builtin_trap()
#define _stricmp strcasecmp
#define _strnicmp strncasecmp
#define strnicmp strncasecmp
#define _byteswap_ushort __builtin_bswap16
#define _byteswap_ulong __builtin_bswap32
#define _byteswap_uint64 __builtin_bswap64
#define abstract
