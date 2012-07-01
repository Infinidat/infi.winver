__import__("pkg_resources").declare_namespace(__name__)

class Windows(object): #pylint: disable-msg=R0902,R0904
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

    def analyze_windows_version(self):
        (major, minor) = self._version_ex.major_version, self._version_ex.minor_version
        if (major, minor) == (5, 0):
            self.version = 'Windows 2000'
        elif (major, minor) == (5, 1):
            self.version = 'Windows XP'
        elif (major, minor) == (5, 2):
            self.version = 'Windows Server 2003'
        elif (major, minor) == (6, 0):
            if self._version_ex.product_type == 1:
                self.version = 'Windows Vista'
            else:
                self.version = 'Windows Server 2008'
        elif (major, minor) == (6, 1):
            if self._version_ex.product_type == 1:
                self.version = 'Windows 7'
            else:
                self.version = 'Windows Server 2008 R2'
        elif (major, minor) == (6, 2):
            if self._version_ex.product_type == 1:
                self.version = 'Windows 8'
            else:
                self.version = 'Windows Server 2012'
        else:
            self.version = 'Unknown'

    def analyze_windows_edition(self):
        self.server_core = False
        self.hyper_v = False
        self.edition = 'Standard'
        if self._version_ex.major_version == 5:
            self.analyze_windows5_edition()
        elif self._version_ex.major_version == 6:
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

    def is_windows_2012(self):
        return self.version == 'Windows Server 2012'

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
