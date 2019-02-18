__import__("pkg_resources").declare_namespace(__name__)

# version numbers in Windows are very tricky and there are several places we have to look at
# * "GetVersionEx" API will return major and minor versions that identify Windows versions lower than
#    6.2 (Windows 2012 / Windows 8). It will be "stuck" at 6.2 for >= Windows Server 2012 / Windows 8
#   (unless the application has a proper manifest - which we don't rely on)
# * Registry value "HKLM\Software\Microsoft\Windows NT\CurrentVersion\CurrentVersion" will differentiate between
#   Windows Server 2012 / Windows 8 and Windows Server 2012 R2 / Windows 8.1 (6.3).
#   This value will be "stuck" at 6.3 for >= Windows 2012 R2 / Windows 8.1
# * Registry values "HKLM\Software\Microsoft\Windows NT\CurrentVersion\CurrentMajorVersion" and "CurrentMinorVersion"
#   are available for Windows Server 2016 / Windows 10 and on. They will be "stuck" at 10 and 0 (10.0) for
#   Windows Server 2016 / Windows 10 and on.
# * Registry value "HKLM\Software\Microsoft\Windows NT\CurrentVersion\ReleaseId" can differentiate versions of
#   Windows >= Server 2016 / 10. Release IDs are different for each update of Windows 10 and Windows Server 2016 and up
# * To differentiate between the Server versions and Workstation versions (Vista/7/8/8.1/10 etc.), the "product id"
#   from GetVersionEx will be "1" for the workstation versions, and 2 or 3 for the server versions.
# See https://docs.microsoft.com/en-us/windows/desktop/sysinfo/operating-system-version for major/minor version list

version_to_name = {
    (5, 0): 'Windows 2000',
    (5, 1): 'Windows XP',
    (5, 2, 1): 'Windows XP',    # Windows XP spans over 5.1 and 5.2 (workstation type)
    (5, 2): 'Windows Server 2003',
    # TODO Windows Server 2003 R2 uses the same version. We may need to read something else to recognize it
    (6, 0, 1): 'Windows Vista',
    (6, 0): 'Windows Server 2008',
    (6, 1, 1): 'Windows 7',
    (6, 1): 'Windows Server 2008 R2',
    (6, 2, 1): 'Windows 8',
    (6, 2): 'Windows Server 2012',
    (6, 3, 1): 'Windows 8.1',
    (6, 3): 'Windows Server 2012 R2',
    # the following will *not* be used by analyze_windows_version.
    # these are for "name_to_version" (used by greater_than)
    (10, 0): 'Windows 10',
    (10, 0, 1607): 'Windows Server 2016',
    (10, 0, 1809): 'Windows Server 2019',
}
win10_release_id_to_update = {
    1507: 'Gold',
    1511: 'November Update',
    1607: 'Aniversary Update',
    1703: 'Creators Update',
    1709: 'Fall Creators Update',
    1803: 'April 2018 Update',
    1809: 'October 2018 Update',
}
win10_server_release_id_to_update = {
    # Windows Server 2016
    1607: 'RTM',
    # the following updates are supposedly "not Windows Server 2016" but we
    # recognize them as updates to Server 2016 nevertheless
    1703: 'Aniversary Update',      # a.k.a "Windows Server, v1703"
    1709: 'Fall Creators Update',   # a.k.a "Windows Server, v1709"
    1803: 'April 2018 Update',      # a.k.a "Windows Server, v1803"
    # Windows Server 2019
    1809: 'RTM',
}
# TODO supposedly there is a difference between "Windows Server, v1809"
# and "Windows Server 2019"? Do we need to check in more places to recognize this?
FIRST_WIN_SERVER_2019_RELEASE_ID = 1809

name_to_version = {value: key for key, value in version_to_name.items()}

