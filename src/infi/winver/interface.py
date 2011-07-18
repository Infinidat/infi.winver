'''
Created on Jul 18, 2011

@author: guy
'''

from infi.crap import WrappedFunction
from infi.crap import errcheck_zero, errcheck_nothing
from infi.crap import IN, IN_OUT, OUT

from ctypes import c_void_p, c_buffer, sizeof, c_ulong, byref, create_string_buffer

class LibraryFunction(WrappedFunction):
    @classmethod
    def _get_library(cls):
        try:
            import ctypes
            return ctypes.windll.kernel32
        except:
            raise OSError

class GetVersionExA(LibraryFunction):
    @classmethod
    def get_errcheck(cls):
        return errcheck_zero()

    @classmethod
    def get_parameters(cls):
        return ((c_void_p, IN_OUT, "lpVersionInfo"),)

class GetSystemInfo(LibraryFunction):
    @classmethod
    def get_errcheck(cls):
        return errcheck_nothing()

    @classmethod
    def get_parameters(cls):
        return ((c_void_p, IN_OUT, "lpSystemInfo"),)

class GetProductInfo(LibraryFunction):
    @classmethod
    def get_errcheck(cls):
        return errcheck_zero()

    @classmethod
    def get_parameters(cls):
        return ((c_ulong, IN, "majorVersion"),
                (c_ulong, IN, "minorVersion"),
                (c_ulong, IN, "spMajorVersion"),
                (c_ulong, IN, "spMinorVersion"),
                (c_void_p, IN_OUT, "returnedProductType"))

def get_version_ex():
    from .structures import OSVersionEx
    instance = OSVersionEx()
    instance.version_info_size = OSVersionEx.sizeof()
    buffer = create_string_buffer(OSVersionEx.instance_to_string(instance))
    GetVersionExA(buffer)
    return OSVersionEx.create_instance_from_string(buffer)

def get_system_info():
    from .structures import SystemInfo
    buffer = c_buffer(SystemInfo.sizeof())
    GetSystemInfo(buffer)
    return SystemInfo.create_instance_from_string(buffer)

def get_product_info(major_version, minor_version, service_pack_major, service_pack_minor):
    result = c_ulong()
    GetProductInfo(major_version, minor_version, service_pack_major, service_pack_minor, byref(result))
    return result.value
