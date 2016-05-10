from setuptools import setup, find_packages

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
      name="cif-apwg-py",
      version="0.0.0a2",
      description="APWG Feed app for CIF",
      url="https://github.com/csirtgadgets/cif-apwg-py",
      license='LGPL3',
      classifiers=[
                   "Topic :: Security",
                   "Environment :: Other Environment",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
                   "Programming Language :: Python",
                   ],
      keywords=['cif', 'security', 'apwg'],
      author="Wes Young",
      author_email="wes@barely3am.org",
      packages=find_packages(),
      install_requires=[
        'cif-sdk-py',
      ],
      entry_points={
          'console_scripts': [
              'cif-apwg=cifapwg:main',
              ]
      },
)
