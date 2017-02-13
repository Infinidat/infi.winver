__import__("pkg_resources").declare_namespace(__name__)

version_to_name = {
    (5, 0): 'Windows 2000',
    (5, 1): 'Windows XP',
    (5, 2): 'Windows Server 2003',
    (6, 0, 1): 'Windows Vista',
    (6, 0): 'Windows Server 2008',
    (6, 1, 1): 'Windows 7',
    (6, 1): 'Windows Server 2008 R2',
    (6, 2, 1): 'Windows 8',
    (10, 0, 1): 'Windows 10',
    (6, 2): 'Windows Server 2012',
    (6, 3): 'Windows Server 2012 R2',
    (10, 0): 'Windows Server 2016',
}
name_to_version = {value: key[:2] for key, value in version_to_name.items()}

class Windows(object):  # pylint: disable-msg=R0902,R0904
    def __init__(self):
        from .interface import get_version_ex, get_system_info
        self.hyper_v = False
        self.architecture = ""
        self.service_pack = ""
        self.server_core = False
        self.edition = ""
        self.version = ""
        self._version_ex = get_version_ex()
        self._system_info = get_system_info()
        self._edition = ""
        self.analyze()

    def analyze(self):
        self.analyze_windows_version()
        self.analyze_windows_edition()
        self.analyze_windows_service_pack()
        self.analyze_windows_architecture()

        from infi.winver.interface import get_version_ex, get_system_info

    def analyze_windows_version(self):
        version = (self._version_ex.major_version, self._version_ex.minor_version, self._version_ex.product_type)
        if version[:2] == (6, 2):
            if self.analyze_windows_2016_version_by_registry() == 10:
                version = (10, 0)
        self.version = version_to_name.get(version, version_to_name.get(version[:2], 'Unknown'))

    def analyze_windows_edition(self):
        self.server_core = False
        self.hyper_v = False
        self.edition = 'Standard'
        if self._version_ex.major_version == 5:
            self.analyze_windows5_edition()
        elif self._version_ex.major_version == 6:
            self._edition = self.get_windows6_edition()
            self.analyze_windows6_edition()
            if self._version_ex.minor_version >= 2:
                # http://msdn.microsoft.com/en-us/library/windows/desktop/ms724358(v=vs.85).aspx
                # PRODUCT_*_SERVER_CORE values are not returned in Windows Server 2012
                self.analyze_server_core_according_to_registry()
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
                               line in pid.get_stdout().splitlines())

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

    def analyze_windows_2016_version_by_registry(self):
        from infi.registry import LocalComputer
        registry_path = r'Software\Microsoft\Windows NT\CurrentVersion'
        registry_key = 'CurrentMajorVersionNumber'
        try:
            local_machine = LocalComputer().local_machine
            reg_folder = local_machine[registry_path]
            return reg_folder.values_store.keys()[registry_key].to_python_object()
        except:
            pass

    def analyze_windows6_edition(self):
        from .constants import PRODUCT_SUITE_CLUSTER, PRODUCT_SUITE_DATACENTER
        from .constants import PRODUCT_SUITE_ENTERPRISE, PRODUCT_SUITE_STORAGE, PRODUCT_SUITE_STANDARD
        from .constants import PRODUCT_SUITE_SMALL_BUSINESS
        from .constants import SERVER_CORE, HYPER_V
        if PRODUCT_SUITE_CLUSTER.__contains__(self._edition):
            self.edition = 'Compute Cluster'
        if PRODUCT_SUITE_DATACENTER.__contains__(self._edition):
            self.edition = 'Datacenter'
        elif PRODUCT_SUITE_ENTERPRISE.__contains__(self._edition):
            self.edition = 'Enterprise'
        elif PRODUCT_SUITE_STORAGE.__contains__(self._edition):
            self.edition = 'Storage'
        elif PRODUCT_SUITE_STANDARD.__contains__(self._edition):
            self.edition = 'Standard'
        elif PRODUCT_SUITE_SMALL_BUSINESS.__contains__(self._edition):
            self.edition = 'Small Business'
        else:
            self.edition = 'Client'
        if SERVER_CORE.__contains__(self._edition):
            self.server_core = True
        if HYPER_V.__contains__(self._edition):
            self.hyper_v = True

    def analyze_windows_service_pack(self):
        self.service_pack = self._version_ex.service_pack_major

    def analyze_windows_architecture(self):
        from .constants import PROCESSOR_ARCHITECTURE_AMD64, PROCESSOR_ARCHITECTURE_IA64, PROCESSOR_ARCHITECTURE_INTEL
        self.architecture = ''
        processor = self._system_info.processor_architecture
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
        actual_version = (self._version_ex.major_version, self._version_ex.minor_version)
        return actual_version > name_to_version[os_name]
