#pragma once
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#define _open open
#define _read read
#define _close close
#define _O_BINARY 0
#define _O_RDONLY O_RDONLY
#define _O_SEQUENTIAL 0
inline int _eof(int fd){struct stat s{};fstat(fd,&s);return lseek(fd,0,SEEK_CUR)>=s.st_size;}
