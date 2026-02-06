from .utils import run_command
import subprocess
import os
import json

# def get_cpu_temperature():
#     from psutil import sensors_temperatures
#     return sensors_temperatures()['cpu_thermal'][0].current

def get_cpu_temperature():
    try:
        result = run_command('cat /sys/class/thermal/thermal_zone0/temp')
        return float(result) / 1000
    except:
        return None

def get_gpu_temperature():
    try:
        result = run_command('vcgencmd measure_temp')
        return float(result.split('=')[1].split("'")[0])
    except:
        return None

def get_cpu_percent(percpu=False):
    from psutil import cpu_percent
    return cpu_percent(percpu=percpu)

class CPUFreq:
    def __init__(self, data):
        self._current = data.current
        self._min = data.min
        self._max = data.max

    def __repr__(self):
        return f'CPUFreq(current: {self.current} MHz, min: {self.min} MHz, max: {self.max} MHz)'

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

    def __repr__(self):
        return f'MemoryInfo(total: {self.total} B, available: {self.available} B, percent: {self.percent}%, used: {self.used} B, free: {self.free} B)'

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
        return self._total-self._available
    
    @property
    def free(self):
        return self._free

def get_memory_info():
    from psutil import virtual_memory
    return MemoryInfo(virtual_memory())

class DiskInfo:
    def __init__(self, total=0, used=0, free=0, percent=0.0, type='unknown', temperature=None, path=None, mounted=False):
        self._total = total
        self._used = used
        self._free = free
        self._percent = percent
        self._path = path
        self._mounted = mounted
        self._temperature = temperature
        self._type = type
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        from psutil._common import bytes2human
        string = ""
        if self.mounted:
            string = f'Disk {self._path}: total: {bytes2human(self.total)}B, used: {bytes2human(self.used)}B, free: {bytes2human(self.free)}B, percent: {self.percent}%, type: {self.type}'
        else:
            string = f'Disk {self._path} not mounted, total: {bytes2human(self.total)}B, type: {self.type}'
        if self.temperature is not None:
            string += f', temperature: {self.temperature}°C'
        return string

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

    @property
    def path(self):
        return self._path
    
    @property
    def mounted(self):
        return self._mounted

    @property
    def temperature(self):
        return self._temperature

    @property
    def type(self):
        return self._type


def get_disk_info(mountpoint='/'):
    from psutil import disk_usage
    disk_info = disk_usage(mountpoint)
    return DiskInfo(
        total=disk_info.total,
        used=disk_info.used,
        free=disk_info.free,
        percent=disk_info.percent,
        path='total',
        mounted=True,
    )

def get_disks():
    from pyudev import Context

    context = Context()
    all_disks = set()

    for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
        device_node = device.device_node

        # 排除RAM磁盘和loop设备
        if 'ram' not in device_node and 'loop' not in device_node:
            all_disks.add(device_node)

    return list(all_disks)

def get_disk_total(disk):
    from .utils import human2bytes

    if "/dev/" in disk:
        disk = disk.split("/dev/")[1]
    cmd = f"lsblk -o NAME,TYPE,SIZE -n -l"
    result = subprocess.check_output(cmd, shell=True).decode().strip()
    lines = result.split("\n")
    total = None
    for line in lines:
        values = line.split()
        name = values[0]
        size = values[2]
        if name == disk:
            total = human2bytes(size)
            break
    else:
        raise Exception(f"Failed to get disk total for {disk}")
    return total

def is_disk_mounted(disk):
    from psutil import disk_partitions
    partitions = disk_partitions(all=False)

    for partition in partitions:
        if disk in partition.device:
            return True

    return False

def get_disk_temperature(disk):
    try:
        output = subprocess.check_output(['smartctl', '-a', disk])
        lines = output.decode('utf-8').split('\n')
        
        for line in lines:
            if 'Temperature_Celsius' in line:
                temperature = line.split()[9]
                return temperature
    except subprocess.CalledProcessError as e:
        # print(f"Error: {e}")
        return None

