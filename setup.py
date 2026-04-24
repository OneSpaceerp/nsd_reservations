from setuptools import setup, find_packages

setup(
    name="nsd_reservations",
    version="1.0.0",
    description="Meeting Room Reservation Module for ERPNext v16",
    author="NSD",
    author_email="info@nsd.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["erpnext>=16.0.0"]
)
