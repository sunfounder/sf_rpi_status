from .version import __version__
from .status import \
    get_cpu_temperature, \
    get_gpu_temperature, \
    get_cpu_percent, \
    get_cpu_freq, \
    get_cpu_count, \
    get_memory_info, \
    get_disks, \
    get_disk_type, \
    is_disk_mounted, \
    get_disk_info, \
    get_disk_temperature, \
    get_disks_info, \
    get_boot_time, \
    get_ips, \
    get_macs, \
    get_network_connection_type, \
    get_network_speed, \
    restart_service, \
    reboot, \
    shutdown, \
    CPUFreq, \
    NetworkSpeed, \
    MemoryInfo, \
    DiskInfo, \
    PWMFan


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Raspberry Pi Status')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--all', action='store_true', help='All info')
    parser.add_argument('--cpu-temperature', action='store_true', help='CPU temperature')
    parser.add_argument('--cpu-percent', action='store_true', help='CPU percent')
    parser.add_argument('--percpu', action='store_true', help='CPU percent per CPU')
    parser.add_argument('--cpu-freq', action='store_true', help='CPU frequency')
    parser.add_argument('--cpu-count', action='store_true', help='CPU count')
    parser.add_argument('--memory', action='store_true', help='Memory info')
    parser.add_argument('--disk', action='store_true', help='Disk info')
    parser.add_argument('--disks', action='store_true', help='Disks info')
    parser.add_argument('--boot-time', action='store_true', help='Boot time')
    parser.add_argument('--ips', action='store_true', help='IP addresses')
    parser.add_argument('--macs', action='store_true', help='MAC addresses')
    parser.add_argument('--network-connection-type', action='store_true', help='Network connection type')
    parser.add_argument('--network-speed', action='store_true', help='Network speed')
    args = parser.parse_args()

    if args.all:
        args.cpu_temperature = True
        args.cpu_percent = True
        args.cpu_freq = True
        args.cpu_count = True
        args.memory = True
        args.disk = True
        args.disks = True
        args.network = True
        args.boot_time = True
        args.ips = True
        args.macs = True
        args.network_connection_type = True
        args.network_speed = True
    
    if args.cpu_temperature:
        print(f'CPU temperature: {get_cpu_temperature()}°C')
    if args.cpu_percent:
        print(f'CPU percent: {get_cpu_percent(args.percpu)}%')
    if args.cpu_freq:
        print(f'CPU frequency: {get_cpu_freq()}')
    if args.cpu_count:
        print(f'CPU count: {get_cpu_count()}')
    if args.memory:
        print(f'Memory info: {get_memory_info()}')
    if args.disk:
        print(f'Disk info: {get_disk_info()}')
    if args.disks:
        print(f'Disks info: {get_disks_info()}')
    if args.boot_time:
        print(f'Boot time: {get_boot_time()}')
    if args.ips:
        print(f'IP addresses: {get_ips()}')
    if args.macs:
        print(f'MAC addresses: {get_macs()}')
    if args.network_connection_type:
        print(f'Network connection type: {get_network_connection_type()}')
    if args.network_speed:
        print(f'Network speed: {get_network_speed()}')


if __name__ == '__main__':
    main()