def get_disk_type(disk_path: str) -> str:
    disk = os.path.basename(disk_path)
    sys_block_path = f'/sys/class/block/{disk}'

    if disk.startswith('nvme'):
        return 'nvme'

    elif disk.startswith('mmcblk'):
        return 'sd'

    elif disk.startswith('md'):
        return 'raid'

    elif disk.startswith('sd'):
        bus_path = f'{sys_block_path}/device/../../../bus'
        if os.path.exists(bus_path):
            bus_type = os.path.basename(os.path.realpath(bus_path))
            if bus_type == 'usb':
                return 'usb'
            else:
                return 'hd'
        else:
            return 'hd'

def get_disks_info(disks=None, temperature=False):
    disk_info = {}
    if disks is None:
        disks = get_disks()  # 假设这个函数依然返回 ['/dev/mmcblk0', '/dev/nvme0n1'] 等

    # 1. 预先通过 lsblk 抓取所有物理磁盘的挂载信息和空间数据
    # -b: 字节单位, -J: JSON, -a: 显示所有, -o: 关键字段
    # 排除主设备号为 7 的 loop 设备
    try:
        lsblk_cmd = ["lsblk", "-b", "-J", "-e", "7", "-o", "NAME,MOUNTPOINT,FSSIZE,FSUSED"]
        lsblk_data = json.loads(subprocess.check_output(lsblk_cmd).decode())
        
        # 将 lsblk 的树状结构扁平化，方便查找
        lsblk_flat = {}
        def flatten(devs):
            for d in devs:
                # 记录每一个设备名对应的空间信息
                # 这里的 d['name'] 可能是 'nvme0n1p1'，我们需要匹配父级名称
                lsblk_flat[d['name']] = d
                if 'children' in d:
                    flatten(d['children'])
        
        flatten(lsblk_data.get('blockdevices', []))
    except Exception as e:
        print(f"lsblk error: {e}")
        lsblk_flat = {}

    # 2. 遍历你传入的磁盘列表
    for disk in disks:
        # 提取设备名，如把 /dev/nvme0n1 变成 nvme0n1
        disk_name = disk.split('/')[-1]
        
        mounted = is_disk_mounted(disk)
        disk_type = get_disk_type(disk) 
        
        try:
            total = 0
            used = 0
            free = 0
            percent = 0.0
            temp_val = None
            
            if temperature:
                try:
                    temp_val = get_disk_temperature(disk)
                except Exception as e:
                    temp_val = None

            if not mounted:
                total = get_disk_total(disk)
            else:
                # 3. 匹配该磁盘下的所有挂载点
                # 我们在 lsblk_flat 中寻找名字包含 disk_name 的项（匹配分区）
                for name, info in lsblk_flat.items():
                    # 匹配逻辑：如果是 nvme0n1，则匹配 nvme0n1 本身或其分区 nvme0n1p1
                    if (disk_name == name or name.startswith(disk_name)) and info.get('mountpoint'):
                        if info.get('fssize'):
                            total += int(info['fssize'])
                            used += int(info['fsused'])
                            free += int(info['fssize']) - int(info['fsused'])

                if total == 0:
                    continue
                
                percent = round((used / total * 100), 2)

            # 保持你原始的 DiskInfo 构造格式
            disk_info[disk] = DiskInfo(
                total=total,
                used=used,
                free=free,
                percent=percent,
                path=disk,
                mounted=mounted,
                temperature=temp_val,
                type=disk_type,
            )
        except Exception as e:
            print(f"Failed to get disk information for {disk}: {str(e)}")
    
    return disk_info

def get_boot_time():
    from psutil import boot_time
    return boot_time()

def _get_ips():
    import psutil
    import socket
    IPs = {}

    try:
        NIC_devices = psutil.net_if_addrs()
        for name, NIC in NIC_devices.items():
            if name == 'lo':
                continue
            try:
                for af in NIC:
                    if af.family == socket.AF_INET: # 2:'IPV4'
                        IPs[name] = af.address
            except:
                continue
    except Exception as e:
        print(f"Failed to get ips: {str(e)}")
    
    return IPs

