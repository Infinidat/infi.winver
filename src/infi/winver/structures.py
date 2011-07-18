
from infi.instruct import Struct, UBInt32, FixedSizeString, UBInt16, UBInt8, UBInt64

def _is_64bit():
    from sys import maxsize
    return maxsize > 2 ** 32

DWORD = UBInt32
TCHAR = FixedSizeString
WORD = UBInt16
BYTE = UBInt8
LPVOID = UBInt64 if _is_64bit() else UBInt32
BOOL = DWORD

class OSVersionEx(Struct):
    _fields_ = [
        DWORD("size"),
        DWORD("major_version"),
        DWORD("minor_version"),
        DWORD("build_number"),
        DWORD("platform_id"),
        TCHAR("csd_version", 128),
        WORD("service_pack_major"),
        WORD("service_pack_minor"),
        WORD("suite_mask"),
        BYTE("product_type"),
        BYTE("reserved")
        ]

class SystemInfo(Struct):
    _fields = [
        DWORD("oem_id"),
        WORD("processor_architecture"),
        WORD("resrrved"),
        DWORD("page_Size"),
        LPVOID("minimum_application_address"),
        LPVOID("maximum_application_address"),
        DWORD("active_processor_mask"),
        DWORD("number_of_processors"),
        DWORD("processor_type"),
        DWORD("allocation_granularity"),
        WORD("processor_level"),
        WORD("processor_revision")
        ]
