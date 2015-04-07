from setuptools import setup

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
      name="py-cif-apwg",
      version="0.0.0a1",
      description="APWG Feed app for CIF",
      url="https://github.com/csirtgadgets/py-cif-apwg",
      license='LGPL3',
      classifiers=[
                   "Topic :: System :: Networking",
                   "Environment :: Other Environment",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
                   "Programming Language :: Python",
                   ],
      keywords=['cif', 'security', 'apwg'],
      author="Wes Young",
      author_email="wes@barely3am.com",
      packages=["cif_apwg"],
      entry_points={
          'console_scripts': [
              'cif-apwg=cif_apwg:main',
              ]
      },
      install_requires=reqs
)
