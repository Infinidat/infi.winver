from __future__ import print_function

#pylint: disable-msg=E1101
def print_records():
    from .interface import get_product_info, get_system_info, get_version_ex
    from .structures import OSVersionEx, SystemInfo

    version = get_version_ex()
    system_info = get_system_info()
    try:
        product_info = get_product_info(version.major_version, version.minor_version,
                                    version.service_pack_major, version.service_pack_minor)
    except:  # pylint: disable-msg=W0702
        # product_info not available on Windows 2003, XP
        product_info = None
    print("OSVersionEx = %s" % repr(OSVersionEx.write_to_string(version)))
    print("SystemInfo = %s" % repr(SystemInfo.write_to_string(system_info)))
    print("ProductInfo = %s" % repr(product_info))
