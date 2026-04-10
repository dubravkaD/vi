import os
import subprocess
import platform


system_data = {
    "uefi": True,
    "architecture": "x86_64",
    "disk": "/dev/sda",
    "filesystem": "ext4",
    "swap": False,
    "bootloader": "grub",
    "kernel": ["linux"],
    "hostname": "voidlinux",
    "root_password": "root",
    "timezone": "UTC",
    "locale": "en_US.UTF-8 UTF-8",
    "repo": "https://repo-default.voidlinux.org/current",
    "packages": ["base-system", "vim", "NetworkManager", "base-devel", "curl", "wget"],
    "users": [{"name": "user", "password": "user", "sudo": True}]
}


def run(cmd, shell: bool = False) -> None:
    """
        Run a shell command
    """
    print(f"Running: {cmd}")
    subprocess.run(cmd, check=True)


def is_uefi() -> bool:
    """
        Detect firmware interface - UEFI
    """
    return os.path.exists("/sys/firmware/efi")


def detect_uefi() -> None:
    if is_uefi():
        system_data["uefi"] = True
        print("Boot mode: UEFI")
    else:
        system_data["uefi"] = False
        print("Boot mode: BIOS")


def detect_arch() -> str:
    arch = platform.machine().lower()

    if arch in ("x86_64", "amd64"):
        return "64-bit (x86_64)"
    elif arch in ("i386", "i686"):
        return "32-bit (x86)"
    elif "aarch64" in arch or "arm64" in arch:
        return "ARM 64-bit"
    elif "arm" in arch:
        return "ARM 32-bit"
    else:
        return f"Unknown architecture ({arch})"


def detect_architecture() -> str:
    """
        Detect CPU architecture
    """
    arch = platform.machine().lower()
    if arch in ('x86_64', 'amd64'):
        arch = 'x86_64'
    elif arch in ('i386', 'i686'):
        arch = 'i686'
    elif arch.startswith('arm') or arch.startswith('aarch64'):
        arch = 'aarch64'
    else:
        arch = arch
    return arch


def display_system_data() -> None:
    # print("Data: ", system_data)
    print("System Data: ")
    for key, value in system_data.items():
        print("\t",key, " -> ", value)
    print("\n")


def reboot() -> None:
    # exit
    # umount -R /mnt
    # shutdown -r now
    run(["exit"])
    run(["unmount", "-R", "/mnt"])
    run(["shutdown", "-r", "now"])


def finale_step() -> None:
    # xbps-reconfigure -fa
    run(["xbps-reconfigure", "-fa"])


def finalization() -> None:
    print("*********************************")
    print("7. Finalization\n")
    finale_step()
    reboot()


def grub_install(boot_mode: str = "UEFI", disk: str = "/dev/sda", arch: str = "x86_64") -> None:
    if boot_mode == "UEFI":
        if arch == "x86_64":
            # xbps-install -S grub-x86_64-efi
            # grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id="Void"
            run(["xbps-install", "-S", "grub-x86_64-efi"])
            run(["grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", '--bootloader-id="Void"'])
        elif arch == "i386":
            run(["xbps-install", "-S", "grub-i386-efi"])
            run(["grub-install", "--target=i386-efi", "--efi-directory=/boot/efi", '--bootloader-id="Void"'])
        elif arch == "arm64":
            run(["xbps-install", "-S", "grub-arm64-efi"])
            run(["grub-install", "--target=arm64-efi", "--efi-directory=/boot/efi", '--bootloader-id="Void"'])
    else:
        # xbps-install -S grub
        # grub-install /dev/sda
        run(["xbps-install", "-S", "grub"])
        run(["grub-install", disk])


def install_bootloader() -> None:
    print("*********************************")
    print("6. Install Bootloader\n")
    grub_install()


def disable_services(service:str):
    # rm /var/service/<service>
    # rm /etc/runit/runsvdir/default/<service>
    pass


