
from infi.cwrap import WrappedFunction, errcheck_zero, errcheck_nothing, IN, IN_OUT
from ctypes import c_void_p, c_buffer, c_ulong, byref, create_string_buffer

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
    instance.version_info_size = OSVersionEx.min_max_sizeof().max  # pylint: disable-msg=E1101
    instance.csd_version = '\x00' * 128
    buff = create_string_buffer(OSVersionEx.write_to_string(instance))  # pylint: disable-msg=E1101
    GetVersionExA(buff)
    return OSVersionEx.create_from_string(buff)  # pylint: disable-msg=E1101

def get_system_info():
    from .structures import SystemInfo
    buff = c_buffer(SystemInfo.min_max_sizeof().max)  # pylint: disable-msg=E1101
    GetSystemInfo(buff)
    return SystemInfo.create_from_string(buff)  # pylint: disable-msg=E1101

def get_product_info(major_version, minor_version, service_pack_major, service_pack_minor):
    result = c_ulong()
    GetProductInfo(major_version, minor_version, service_pack_major, service_pack_minor, byref(result))
    return result.value
