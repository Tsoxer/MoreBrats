#pragma once
#include "compat.h"
#include <filesystem>
#include <sys/stat.h>
#include <unistd.h>
using DWORD=uint32_t;
struct FILETIME { DWORD dwLowDateTime,dwHighDateTime; };
union ULARGE_INTEGER { struct {DWORD LowPart,HighPart;}; uint64_t QuadPart; };
struct WIN32_FIND_DATA { DWORD dwFileAttributes; FILETIME ftLastWriteTime; DWORD nFileSizeLow,nFileSizeHigh; char cFileName[1024]; };
struct Finder { std::filesystem::directory_iterator it,end; };
using HANDLE=Finder*;
#define INVALID_HANDLE_VALUE nullptr
#define FILE_ATTRIBUTE_DIRECTORY 16
#define MAX_COMPUTERNAME_LENGTH 255
inline bool fillFind(HANDLE h,WIN32_FIND_DATA* d) {
 if(h->it==h->end)return false;
 auto p=h->it->path(); auto n=p.filename().string(); std::strcpy(d->cFileName,n.c_str());
 struct stat s{}; ::stat(p.c_str(),&s); d->dwFileAttributes=S_ISDIR(s.st_mode)?16:0;
 uint64_t t=(uint64_t(s.st_mtime)+11644473600ULL)*10000000ULL;
 d->ftLastWriteTime={DWORD(t),DWORD(t>>32)};
 d->nFileSizeLow=DWORD(s.st_size);d->nFileSizeHigh=DWORD(uint64_t(s.st_size)>>32);return true;
}
inline HANDLE FindFirstFileA(const char* pattern,WIN32_FIND_DATA* d) {
 try { auto h=new Finder{std::filesystem::directory_iterator(std::filesystem::path(pattern).parent_path()),{}};if(fillFind(h,d))return h;delete h;return nullptr; }catch(...){return nullptr;}
}
inline bool FindNextFileA(HANDLE h,WIN32_FIND_DATA* d){++h->it;return fillFind(h,d);}
inline void FindClose(HANDLE h){delete h;}
inline bool IsDebuggerPresent(){return false;}
inline bool GetComputerNameA(char* b,DWORD* n){std::strcpy(b,"CodexCloud");*n=10;return true;}
inline bool GetUserNameA(char* b,DWORD* n){std::strcpy(b,"Tsoxer");*n=7;return true;}
