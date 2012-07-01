
from infi.instruct import Struct, ULInt32, FixedSizeString, ULInt16, ULInt8, ULInt64

def _is_64bit():
    from sys import maxsize
    return maxsize > 2 ** 32

DWORD = ULInt32
TCHAR = FixedSizeString
WORD = ULInt16
BYTE = ULInt8
LPVOID = ULInt64 if _is_64bit() else ULInt32
BOOL = DWORD

class OSVersionEx(Struct):
    _fields_ = [
        DWORD("version_info_size", 0),
        DWORD("major_version", 0),
        DWORD("minor_version", 0),
        DWORD("build_number", 0),
        DWORD("platform_id", 0),
        TCHAR("csd_version", 128),
        WORD("service_pack_major", 0),
        WORD("service_pack_minor", 0),
        WORD("suite_mask", 0),
        BYTE("product_type", 0),
        BYTE("reserved", 0)
        ]

class SystemInfo(Struct):
    _fields_ = [
        WORD("processor_architecture"),
        WORD("reserved"),
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
