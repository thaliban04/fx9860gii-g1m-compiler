import os
import string
import ctypes

def get_removable_drives():
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drive_path = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            # DRIVE_REMOVABLE = 2
            if drive_type == 2:
                # Check volume name and space
                vol_name_buf = ctypes.create_unicode_buffer(261)
                fs_name_buf = ctypes.create_unicode_buffer(261)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    drive_path, vol_name_buf, 261, None, None, None, fs_name_buf, 261
                )
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    drive_path, ctypes.byref(free_bytes), ctypes.byref(total_bytes), None
                )
                drives.append({
                    "drive": drive_path,
                    "volume": vol_name_buf.value,
                    "fs": fs_name_buf.value,
                    "total_mb": round(total_bytes.value / (1024 * 1024), 2),
                    "free_mb": round(free_bytes.value / (1024 * 1024), 2)
                })
        bitmask >>= 1
    return drives

print("Removable drives:", get_removable_drives())
