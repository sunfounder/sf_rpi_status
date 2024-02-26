
import os
import subprocess

from . import ha_api

def get_cpu_temperature():
    from psutil import sensors_temperatures
    return sensors_temperatures()['cpu_thermal'][0].current

def get_cpu_percent(percpu=False):
    from psutil import cpu_percent
    return cpu_percent(percpu=percpu)

class CPUFreq:
    def __init__(self, data):
        self._current = data.current
        self._min = data.min
        self._max = data.max

    def __str__(self):
        return f'CPUFreq(current: {self.current} MHz, min: {self.min} MHz, max: {self.max} MHz)'

    @property
    def current(self):
        return self._current
    
    @property
    def min(self):
        return self._min
    
    @property
    def max(self):
        return self._max

def get_cpu_freq():
    from psutil import cpu_freq
    return CPUFreq(cpu_freq())

def get_cpu_count():
    from psutil import cpu_count
    return cpu_count()

class MemoryInfo:
    def __init__(self, data):
        self._total = data.total
        self._available = data.available
        self._percent = data.percent
        self._used = data.used
        self._free = data.free

    def __str__(self):
        return f'MemoryInfo(total: {self.total} B, available: {self.available} B, percent: {self.percent}%, used: {self.used} B, free: {self.free} B)'

    @property
    def total(self):
        return self._total
    
    @property
    def available(self):
        return self._available
    
    @property
    def percent(self):
        return self._percent
    
    @property
    def used(self):
        return self._used
    
    @property
    def free(self):
        return self._free

def get_memory_info():
    from psutil import virtual_memory
    return MemoryInfo(virtual_memory())

class DiskInfo:
    def __init__(self, total, used, free, percent):
        self._total = total
        self._used = used
        self._free = free
        self._percent = percent

    def __str__(self):
        return f'DiskInfo(total: {self.total} B, used: {self.used} B, free: {self.free} B, percent: {self.percent}%)'

    @property
    def total(self):
        return self._total
    
    @property
    def used(self):
        return self._used
    
    @property
    def free(self):
        return self._free
    
    @property
    def percent(self):
        return self._percent

def get_disk_info():
    from psutil import disk_usage
    disk_info = disk_usage('/')
    return DiskInfo(disk_info.total, disk_info.used, disk_info.free, disk_info.percent)

def get_disks_info():
    from psutil import disk_partitions, disk_usage
    import subprocess
    disks = []
    output = subprocess.check_output(["lsblk", "-o", "NAME,TYPE", "-n", "-l"]).decode().strip().split('\n')
    
    for line in output:
        disk_name, disk_type = line.split()
        if disk_type == "disk":
            disks.append(disk_name)
    
    disk_info = {}
    
    for disk in disks:
        try:
            partitions = disk_partitions(all=True)
            total = 0
            used = 0
            free = 0
            percent = 0
            
            for partition in partitions:
                if partition.device.startswith("/dev/" + disk):
                    usage = disk_usage(partition.mountpoint)
                    total += usage.total
                    used += usage.used
                    free += usage.free
                    percent = max(percent, usage.percent)
            
            disk_info[disk] = DiskInfo(total, used, free, percent)
        except Exception as e:
            print(f"Failed to get disk information for {disk}: {str(e)}")
    
    return disk_info

def get_boot_time():
    from psutil import boot_time
    return boot_time()

# IP address
def _get_ips():
    IPs = {}
    NIC_devices = []
    NIC_devices = os.listdir('/sys/class/net/')

    for NIC in NIC_devices:
        if NIC == 'lo':
            continue
        try:
            IPs[NIC] = subprocess.check_output('ifconfig ' + NIC + ' | grep "inet " | awk \'{print $2}\'', shell=True).decode().strip('\n')
        except:
            continue

    return IPs

def get_ips():
    ips = None
    if ha_api.is_homeassistant_addon():
        ips = ha_api.get_ips()
        if len(ips) == 0:
            ips = _get_ips()
    else:
        ips = _get_ips()

    for key in ips:
        if ips[key] == '' or ips[key] == None:
            ips = ips.pop(key)
            
    return ips


def get_macs():
    MACs = {}
    NIC_devices = []
    NIC_devices = os.listdir('/sys/class/net/')
    for NIC in NIC_devices:
        if NIC == 'lo':
            continue
        try:
            with open('/sys/class/net/' + NIC + '/address', 'r') as f:
                MACs[NIC] = f.readline().strip()
        except:
            continue

    return MACs

net_io_counter = None
net_io_counter_time = None

def get_network_connection_type():
    from psutil import net_if_stats
    interfaces = net_if_stats()
    connection_type = []
    
    for interface, stats in interfaces.items():
        if stats.isup:
            if "eth" in interface or "enp" in interface or "ens" in interface:
                connection_type.append("Wired")
            if "wlan" in interface or "wlp" in interface or "wls" in interface:
                connection_type.append("Wireless")
    
    return connection_type

class NetworkSpeed:
    def __init__(self):
        self._upload = 0
        self._download = 0

    def __str__(self):
        return f'NetworkSpeed(upload: {self.upload} B/s, download: {self.download} B/s)'

    def set_upload(self, speed):
        self._upload = speed

    def set_download(self, speed):
        self._download = speed

    @property
    def upload(self):
        return self._upload
    
    @property
    def download(self):
        return self._download


def get_network_speed():
    from psutil import net_io_counters
    from time import time
    global net_io_counter, net_io_counter_time
    network_speed = NetworkSpeed()
    # 获取初始网络计数器信息
    current_net_io_counter = net_io_counters()
    current_net_io_counter_time = time()

    if net_io_counter is None:
        net_io_counter = current_net_io_counter
        net_io_counter_time = current_net_io_counter_time
        return network_speed

    # 计算速度差异
    bytes_sent = current_net_io_counter.bytes_sent - net_io_counter.bytes_sent
    bytes_recv = current_net_io_counter.bytes_recv - net_io_counter.bytes_recv
    interval = current_net_io_counter_time - net_io_counter_time

    # 计算速度（每秒字节数）
    upload_speed = bytes_sent / interval
    download_speed = bytes_recv / interval

    network_speed.set_upload(round(upload_speed))
    network_speed.set_download(round(download_speed))

    net_io_counter = current_net_io_counter
    net_io_counter_time = current_net_io_counter_time

    return network_speed