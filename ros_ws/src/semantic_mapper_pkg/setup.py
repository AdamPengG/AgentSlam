from setuptools import find_packages, setup

package_name = 'semantic_mapper_pkg'

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
    description='Offline and ROS-driven semantic mapping baseline using GT pose plus visual observations.',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'semantic_mapper_fixture = semantic_mapper_pkg.cli:run_fixture_main',
            'semantic_mapper_query = semantic_mapper_pkg.cli:run_query_main',
            'semantic_mapper_fixture_with_queries = semantic_mapper_pkg.cli:run_fixture_with_queries_main',
            'semantic_mapper_ros = semantic_mapper_pkg.ros_node:main',
        ],
    },
)
