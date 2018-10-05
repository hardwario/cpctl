from setuptools import setup

setup(
    name='cpctl',
    packages=['cpctl'],
    version='@@VERSION@@',
    description='Cooper Control Tool',
    url='https://github.com/blavka/cpctl',
    author='HARDWARIO s.r.o.',
    author_email='ask@hardwario.com',
    license='MIT',
    keywords = ['cooper', 'cli', 'tool'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Environment :: Console',
        'Intended Audience :: Science/Research'
    ],
    install_requires=[
        'click==6.7', 'pyserial==3.4'
    ],
    entry_points='''
        [console_scripts]
        cpctl=cpctl.cli:main
    '''
)