def enable_services(dhcpcd: bool = True, networkmanager: bool = False) -> None:
    # ln -s /etc/sv/<service> /etc/runit/runsvdir/default/
    # touch /etc/sv/<service>/down
    # ln -s /etc/sv/<service> /var/service/

    if dhcpcd:
        run(["ln", "-s", "/etc/sv/dhcpcd", "/etc/runit/runsvdir/default/"])
    elif networkmanager:
        run(["ln", "-s", "/etc/sv/NetworkManager", "/etc/runit/runsvdir/default/"])


def set_password(user: str = "root", password: str = "root") -> None:
    # passwd for root
    subprocess.run(
        ["chpasswd"],
        input=f"{user}:{password}".encode(),
        check=True
    )


def installation_configuration(hostname:str = "voidlinux") -> None:
    # /etc/hostname
    # echo hostname > /etc/hostname
    run(["echo", hostname, ">>", "/etc/hostname"])
    # xbps-reconfigure -f glibc-locales
    run(["xbps-reconfigure", "-f", "glibc-locales"])


def entering_chroot() -> None:
    # xchroot /mnt /bin/bash
    run(["xchroot", "/mnt", "/bin/bash"])


def configure_filesystems() -> None:
    # xgenfstab -U /mnt > /mnt/etc/fstab
    run(["xgenfstab", "-U", "/mnt", ">", "/mnt/etc/fstab"])


def system_configuration() -> None:
    print("*********************************")
    print("5. Configure System Basics\n")
    configure_filesystems()
    entering_chroot()
    installation_configuration()
    set_password() # root
    enable_services()



def base_system_installation(arch: str = "x86_64", repo: str = "https://repo-default.voidlinux.org/current") -> None:
    print("*********************************")
    print("4. Install Base System\n")
    # mkdir -p /mnt/var/db/xbps/keys
    # cp /var/db/xbps/keys/* /mnt/var/db/xbps/keys/
    run(["mkdir", "-p", "/mnt/var/db/xbps/keys"])
    run(["cp", "-rv", "/var/db/xbps/keys/.", "/mnt/var/db/xbps/keys/"])
    # XBPS_ARCH=$ARCH xbps-install -S -r /mnt -R "$REPO" base-system
    subprocess.run(["XBPS_ARCH={arch}", "xbps-install", "-S", "-r", "/mnt", "-R", repo, "base-system"], shell=True, check=True)


def mount_filesystem(boot_mode: str = "UEFI", disk: str = "/dev/sda", option: str = "1") -> None:
    print("*********************************")
    print("3. Mount Filesystems\n")
    # UEFI option 1
    # mount /dev/sda2 /mnt/
    # mkdir -p /mnt/boot/efi/
    # mount /dev/sda1 /mnt/boot/efi/
    if boot_mode == "UEFI":
        if option in ["1"]:
            run(["mount", f"{disk}2", "/mnt/"])
            run(["mkdir", "-p", "/mnt/boot/efi"])
            run(["mount", f"{disk}1", "/mnt/boot/efi"])
        elif option in ["2"]:
            run(["mount", f"{disk}3", "/mnt/"])
            run(["mkdir", "-p", "/mnt/boot/efi"])
            run(["mount", f"{disk}1", "/mnt/boot/efi"])


