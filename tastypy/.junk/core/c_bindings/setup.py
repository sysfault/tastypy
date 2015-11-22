# vim: set fileencoding=utf-8 :
# -*- coding:utf-8 -*_
import platform
import os
import sys
import shutil
from setuptools import setup, find_packages
from distutils.core import Extension

__doc__ = """cpuset - bind a running process to a cpuset
"""

classifiers = """\
Development Status :: 3 - Alpha
Environment :: Other Environment
License :: OSI Approved :: Python Software Foundation License
Operating System :: POSIX :: Linux
Programming Language :: Python
Topic :: System :: Hardware :: Symmetric Multi-processing
"""


doclines = __doc__.splitlines()
VERSION = '0.1.0'
STATUS = 'alpha'


setup(
    name='cpuset',
    version=VERSION,
    author="system fault",
    author_email="sysfault@yahoo.com",
    keywords="process scheduler cpu affinity",
    url="http://tastypy.com/documentation",
    download_url="https://tastypy.com/downloads/releases/%s/tastypy-%s.zip" % (STATUS, VERSION),
    description=doclines[0],
    classifiers=filter(None, classifiers.split("\n")),
    long_description="\n".join(doclines[2:]),
    packages=find_packages(),
    ext_modules=[
        Extension(name='cpuset._cpuset', sources=['cpuset/_cpuset.c'])
    ],
    )

# install hack
# TODO: fix this shit

print("BUILD_DONE, installing into runtime tree")
p = platform.uname()
ver = sys.version_info

src = os.path.join('.', 'build', "lib.%s-%s-%d.%d" % (p[0].lower(), p[4], ver.major, ver.minor), 'cpuset', '_cpuset.so')
dst = 'cpuset/_cpuset.so'
os.rename(src, dst)
shutil.rmtree(os.path.join('.', 'build'))
print(src)

