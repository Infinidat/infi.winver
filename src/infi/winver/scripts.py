
def print_records():
    from .interface import get_product_info, get_system_info, get_version_ex
    from .structures import OSVersionEx, SystemInfo

    version = get_version_ex()
    system_info = get_system_info()
    product_info = get_product_info(version.major_version, version.minor_version,
                                    version.service_pack_major, version.service_pack_minor)
    print "OSVersionEx = %s" % repr(OSVersionEx.instance_to_string(version))
    print "SystemInfo = %s" % repr(SystemInfo.instance_to_string(system_info))
    print "ProductInfo = %s" % repr(product_info)