def get_ips():
    from . import ha_api
    ips = None
    if ha_api.is_homeassistant_addon():
        ips = ha_api.get_ips()
    else:
        ips = _get_ips()

    result = {}
    for key in ips:
        if ips[key] != '' and ips[key] != None:
            result[key] = ips[key]

    return result

def get_macs():
    from os import listdir
    MACs = {}
    NIC_devices = []
    NIC_devices = listdir('/sys/class/net/')
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

def shutdown():
    from . import ha_api
    if ha_api.is_homeassistant_addon():
        ha_api.shutdown()
    else:
        from os import system
        system('sudo systemctl poweroff -i')

def reboot():
    from . import ha_api
    if ha_api.is_homeassistant_addon():
        ha_api.reboot()
    else:
        from os import system
        system('sudo systemctl reboot -i')

def restart_service():
    from . import systemd_detector as systemd_detector
    from . import ha_api
    if ha_api.is_homeassistant_addon():
        ha_api.restart_addon()
    elif systemd_detector.is_running_as_systemd_service():
        service_name = systemd_detector.get_systemd_service_name()
        if service_name:
            from os import system
            system(f'systemctl restart {service_name}')

class PWMFan():
    # Systems that need to replace system pwm fan control
    # Please use all lowercase
    TEMP_CONTROL_INTERVENE_OS = [
        
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not PWMFan.pwm_fan_supported():
            print("PWM Fan is not supported")
            self._is_ready = False
            return

        # Check if system support pwm fan control
        os_id = run_command("lsb_release -a |grep ID | awk -F ':' '{print $2}'")
        os_id = os_id.strip()
        os_code_name = run_command("lsb_release -a |grep Codename | awk -F ':' '{print $2}'")
        os_code_name = os_code_name.strip()

        self.enable_control = False
        if os_id.lower() in self.TEMP_CONTROL_INTERVENE_OS or os_code_name.lower() in self.TEMP_CONTROL_INTERVENE_OS:
            print("System do not support pwm fan control")
            self.enable_control = True
        self._is_ready = True

    @staticmethod
    def pwm_fan_supported():
        from os import path
        return path.exists('/sys/class/thermal/cooling_device0/cur_state') and path.exists('/sys/devices/platform/cooling_fan')

    def check_ready(func):
        def wrapper(self, *args, **kwargs):
            if not self._is_ready:
                return None
            return func(self, *args, **kwargs)
        return wrapper

    @check_ready
    def is_supported(self):
        return not self.enable_control

    check_ready
    def get_state(self):
        path = '/sys/class/thermal/cooling_device0/cur_state'
        try:
            with open(path, 'r') as f:
                cur_state = int(f.read())
            return cur_state
        except Exception as e:
            print(f'read pwm fan state error: {e}')
            return 0

    @check_ready
    def set_state(self, level: int):
        '''
        level: 0 ~ 4
        '''
        if (isinstance(level, int)):
            if level > 4:
                level = 4
            elif level < 0:
                level = 0

            cmd = f"echo '{level}' | sudo tee -a /sys/class/thermal/cooling_device0/cur_state"
            result = subprocess.check_output(cmd, shell=True)

            return result

    @check_ready
    def get_speed(self):
        '''
        path =  '/sys/devices/platform/cooling_fan/hwmon/*/fan1_input'
        '''
        dir = '/sys/devices/platform/cooling_fan/hwmon/'
        secondary_dir = os.listdir(dir)
        path = f'{dir}/{secondary_dir[0]}/fan1_input'

        os.listdir
        try:
            with open(path, 'r') as f:
                speed = int(f.read())
            return speed
        except Exception as e:
            print(f'read fan1 speed error: {e}')
            return 0

    @check_ready
    def off(self):
        if not self.is_supported():
            self.set_state(0)

    @check_ready
    def close(self):
        self.off()
        self._is_ready = False