def partitioning_options(boot_mode: str = "UEFI", disk: str = "/dev/sda", option: str = "1") -> None:

    print("EFI/BIOS + rest root")

    if boot_mode == "UEFI":
        run(["parted", "-s", disk, "mklabel", "gpt"])
    else:
        run(["parted", "-s", disk, "mklabel", "msdos"])

    partitions = []

    if boot_mode == "UEFI":
        if option in ["1", "2", "3", "4"]:
            partitions.append(("mkpart ESP fat32 1 1.5", "set 1 esp on"))

    current_start = 1.5 if boot_mode == "UEFI" else 1

    if option in ["1", "2"]:
        partitions.append((f"mkpart primary ext4 {current_start} 100%", None))

    for cmd, flag_cmd in partitions:
        run(["parted", "-s", disk] + cmd.split())
        if flag_cmd:
            run(["parted", "-s", disk] + flag_cmd.split())

    part_num = 1
    if boot_mode == "UEFI":
        run(["mkfs.fat", "-F32", f"{disk}{part_num}"])
        part_num += 1
    if option in ["2", "4"]:
        run(["mkswap", f"{disk}{part_num}"])
        run(["swapon", f"{disk}{part_num}"])
        part_num += 1
    if option in ["1", "2"]:
        run(["mkfs.ext4", f"{disk}{part_num}"])
    elif option in ["3", "4"]:
        # Root
        run(["mkfs.ext4", f"{disk}{part_num}"])
        part_num += 1
        # Home
        run(["mkfs.ext4", f"{disk}{part_num}"])

    if boot_mode == "BIOS":
        run(["parted", "-s", disk, "set", str(part_num if option in ["1", "3"] else 2), "boot", "on"])


def disk_partitioning(boot_mode: str = "UEFI") -> None:
    print("*********************************")
    print("2. Partition the disk & Format Partitions\n")
    # print("Select layout option:")
    print("1: EFI/BIOS + rest root")
    print("2: EFI/BIOS + Swap + rest root")
    print("3: EFI/BIOS + root 20GB + rest home")
    print("4: EFI/BIOS + Swap + root 20GB + rest home\n")
    partitioning_options()


def system_detection() -> tuple[str, str]:
    print("*********************************")
    print("1. System detection\n")
    arch = detect_architecture()
    print(f"Architecture: {arch}")
    type_fi = is_uefi()
    firmware = "UEFI" if type_fi else "BIOS"
    print(f"Firmware interface: {firmware}\n")
    return arch, firmware


def get_choice(min_val=1, max_val=8) -> int:
    while True:
        try:
            choice = int(input(f"Select an option ({min_val}-{max_val}): "))
            if min_val <= choice <= max_val:
                return choice
            print(f"Enter a number between {min_val} and {max_val}\n")
        except ValueError:
            print("Invalid input\n")


def cli_menu_configure_system_basics() -> None:
    print("*********************************")
    print("7. Configure System Basics")
    print("*********************************")
    print("7a. Set hostname")
    print("7b. Set timezone")
    print("7c. Set locale")
    print("7d. Set Root Password")
    print("7e. Create User\n")


def cli_menu() -> None:
    print("1. System detection")
    print("2. Partition the disks & Format Partitions")
    print("3. Mount Filesystems")
    print("4. Install Base System")
    print("5. Configure System Basics")
    print("6. Install Bootloader")
    print("7. Finalization")
    print("8. Reboot")
    print("9. Exit")


def main_loop():
    while True:
        cli_menu()
        arch, type = system_detection()
        choice = get_choice(max_val=9)
        try:
            match choice:
                case 1:
                    system_detection()
                case 2:
                    disk_partitioning()
                case 3:
                    mount_filesystem()
                case 4:
                    base_system_installation()
                case 5:
                    system_configuration()
                case 6:
                    install_bootloader()
                case 7:
                    finalization()
                case 8:
                    reboot()
                case 9:
                    print("Exiting program...")
                    break
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")


def main_banner() -> None:
    print("*********************************")
    print("    Void Linux install script")
    print("*********************************")


def main() -> None:
    main_banner()
    # display_system_data()
    # cli_menu()
    # cli_menu_configure_system_basics()
    # print(detect_architecture())
    # arch , type = system_detection()
    main_loop()
    # print(get_choice())
    # disk_partitioning()
    # mount_filesystem()
    # base_system_installation()
    # system_configuration()
    # install_bootloader()
    # finalization()


if __name__ == '__main__':
    main()