"""Publish read-only document download progress for the isolated Podman lab."""
import time

import library_monitor
import linux_lab
import setup
from delivery_paths import destination


def publish():
    linux_lab.checked_mount()
    root = linux_lab.MOUNT / 'data'
    report = library_monitor.snapshot(root, linux_lab.MOUNT / 'private')
    setup.write_json(destination(root, 'catalog/lab-activity.json'), report)


def main():
    while True:
        publish()
        time.sleep(5)


if __name__ == '__main__':
    main()
