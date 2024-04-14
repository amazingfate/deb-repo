# Scripts to manage deb repo based on GHCR

## Create a repo:
https://github.com/AkihiroSuda/apt-transport-oci/blob/master/examples/README.md

## OCI repo auth setting
There are 3 necessary env:
 - `OCI_REPO` for oci repo, for example `ghcr.io/amazingfate/deb-repo:test`
 - `OCI_AUTH_NAME` for your oci repo auth username
 - `GH_TK` for oci repo auth token

## Upload packages to an existing repo:
1, use oras to pull the full repo

2, Add package files to the local repo dir

3, dpkg-scanpackage/dpkg-scansources to generate Packages/Sources

4, run upload_package.py in the local repo dir, it's hard-coded to my repo `ghcr.io/amazingfate/deb-repo:test` at the moment
