from distutils.core import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='arm_kernel',
    version='1.1',
    packages=['arm_kernel'],
    description='Test ARN assembly kernel for Jupyter',
    long_description=readme,
    author='Beefy Bakers',
    author_email='',
    url='',
    install_requires=[
        'jupyter_client', 'IPython', 'ipykernel'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
)
