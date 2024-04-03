# Scripts to manage deb repo based on GHCR

## Create a repo:
https://github.com/AkihiroSuda/apt-transport-oci/blob/master/examples/README.md

## Upload packages to an existing repo:
1, use oras to pull the full repo

2, Add package files to the local repo dir

3, dpkg-scanpackage/dpkg-scansources to generate Packages/Sources

4, run upload_package.py in the local repo dir, it's hard-coded to my repo `ghcr.io/amazingfate/deb-repo:test` at the moment
