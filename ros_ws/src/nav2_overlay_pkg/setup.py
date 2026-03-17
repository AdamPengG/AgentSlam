from setuptools import find_packages, setup

package_name = 'nav2_overlay_pkg'

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
    description='Nav2 overlay scaffolding and deferred semantic navigation hooks.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'semantic_exploration_demo = nav2_overlay_pkg.exploration_demo:main',
            'localized_geometric_mapper = nav2_overlay_pkg.localized_mapping:main',
        ],
    },
)
