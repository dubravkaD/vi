import subprocess

# entering_chroot with xchroot -> try to fix error
subprocess.run(["xchroot", "/mnt", "/bin/bash"], check=True)