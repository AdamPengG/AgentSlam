from setuptools import find_packages, setup

package_name = 'localization_adapter_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='peng',
    maintainer_email='424158674@qq.com',
    description='Ground-truth-first localization adapter contracts for AgentSlam.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'localization_adapter = localization_adapter_pkg.ros_node:main',
        ],
    },
)
