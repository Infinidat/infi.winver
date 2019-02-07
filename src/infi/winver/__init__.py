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
    (6, 2): 'Windows Server 2012',
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
    1607: 'RTM',
    1703: 'Aniversary Update',
    1709: 'Fall Creators Update',
    1803: 'version 1803',
    1809: 'RTM',
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
        if self._version_ex.major_version == 10:
            self._release_id = self.get_release_id_from_registry()
        self._system_info = get_system_info()
        self._edition = ""
        self.analyze()

    def analyze(self):
        if self._version_ex.major_version == 10:
            self.analyze_windows10_version()
            self.analyze_windows10_update()
        else:
            self.analyze_windows_version()
        self.analyze_windows_edition()
        self.analyze_windows_service_pack()
        self.analyze_windows_architecture()

    def analyze_windows_version(self):
        version = (self._version_ex.major_version, self._version_ex.minor_version, self._version_ex.product_type)
        self.version = version_to_name.get(version, version_to_name.get(version[:2], 'Unknown'))

    def analyze_windows10_version(self):
        from .constants import VER_NT_WORKSTATION
        # Windows 10 and on, and Windows Server 2016 and on, use only "release id" to diffentiate different releases
        # product_type still determines whether this is Windows 10 or Windows Server
        if self._version_ex.product_type == VER_NT_WORKSTATION:
            self.version = "Windows 10"
        elif self._release_id < 1809:
            self.version = "Windows Server 2016"
        else:
            self.version = "Windows Server 2019"

    def analyze_windows10_update(self):
        from .constants import VER_NT_WORKSTATION
        if self._version_ex.product_type == VER_NT_WORKSTATION:
            release_id_to_update = win10_release_id_to_update
        else:
            release_id_to_update = win10_server_release_id_to_update
        self.win10_update = release_id_to_update.get(self._release_id, 'Unknown')

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
        elif self._version_ex.major_version == 10:
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
        if self._version_ex.major_version == 10:
            actual_version = (self._version_ex.major_version, self._version_ex.minor_version, self._release_id)
        else:
            actual_version = (self._version_ex.major_version, self._version_ex.minor_version)
        return actual_version > name_to_version[os_name]
