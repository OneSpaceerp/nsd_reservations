from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="nsd_reservations",
    version="1.0.0",
    description="Meeting Room Reservation Module for ERPNext",
    author="NSD",
    author_email="info@nsd.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)