class Windows(object):  # pylint: disable-msg=R0902,R0904
    def __init__(self):
        from .interface import get_version_ex
        self.hyper_v = False
        self.architecture = ""
        self.service_pack = ""
        self.server_core = False
        self.edition = ""
        self.version = ""
        self._version_ex = get_version_ex()
        self.analyze()

    def analyze(self):
        self.analyze_major_minor_versions()
        if self._major_version == 10:
            self._release_id = self.get_release_id_from_registry()
            self.analyze_windows10_version()
            self.analyze_windows10_update()
        else:
            self.analyze_windows_version()
        self.analyze_windows_edition()
        self.analyze_windows_service_pack()
        self.analyze_windows_architecture()

    def analyze_major_minor_versions(self):
        self._major_version = self._version_ex.major_version
        self._minor_version = self._version_ex.minor_version
        self._product_type = self._version_ex.product_type
        if (self._major_version, self._minor_version) == (6, 2):
            # GetVersionEx will return 6.2 for Windows 2012 and up. See documentation above.
            self._major_version, self._minor_version = self.get_version_from_registry()

    def analyze_windows_version(self):
        version = (self._major_version, self._minor_version, self._product_type)
        self.version = version_to_name.get(version, version_to_name.get(version[:2], 'Unknown'))

    def analyze_windows10_version(self):
        from .constants import VER_NT_WORKSTATION
        # Windows 10 and on, and Windows Server 2016 and on, use only "release id" to differentiate different releases
        # product_type still determines whether this is Windows 10 or Windows Server
        if self._product_type == VER_NT_WORKSTATION:
            self.version = "Windows 10"
        elif self._release_id < FIRST_WIN_SERVER_2019_RELEASE_ID:
            self.version = "Windows Server 2016"
        else:
            self.version = "Windows Server 2019"

    def analyze_windows10_update(self):
        from .constants import VER_NT_WORKSTATION
        if self._product_type == VER_NT_WORKSTATION:
            release_id_to_update = win10_release_id_to_update
        else:
            release_id_to_update = win10_server_release_id_to_update
        self.win10_update = release_id_to_update.get(self._release_id, 'Unknown')

    def analyze_windows_edition(self):
        self.server_core = False
        self.hyper_v = False
        self.edition = 'Standard'
        if self._major_version == 5:
            self.analyze_windows5_edition()
        elif self._major_version == 6:
            self._edition = self.get_windows6_edition()
            self.analyze_windows6_edition()
            if self._minor_version >= 2:
                # http://msdn.microsoft.com/en-us/library/windows/desktop/ms724358(v=vs.85).aspx
                # PRODUCT_*_SERVER_CORE values are not returned in Windows Server 2012
                self.analyze_server_core_according_to_registry()
        elif self._major_version == 10:
            self._edition = self.get_windows6_edition()
            self.analyze_windows6_edition()
        else:
            self.edition = 'Unknown'

    def analyze_windows5_edition(self):
        from .constants import VER_SUITE_BACKOFFICE, VER_SUITE_COMPUTE_SERVER, VER_SUITE_DATACENTER
        from .constants import VER_SUITE_ENTERPRISE, VER_SUITE_STORAGE_SERVER, VER_SUITE_WH_SERVER
        (_, mask) = (self._version_ex.suite_mask, self._version_ex.product_type)
        if mask & VER_SUITE_BACKOFFICE:
            self.edition = 'BackOffice'
        elif mask & VER_SUITE_COMPUTE_SERVER:
            self.edition = 'Compute Cluster'
        elif mask & VER_SUITE_DATACENTER:
            self.edition = 'Datacenter'
        elif mask & VER_SUITE_ENTERPRISE:
            self.edition = 'Enterprise'
        elif mask & VER_SUITE_STORAGE_SERVER:
            self.edition = 'Storage'
        elif mask & VER_SUITE_WH_SERVER:
            self.edition = 'Home'
        else:
            self.edition = 'Standard'

    def get_windows6_edition(self):
        from .interface import get_product_info
        return get_product_info(self._version_ex.major_version,
                                self._version_ex.minor_version,
                                self._version_ex.service_pack_major,
                                self._version_ex.service_pack_minor)

    def analyze_server_core_according_to_dism(self):
        # http://stackoverflow.com/questions/13065479/how-to-detect-windows-2012-core-edition-c
        from os import environ, path
        from infi.execute import execute
        dism = path.join(environ.get("SYSTEMROOT"), "System32", "dism.exe")
        pid = execute([dism, "/online", "/get-features", "/format:table"])
        self.server_core = any("ServerCore-FullServer" in line and "Disabled" in line for
                               line in pid.get_stdout().decode().splitlines())

    def analyze_server_core_according_to_registry(self):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/hh846315%28v=vs.85%29.aspx
        from infi.registry import LocalComputer
        from infi.registry.errors import AccessDeniedException
        KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Server\ServerLevels"
        FEATURES = ("ServerCore", "Server-Gui-Mgmt", "Server-Gui-Shell")
        try:
            store = LocalComputer().local_machine[KEY].values_store
        except KeyError:
            return
        except AccessDeniedException:
            self.analyze_server_core_according_to_dism()
            return
        self.server_core = all(item in store for item in FEATURES)

    def get_release_id_from_registry(self):
        from infi.registry import LocalComputer
        local_machine = LocalComputer().local_machine
        reg_folder = local_machine[r'Software\Microsoft\Windows NT\CurrentVersion']
        release_id = int(reg_folder.values_store['ReleaseId'].to_python_object())
        return release_id

    def get_version_from_registry(self):
        # see documentation about reading the major/minor versions from the registry at the top of the file
        from infi.registry import LocalComputer
        local_machine = LocalComputer().local_machine
        reg_folder = local_machine[r'Software\Microsoft\Windows NT\CurrentVersion']
        major_version = reg_folder.values_store.get('CurrentMajorVersionNumber')
        minor_version = reg_folder.values_store.get('CurrentMinorVersionNumber')
        if major_version and minor_version:
            # should be 10.0
            return major_version.to_python_object(), minor_version.to_python_object()
        # 6.2 or 6.3
        major_version, minor_version = reg_folder.values_store['CurrentVersion'].to_python_object().split('.')
        return int(major_version), int(minor_version)

        return major_version, minor_version

    def analyze_windows6_edition(self):
        from .constants import PRODUCT_SUITE_CLUSTER, PRODUCT_SUITE_DATACENTER
        from .constants import PRODUCT_SUITE_ENTERPRISE, PRODUCT_SUITE_STORAGE, PRODUCT_SUITE_STANDARD
        from .constants import PRODUCT_SUITE_SMALL_BUSINESS
        from .constants import SERVER_CORE, HYPER_V
        if self._edition in PRODUCT_SUITE_CLUSTER:
            self.edition = 'Compute Cluster'
        if self._edition in PRODUCT_SUITE_DATACENTER:
            self.edition = 'Datacenter'
        elif self._edition in PRODUCT_SUITE_ENTERPRISE:
            self.edition = 'Enterprise'
        elif self._edition in PRODUCT_SUITE_STORAGE:
            self.edition = 'Storage'
        elif self._edition in PRODUCT_SUITE_STANDARD:
            self.edition = 'Standard'
        elif self._edition in PRODUCT_SUITE_SMALL_BUSINESS:
            self.edition = 'Small Business'
        else:
            self.edition = 'Client'
        if self._edition in SERVER_CORE:
            self.server_core = True
        if self._edition in HYPER_V:
            self.hyper_v = True

    def analyze_windows_service_pack(self):
        self.service_pack = self._version_ex.service_pack_major

    def analyze_windows_architecture(self):
        from .constants import PROCESSOR_ARCHITECTURE_AMD64, PROCESSOR_ARCHITECTURE_IA64, PROCESSOR_ARCHITECTURE_INTEL
        from .interface import get_system_info
        system_info = get_system_info()
        processor = system_info.processor_architecture
        if processor == PROCESSOR_ARCHITECTURE_AMD64:
            self.architecture = 'x64'
        elif processor == PROCESSOR_ARCHITECTURE_IA64:
            self.architecture = 'ia64'
        elif processor == PROCESSOR_ARCHITECTURE_INTEL:
            self.architecture = 'x86'
        else:
            self.architecture = 'unknown'

    def __str__(self):
        return "%s %s Service Pack %s" % (self.version, self.edition, self.service_pack)

    def is_windows_2000(self):
        return self.version == 'Windows 2000'

    def is_windows_xp(self):
        return self.version == 'Windows XP'

    def is_windows_2003(self):
        return self.version == 'Windows Server 2003'

    def is_windows_2008(self):
        return self.version == 'Windows Server 2008'

    def is_windows_2008_r2(self):
        return self.version == 'Windows Server 2008 R2'

    def is_windows_vista(self):
        return self.version == 'Windows Vista'

    def is_windows_7(self):
        return self.version == 'Windows 7'

    def is_windows_8(self):
        return self.version == 'Windows 8'

    def is_windows_10(self):
        return self.version == 'Windows 10'

    def is_windows_2012(self):
        return self.version == 'Windows Server 2012'

    def is_windows_2012_r2(self):
        return self.version == 'Windows Server 2012 R2'

    def is_windows_2016(self):
        return self.version == 'Windows Server 2016'

    def is_windows_2019(self):
        return self.version == 'Windows Server 2019'

    def is_x86(self):
        return self.architecture == 'x86'

    def is_x64(self):
        return self.architecture == 'x64'

    def is_ia64(self):
        return self.architecture == 'ia64'

    def is_server_core(self):
        return self.server_core

    def is_hyper_v(self):
        return self.hyper_v

    def is_cluster_aware(self):
        if self.edition == 'Enterprise':
            return True
        if self.edition == 'Datacenter':
            return True
        return False

    def greater_than(self, os_name):
        if os_name not in name_to_version:
            raise Exception("Could not find OS name {}".format(os_name))
        if self._major_version == 10:
            actual_version = (self._major_version, self._minor_version, self._release_id)
        else:
            actual_version = (self._major_version, self._minor_version)
        compared_version = name_to_version[os_name]
        if compared_version[0] < 10:
            # in name_to_version, values of Windows 10 have the release id in position 2
            # other values may have product id which needs to be stripped
            compared_version = compared_version[:2]
        return actual_version > compared_version
