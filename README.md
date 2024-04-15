# Scripts to manage deb repo based on GHCR

##  Features
- [x] Only upload files not exist in remote repo
- [x] Delete unused files in remote repo
- [ ] Signature of repo

## Create a repo:
https://github.com/AkihiroSuda/apt-transport-oci/blob/master/examples/README.md

## OCI repo auth setting
There are 3 necessary env:
 - `OCI_REPO` for oci repo, for example `ghcr.io/amazingfate/deb-repo:test`
 - `OCI_AUTH_NAME` for your oci repo auth username
 - `GH_TK` for oci repo auth token

Make sure to export them before uploading.

## Upload packages to an existing repo:
1, use oras to pull the full repo for example: `oras pull ghcr.io/amazingfate/deb-repo:test`

2, Add/delete/update package files to the local repo dir

3, Use command `dpkg-scanpackage`/`dpkg-scansources` to generate `Packages`/`Sources`

4, run `upload_package.py` in the local repo dir
