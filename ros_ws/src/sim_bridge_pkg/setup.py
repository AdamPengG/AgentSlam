from setuptools import find_packages, setup

package_name = 'sim_bridge_pkg'

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
    description='Isaac/ROS2 bridge scaffolding plus replay publishers for AgentSlam.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'fixture_replay_publisher = sim_bridge_pkg.fixture_replay_publisher:main',
        ],
    },
)
